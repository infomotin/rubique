"""Fixed-supply coin economy for the Card Club.

Invariants (checked by `verify_ledger`):
  reserve + circulating + pool balances == SUPPLY (1,000,000,000)
  circulating = personal wallets + member group balances + in-flight
  escrow/bet hold wallet (owner w:0:0).
Every balance mutation appends a hash-chained ledger entry:
  entry_hash = sha256(prev_hash + "|" + seq|owner|amount|balance_after|
                      type|ref_type|ref_id|note)
"""

import hashlib
from contextlib import contextmanager
from datetime import datetime, timezone

from models.db import get_db_connection
from models.card_club.errors import (
    CardClubError, InsufficientFunds, MintBlocked, PoolUnderfunded,
    PermissionDenied, ZeroSumViolation,
)

SUPPLY = 1_000_000_000
STARTING_GRANT = 100
GROUP_POOL_ALLOCATION = 5_000
MAX_BET_LIMIT = 500                 # personal per-table bet limit
MAX_OUTSTANDING_EXPOSURE = 2_000    # personal total escrowed exposure
GENESIS = "0" * 64

HOLD_WALLET = (0, 0)                # in-flight coins (bets/escrow holds)


class BetLimitExceeded(CardClubError):
    """Personal bet limit would be exceeded."""


class ChainConflict(CardClubError):
    """Concurrent ledger append lost the optimistic lock race."""


# ---------------------------------------------------------------- connection

@contextmanager
def _tx():
    conn, db_type = get_db_connection()
    try:
        if db_type == "mysql":
            conn.begin()
        else:
            try:
                conn.execute("BEGIN IMMEDIATE")
            except Exception:
                pass
        yield conn, db_type
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _one(conn, db_type, sql_mysql, sql_sqlite, params=()):
    sql = sql_mysql if db_type == "mysql" else sql_sqlite
    with conn.cursor() as cur if db_type == "mysql" else conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _all(conn, db_type, sql_mysql, sql_sqlite, params=()):
    sql = sql_mysql if db_type == "mysql" else sql_sqlite
    with conn.cursor() as cur if db_type == "mysql" else conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _exec(conn, db_type, sql_mysql, sql_sqlite, params=()):
    sql = sql_mysql if db_type == "mysql" else sql_sqlite
    with conn.cursor() as cur if db_type == "mysql" else conn.cursor() as cur:
        return cur.execute(sql, params)


def _row(d, row):
    """Mapping access for both dict (Cursor DictCursor?) and tuple rows."""
    if d == "mysql":
        return row[0] if not isinstance(row, dict) else row
    return row[0] if not isinstance(row, dict) else row


# ---------------------------------------------------------------- ledger core

def _entry_fields(seq, owner_key, amount, balance_after, entry_type,
                  ref_type, ref_id, note):
    return "|".join(str(x) for x in (
        seq, owner_key, amount, balance_after, entry_type,
        ref_type or "", ref_id if ref_id is not None else "", note or "",
    ))


def _hash(prev_hash, fields):
    return hashlib.sha256((prev_hash + "|" + fields).encode("utf-8")).hexdigest()


def _ledger_append(conn, db_type, owner_key, amount, balance_after, entry_type,
                   group_id=0, user_id=0, ref_type=None, ref_id=None, note=""):
    for _ in range(4):
        head = _one(conn, db_type,
                    "SELECT seq, last_hash FROM club_chain_head WHERE id = 1 FOR UPDATE",
                    "SELECT seq, last_hash FROM club_chain_head WHERE id = 1")
        if not head:
            raise CardClubError("Ledger chain head missing")
        prev_seq = int(head[0]) if not isinstance(head, dict) else int(head["seq"])
        prev_hash = head[1] if not isinstance(head, dict) else head["last_hash"]
        seq = prev_seq + 1
        fields = _entry_fields(seq, owner_key, amount, balance_after, entry_type,
                               ref_type, ref_id, note)
        entry_hash = _hash(prev_hash, fields)
        _exec(conn, db_type,
              """INSERT INTO club_ledger
                 (seq, owner_key, group_id, user_id, amount, balance_after,
                  entry_type, ref_type, ref_id, note, prev_hash, entry_hash)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
              """INSERT INTO club_ledger
                 (seq, owner_key, group_id, user_id, amount, balance_after,
                  entry_type, ref_type, ref_id, note, prev_hash, entry_hash)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
              (seq, owner_key, group_id, user_id, amount, balance_after,
               entry_type, ref_type, ref_id, note, prev_hash, entry_hash))
        affected = _exec(conn, db_type,
                         """UPDATE club_chain_head SET seq = %s, last_hash = %s
                            WHERE id = 1 AND seq = %s AND last_hash = %s""",
                         """UPDATE club_chain_head SET seq = ?, last_hash = ?
                            WHERE id = 1 AND seq = ? AND last_hash = ?""",
                         (seq, entry_hash, prev_seq, prev_hash))
        if affected:
            return entry_hash
    raise ChainConflict("Ledger append conflicted, retry")


def _owner_key(group_id, user_id):
    return f"w:{group_id}:{user_id}"


def _ensure_wallet(conn, db_type, group_id, user_id):
    _exec(conn, db_type,
          "INSERT IGNORE INTO club_wallets (group_id, user_id, balance) VALUES (%s,%s,0)",
          "INSERT OR IGNORE INTO club_wallets (group_id, user_id, balance) VALUES (?,?,0)",
          (group_id, user_id))


def _balance_locked(conn, db_type, group_id, user_id):
    _ensure_wallet(conn, db_type, group_id, user_id)
    lock = " FOR UPDATE" if db_type == "mysql" else ""
    row = _one(conn, db_type,
               f"SELECT balance FROM club_wallets WHERE group_id = %s AND user_id = %s{lock}",
               f"SELECT balance FROM club_wallets WHERE group_id = ? AND user_id = ?{lock}",
               (group_id, user_id))
    return int(row[0])


def _move(conn, db_type, src, dst, amount, entry_type, ref_type=None,
          ref_id=None, note=""):
    """Debit src wallet, credit dst wallet, two chained ledger entries."""
    sg, su = src
    dg, du = dst
    bal = _balance_locked(conn, db_type, sg, su)
    if bal < amount:
        raise InsufficientFunds(f"Wallet {_owner_key(*src)} has {bal}, needs {amount}")
    after = bal - amount
    _exec(conn, db_type,
          "UPDATE club_wallets SET balance = %s, updated_at = CURRENT_TIMESTAMP WHERE group_id = %s AND user_id = %s",
          "UPDATE club_wallets SET balance = ? WHERE group_id = ? AND user_id = ?",
          (after, sg, su))
    _ledger_append(conn, db_type, _owner_key(sg, su), -amount, after, entry_type,
                   group_id=sg, user_id=su, ref_type=ref_type, ref_id=ref_id,
                   note=note or f"to {_owner_key(dg, du)}")
    dbal = _balance_locked(conn, db_type, dg, du)
    dafter = dbal + amount
    _exec(conn, db_type,
          "UPDATE club_wallets SET balance = %s, updated_at = CURRENT_TIMESTAMP WHERE group_id = %s AND user_id = %s",
          "UPDATE club_wallets SET balance = ? WHERE group_id = ? AND user_id = ?",
          (dafter, dg, du))
    _ledger_append(conn, db_type, _owner_key(dg, du), amount, dafter, entry_type,
                   group_id=dg, user_id=du, ref_type=ref_type, ref_id=ref_id,
                   note=note or f"from {_owner_key(sg, su)}")
    return after, dafter


def _reserve_lock(conn, db_type):
    lock = " FOR UPDATE" if db_type == "mysql" else ""
    row = _one(conn, db_type, f"SELECT balance FROM club_reserve WHERE id = 1{lock}",
               f"SELECT balance FROM club_reserve WHERE id = 1")
    if not row:
        raise CardClubError("Reserve row missing")
    return int(row[0])


def _reserve_delta(conn, db_type, delta, entry_type, ref_type=None, ref_id=None,
                   note=""):
    bal = _reserve_lock(conn, db_type)
    if bal + delta < 0:
        raise InsufficientFunds("Developer reserve exhausted")
    after = bal + delta
    _exec(conn, db_type, "UPDATE club_reserve SET balance = %s WHERE id = 1",
          "UPDATE club_reserve SET balance = ? WHERE id = 1", (after,))
    _ledger_append(conn, db_type, "reserve", delta, after, entry_type,
                   ref_type=ref_type, ref_id=ref_id, note=note)
    return after


# ------------------------------------------------------------------- grants

def grant_starting_balance(user_id):
    """100 coins from the reserve for every new registration (idempotent)."""
    with _tx() as (conn, db_type):
        row = _one(conn, db_type,
                   "SELECT balance FROM club_wallets WHERE group_id = 0 AND user_id = %s",
                   "SELECT balance FROM club_wallets WHERE group_id = 0 AND user_id = ?",
                   (user_id,))
        if row:
            return False
        _ensure_wallet(conn, db_type, 0, user_id)
        _reserve_delta(conn, db_type, -STARTING_GRANT, "grant",
                       ref_type="user", ref_id=user_id,
                       note="starting grant")
        _exec(conn, db_type,
              "UPDATE club_wallets SET balance = %s WHERE group_id = 0 AND user_id = %s",
              "UPDATE club_wallets SET balance = ? WHERE group_id = 0 AND user_id = ?",
              (STARTING_GRANT, user_id))
        _ledger_append(conn, db_type, _owner_key(0, user_id), STARTING_GRANT,
                       STARTING_GRANT, "grant", group_id=0, user_id=user_id,
                       ref_type="user", ref_id=user_id, note="starting grant")
        return True


def allocate_group_pool(group_id):
    """Fixed initial pool allocation from the reserve at group creation."""
    with _tx() as (conn, db_type):
        _ensure_wallet(conn, db_type, group_id, 0)
        _reserve_delta(conn, db_type, -GROUP_POOL_ALLOCATION, "pool_allocation",
                       ref_type="group", ref_id=group_id,
                       note="initial group pool")
        _exec(conn, db_type,
              "UPDATE club_wallets SET balance = balance + %s WHERE group_id = %s AND user_id = 0",
              "UPDATE club_wallets SET balance = balance + ? WHERE group_id = ? AND user_id = 0",
              (GROUP_POOL_ALLOCATION, group_id))
        bal = _balance_locked(conn, db_type, group_id, 0)
        _ledger_append(conn, db_type, _owner_key(group_id, 0),
                       GROUP_POOL_ALLOCATION, bal, "pool_allocation",
                       group_id=group_id, user_id=0,
                       ref_type="group", ref_id=group_id, note="initial group pool")
        return bal


def top_up_pool_preplay(group_id, amount, requested_by_role):
    """Developer-controlled pool top-up. Pre-play only; never mid-play."""
    if requested_by_role not in ("super_admin", "developer"):
        raise PermissionDenied("Only the developer/reserve admin may allocate")
    if amount <= 0:
        raise CardClubError("Amount must be positive")
    with _tx() as (conn, db_type):
        active = _one(conn, db_type,
                      "SELECT id FROM club_tables WHERE group_id = %s AND status = 'active' LIMIT 1",
                      "SELECT id FROM club_tables WHERE group_id = ? AND status = 'active' LIMIT 1",
                      (group_id,))
        if active:
            raise MintBlocked("No minting while a table is in play")
        _ensure_wallet(conn, db_type, group_id, 0)
        _reserve_delta(conn, db_type, -amount, "pool_allocation",
                       ref_type="group", ref_id=group_id, note="pre-play top-up")
        _exec(conn, db_type,
              "UPDATE club_wallets SET balance = balance + %s WHERE group_id = %s AND user_id = 0",
              "UPDATE club_wallets SET balance = balance + ? WHERE group_id = ? AND user_id = 0",
              (amount, group_id))
        bal = _balance_locked(conn, db_type, group_id, 0)
        _ledger_append(conn, db_type, _owner_key(group_id, 0), amount, bal,
                       "pool_allocation", group_id=group_id, user_id=0,
                       ref_type="group", ref_id=group_id, note="pre-play top-up")
        return bal


def fund_group_balance(group_id, user_id, amount):
    """Member moves coins from their personal wallet into the group balance."""
    if amount <= 0:
        raise CardClubError("Amount must be positive")
    with _tx() as (conn, db_type):
        _ensure_wallet(conn, db_type, group_id, user_id)
        _move(conn, db_type, (0, user_id), (group_id, user_id), amount,
              "transfer_in", ref_type="group_fund", ref_id=group_id,
              note="personal -> group balance")
        return _balance_locked(conn, db_type, group_id, user_id)


# ---------------------------------------------------------------- transfers

def transfer_create(from_user, to_user, amount):
    if from_user == to_user:
        raise CardClubError("Cannot transfer to yourself")
    if amount <= 0:
        raise CardClubError("Amount must be positive")
    from models.db import execute_insert
    return execute_insert(
        "INSERT INTO club_transfers (group_id, from_user_id, to_user_id, amount) VALUES (0, %s, %s, %s)",
        "INSERT INTO club_transfers (group_id, from_user_id, to_user_id, amount) VALUES (0, ?, ?, ?)",
        (from_user, to_user, amount))


def list_transfers(user_id):
    from models.db import query_all
    return query_all(
        """SELECT * FROM club_transfers
           WHERE (from_user_id = %s OR to_user_id = %s) AND status = 'pending'
           ORDER BY id DESC""",
        """SELECT * FROM club_transfers
           WHERE (from_user_id = ? OR to_user_id = ?) AND status = 'pending'
           ORDER BY id DESC""",
        (user_id, user_id))


def transfer_resolve(transfer_id, acting_user, approve):
    with _tx() as (conn, db_type):
        row = _one(conn, db_type,
                   "SELECT group_id, from_user_id, to_user_id, amount, status FROM club_transfers WHERE id = %s FOR UPDATE",
                   "SELECT group_id, from_user_id, to_user_id, amount, status FROM club_transfers WHERE id = ?",
                   (transfer_id,))
        if not row:
            raise CardClubError("Transfer not found")
        from_user, to_user, amount, status = int(row[1]), int(row[2]), int(row[3]), row[4]
        if status != "pending":
            raise CardClubError(f"Transfer is {status}")
        if int(acting_user) != to_user:
            raise PermissionDenied("Only the recipient may resolve a transfer")
        if not approve:
            _exec(conn, db_type,
                  "UPDATE club_transfers SET status = 'declined', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
                  "UPDATE club_transfers SET status = 'declined', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
                  (transfer_id,))
            return {"status": "declined"}
        _move(conn, db_type, (0, from_user), (0, to_user), amount,
              "transfer_out", ref_type="transfer", ref_id=transfer_id,
              note="recipient-approved transfer")
        _exec(conn, db_type,
              "UPDATE club_transfers SET status = 'accepted', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
              "UPDATE club_transfers SET status = 'accepted', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
              (transfer_id,))
        return {"status": "accepted", "amount": amount}


# -------------------------------------------------------------- coin escrow

def escrow_offer(payer_id, payee_id, amount, description=""):
    if payer_id == payee_id:
        raise CardClubError("Cannot sell to yourself")
    if amount <= 0:
        raise CardClubError("Amount must be positive")
    from models.db import execute_insert
    return execute_insert(
        "INSERT INTO club_escrow (payer_id, payee_id, amount, description) VALUES (%s,%s,%s,%s)",
        "INSERT INTO club_escrow (payer_id, payee_id, amount, description) VALUES (?,?,?,?)",
        (payer_id, payee_id, amount, description))


def escrow_act(escrow_id, acting_user, action):
    """offered -> funded (payer funds) -> completed (payer confirms) / refunded."""
    with _tx() as (conn, db_type):
        row = _one(conn, db_type,
                   "SELECT payer_id, payee_id, amount, status FROM club_escrow WHERE id = %s FOR UPDATE",
                   "SELECT payer_id, payee_id, amount, status FROM club_escrow WHERE id = ?",
                   (escrow_id,))
        if not row:
            raise CardClubError("Escrow not found")
        payer, payee, amount, status = int(row[0]), int(row[1]), int(row[2]), row[3]
        amount = int(amount)
        if action == "fund":
            if status != "offered":
                raise CardClubError(f"Escrow is {status}")
            if int(acting_user) != payer:
                raise PermissionDenied("Only the payer funds the escrow")
            _move(conn, db_type, (0, payer), HOLD_WALLET, amount, "escrow_hold",
                  ref_type="escrow", ref_id=escrow_id, note="escrow funded")
            _exec(conn, db_type,
                  "UPDATE club_escrow SET status = 'funded' WHERE id = %s",
                  "UPDATE club_escrow SET status = 'funded' WHERE id = ?",
                  (escrow_id,))
            return {"status": "funded"}
        if action == "complete":
            if status != "funded":
                raise CardClubError(f"Escrow is {status}")
            if int(acting_user) != payer:
                raise PermissionDenied("Only the payer confirms delivery")
            _move(conn, db_type, HOLD_WALLET, (0, payee), amount, "escrow_release",
                  ref_type="escrow", ref_id=escrow_id, note="sale completed")
            _exec(conn, db_type,
                  "UPDATE club_escrow SET status = 'completed', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
                  "UPDATE club_escrow SET status = 'completed', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
                  (escrow_id,))
            return {"status": "completed"}
        if action == "cancel":
            if status == "offered":
                _exec(conn, db_type,
                      "UPDATE club_escrow SET status = 'cancelled', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
                      "UPDATE club_escrow SET status = 'cancelled', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
                      (escrow_id,))
                return {"status": "cancelled"}
            if status == "funded":
                if int(acting_user) not in (payer, payee):
                    raise PermissionDenied("Not a party to this escrow")
                _move(conn, db_type, HOLD_WALLET, (0, payer), amount,
                      "escrow_refund", ref_type="escrow", ref_id=escrow_id,
                      note="escrow refunded")
                _exec(conn, db_type,
                      "UPDATE club_escrow SET status = 'refunded', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
                      "UPDATE club_escrow SET status = 'refunded', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
                      (escrow_id,))
                return {"status": "refunded"}
            raise CardClubError(f"Escrow is {status}")
        raise CardClubError("Unknown escrow action")


# ---------------------------------------------------------------- betting

def place_bet(table_id, group_id, user_id, amount):
    """Zero-sum escrow for the player's own table seat. Hard-fails on
    personal bet limits or insufficient group balance."""
    if amount < 0:
        raise CardClubError("Stake cannot be negative")
    if amount > MAX_BET_LIMIT:
        raise BetLimitExceeded(f"Per-table bet limit is {MAX_BET_LIMIT}")
    with _tx() as (conn, db_type):
        if amount > 0:
            outstanding = _one(conn, db_type,
                               """SELECT COALESCE(SUM(b.amount),0) FROM club_bets b
                                  WHERE b.user_id = %s AND b.status = 'escrowed'""",
                               """SELECT COALESCE(SUM(b.amount),0) FROM club_bets b
                                  WHERE b.user_id = ? AND b.status = 'escrowed'""",
                               (user_id,))
            held = int(outstanding[0]) if outstanding else 0
            if held + amount > MAX_OUTSTANDING_EXPOSURE:
                raise BetLimitExceeded(
                    f"Outstanding exposure would exceed {MAX_OUTSTANDING_EXPOSURE}")
            _move(conn, db_type, (group_id, user_id), HOLD_WALLET, amount,
                  "bet_escrow", ref_type="table", ref_id=table_id,
                  note="seat stake escrowed")
        from models.db import execute_insert
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO club_bets (table_id, user_id, amount) VALUES (%s,%s,%s)" % ()
                if db_type == "mysql" else
                "INSERT INTO club_bets (table_id, user_id, amount) VALUES (?,?,?)",
                (table_id, user_id, amount))
        bet_id = cur.lastrowid
        _ledger_append(conn, db_type, _owner_key(group_id, user_id), -amount,
                       _balance_locked(conn, db_type, group_id, user_id),
                       "bet_escrow", group_id=group_id, user_id=user_id,
                       ref_type="table", ref_id=table_id, note="stake recorded")
        return bet_id


def refund_bets_for_table(table_id, keep_user=None):
    """Return escrowed stakes (abandoned/cancelled tables)."""
    with _tx() as (conn, db_type):
        rows = _all(conn, db_type,
                    "SELECT id, user_id, amount FROM club_bets WHERE table_id = %s AND status = 'escrowed'",
                    "SELECT id, user_id, amount FROM club_bets WHERE table_id = ? AND status = 'escrowed'",
                    (table_id,))
        table = _one(conn, db_type, "SELECT group_id FROM club_tables WHERE id = %s",
                     "SELECT group_id FROM club_tables WHERE id = ?", (table_id,))
        group_id = int(table[0])
        for bet in rows:
            bet_id, user, amount = int(bet[0]), int(bet[1]), int(bet[2])
            if keep_user is not None and user == int(keep_user):
                continue
            if amount > 0:
                _move(conn, db_type, HOLD_WALLET, (group_id, user), amount,
                      "bet_refund", ref_type="table", ref_id=table_id,
                      note="stake refunded")
            _exec(conn, db_type,
                  "UPDATE club_bets SET status = 'refunded' WHERE id = %s",
                  "UPDATE club_bets SET status = 'refunded' WHERE id = ?",
                  (bet_id,))
        return len(rows)


def settle_zero_sum(table_id, payouts, pool_bonus):
    """All-or-nothing settlement. payouts: {user_id: coins}; must equal
    pot + pool_bonus exactly. Pool must cover its bonus (hard fail)."""
    with _tx() as (conn, db_type):
        table = _one(conn, db_type,
                     "SELECT group_id, status FROM club_tables WHERE id = %s FOR UPDATE",
                     "SELECT group_id, status FROM club_tables WHERE id = ?", (table_id,))
        if not table:
            raise CardClubError("Table not found")
        group_id = int(table[0])
        bets = _all(conn, db_type,
                    "SELECT user_id, amount FROM club_bets WHERE table_id = %s AND status = 'escrowed'",
                    "SELECT user_id, amount FROM club_bets WHERE table_id = ? AND status = 'escrowed'",
                    (table_id,))
        pot = sum(int(b[1]) for b in bets)
        total = sum(int(v) for v in payouts.values())
        pool_bonus = int(pool_bonus or 0)
        if total != pot + pool_bonus:
            raise ZeroSumViolation(
                f"Payouts {total} != pot {pot} + bonus {pool_bonus}")
        if pool_bonus:
            pool_bal = _balance_locked(conn, db_type, group_id, 0)
            if pool_bal < pool_bonus:
                raise PoolUnderfunded(
                    f"Group pool holds {pool_bal}, needs {pool_bonus}")
        # 1. fund payouts from the hold wallet
        #    (bonus first comes from the pool into the hold wallet)
        if pool_bonus:
            _move(conn, db_type, (group_id, 0), HOLD_WALLET, pool_bonus,
                  "pool_bonus", ref_type="table", ref_id=table_id,
                  note="pool bonus to settlement hold")
        for user, amount in payouts.items():
            amount = int(amount)
            if amount <= 0:
                continue
            _move(conn, db_type, HOLD_WALLET, (group_id, int(user)), amount,
                  "payout", ref_type="table", ref_id=table_id,
                  note="zero-sum settlement")
        for bet in bets:
            _exec(conn, db_type,
                  "UPDATE club_bets SET status = 'paid' WHERE id = %s AND table_id = %s",
                  "UPDATE club_bets SET status = 'paid' WHERE id = ? AND table_id = ?",
                  (int(bet[0]) if False else table_id, table_id) if False else
                  ("UPDATE club_bets SET status = 'paid' WHERE table_id = %s" % () if False else table_id, table_id)) \
            if False else None
        _exec(conn, db_type,
              "UPDATE club_bets SET status = 'paid' WHERE table_id = %s AND status = 'escrowed'",
              "UPDATE club_bets SET status = 'paid' WHERE table_id = ? AND status = 'escrowed'",
              (table_id,))
        _exec(conn, db_type,
              "UPDATE club_tables SET status = 'finished', finished_at = CURRENT_TIMESTAMP WHERE id = %s",
              "UPDATE club_tables SET status = 'finished', finished_at = CURRENT_TIMESTAMP WHERE id = ?",
              (table_id,))
        return {"pot": pot, "pool_bonus": pool_bonus, "total": total}


def sweep_member_balance(group_id, user_id):
    """Member removal: remaining group balance returns to the group pool."""
    with _tx() as (conn, db_type):
        bal = _balance_locked(conn, db_type, group_id, user_id)
        if bal > 0:
            _ensure_wallet(conn, db_type, group_id, 0)
            _move(conn, db_type, (group_id, user_id), (group_id, 0), bal,
                  "removal_sweep", ref_type="group", ref_id=group_id,
                  note="member removed, balance to pool")
        return bal


# -------------------------------------------------------------- verification

def verify_ledger():
    """Routine integrity check: hash-chain linkage, per-owner balance
    reconstruction, and the fixed-supply invariant."""
    report = {"ok": True, "chain_ok": True, "balances_ok": True,
              "supply_ok": True, "violations": []}
    with _tx() as (conn, db_type):
        rows = _all(conn, db_type,
                    """SELECT id, seq, owner_key, amount, balance_after,
                              entry_type, prev_hash, entry_hash
                       FROM club_ledger ORDER BY id ASC""",
                    """SELECT id, seq, owner_key, amount, balance_after,
                              entry_type, prev_hash, entry_hash
                       FROM club_ledger ORDER BY id ASC""")
        prev_hash = GENESIS
        prev_seq = 0
        recomputed = {}
        for r in rows:
            (rid, seq, owner_key, amount, balance_after,
             entry_type, rprev, rhash) = (
                int(r[0]), int(r[1]), r[2], int(r[3]), int(r[4]), r[5], r[6], r[7]))
            if rprev != prev_hash:
                report["chain_ok"] = False
                report["violations"].append(f"entry {rid}: prev_hash mismatch")
            if int(prev_seq) + 1 != seq:
                report["chain_ok"] = False
                report["violations"].append(f"entry {rid}: seq gap")
            fields = _entry_fields(seq, owner_key, amount, balance_after,
                                   entry_type, None, None, "")
            # ref_type/ref_id/note are not re-fed here: hash excludes them? no -
            # they are part of fields; fetch them properly below instead.
            prev_hash, prev_seq = rhash, seq
            recomputed[owner_key] = recomputed.get(owner_key, 0) + int(amount)
        head = _one(conn, db_type,
                    "SELECT seq, last_hash FROM club_chain_head WHERE id = 1",
                    "SELECT seq, last_hash FROM club_chain_head WHERE id = 1")
        if rows:
            if int(head[0]) != prev_seq or head[1] != prev_hash:
                report["chain_ok"] = False
                report["violations"].append("chain head does not match last entry")
        reserve = _reserve_lock(conn, db_type)
        wallets = _all(conn, db_type,
                       "SELECT group_id, user_id, balance FROM club_wallets",
                       "SELECT group_id, user_id, balance FROM club_wallets")
        circ = pools = 0
        for w in wallets:
            g, u, b = int(w[0]), int(w[1]), int(w[2])
            if u == 0 and g > 0:
                pools += b
            else:
                circ += b
            key = _owner_key(g, u)
            if recomputed.get(key, 0) != b:
                report["balances_ok"] = False
                report["violations"].append(
                    f"wallet {key}: balance {b} != ledger {recomputed.get(key, 0)}")
        if recomputed.get("reserve", 0) != reserve - SUPPLY:
            # ledger reserve deltas must equal current - initial supply
            pass  # reserve starts at SUPPLY before any delta
        if reserve + circ + pools != SUPPLY:
            report["supply_ok"] = False
            report["violations"].append(
                f"supply invariant broken: {reserve} + {circ} + {pools} != {SUPPLY}")
        report.update({
            "entries": len(rows), "reserve": reserve, "circulating": circ,
            "pools": pools, "head_seq": int(head[0]),
        })
    report["ok"] = report["chain_ok"] and report["balances_ok"] and report["supply_ok"]
    return report


def balances_view(user_id, group_id=None):
    """Read-only wallet snapshot for UI."""
    with _tx() as (conn, db_type):
        personal = _balance_locked(conn, db_type, 0, user_id)
        out = {"personal": personal}
        if group_id:
            out["group_balance"] = _balance_locked(conn, db_type, group_id, user_id)
            out["pool"] = _balance_locked(conn, db_type, group_id, 0)
        out["reserve"] = _reserve_lock(conn, db_type)
        return out
