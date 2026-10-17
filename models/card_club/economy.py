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
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        row = cur.fetchone()
        if isinstance(row, dict):
            return tuple(row.values())
        return row
    finally:
        try:
            cur.close()
        except Exception:
            pass


def _all(conn, db_type, sql_mysql, sql_sqlite, params=()):
    sql = sql_mysql if db_type == "mysql" else sql_sqlite
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        if rows and isinstance(rows[0], dict):
            return [tuple(r.values()) for r in rows]
        return rows
    finally:
        try:
            cur.close()
        except Exception:
            pass


def _exec(conn, db_type, sql_mysql, sql_sqlite, params=()):
    sql = sql_mysql if db_type == "mysql" else sql_sqlite
    cur = conn.cursor()
    try:
        affected = cur.execute(sql, params)
        return affected if affected is not None else cur.rowcount
    finally:
        try:
            cur.close()
        except Exception:
            pass


def _insert(conn, db_type, sql_mysql, sql_sqlite, params=()):
    sql = sql_mysql if db_type == "mysql" else sql_sqlite
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.lastrowid
    finally:
        try:
            cur.close()
        except Exception:
            pass


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
    if db_type == "sqlite":
        _exec(conn, db_type,
              "INSERT OR IGNORE INTO club_wallets (group_id, user_id, balance) VALUES (?,?,0)",
              "INSERT OR IGNORE INTO club_wallets (group_id, user_id, balance) VALUES (?,?,0)",
              (group_id, user_id))
        return
    try:
        _exec(conn, db_type,
              "INSERT INTO club_wallets (group_id, user_id, balance) VALUES (%s,%s,0)",
              "INSERT INTO club_wallets (group_id, user_id, balance) VALUES (%s,%s,0)",
              (group_id, user_id))
    except Exception:
        # Duplicate key on MySQL does not abort the transaction: confirm row.
        row = _one(conn, db_type,
                   "SELECT balance FROM club_wallets WHERE group_id = %s AND user_id = %s",
                   "SELECT balance FROM club_wallets WHERE group_id = %s AND user_id = %s",
                   (group_id, user_id))
        if not row:
            raise


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


def replenish_wallet(user_id, amount=100, max_balance=None):
    """Claim top-up coins from the developer reserve when user balance is low.

    ``max_balance`` (when given) is re-checked *inside* the wallet lock so
    concurrent claims cannot all pass a stale pre-check and mint repeatedly.
    """
    with _tx() as (conn, db_type):
        _ensure_wallet(conn, db_type, 0, user_id)
        cur = _balance_locked(conn, db_type, 0, user_id)
        if max_balance is not None and cur > max_balance:
            raise CardClubError("Wallet balance too high to claim a refill")
        _reserve_delta(conn, db_type, -amount, "grant_refill",
                       ref_type="user", ref_id=user_id, note="wallet replenishment")
        after = cur + amount
        _exec(conn, db_type,
              "UPDATE club_wallets SET balance = %s WHERE group_id = 0 AND user_id = %s",
              "UPDATE club_wallets SET balance = ? WHERE group_id = 0 AND user_id = ?",
              (after, user_id))
        _ledger_append(conn, db_type, _owner_key(0, user_id), amount, after,
                       "grant_refill", group_id=0, user_id=user_id,
                       ref_type="user", ref_id=user_id, note="wallet replenishment")
        return after


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
            # Lock the payer's wallet first: concurrent stakes otherwise all
            # read the same pre-lock exposure snapshot and bypass the cap.
            _balance_locked(conn, db_type, group_id, user_id)
            outstanding = _one(conn, db_type,
                               """SELECT COALESCE(SUM(amount),0) FROM club_bets
                                  WHERE user_id = %s AND status = 'escrowed' FOR UPDATE""",
                               """SELECT COALESCE(SUM(amount),0) FROM club_bets
                                  WHERE user_id = ? AND status = 'escrowed'""",
                               (user_id,))
            held = int(outstanding[0]) if outstanding else 0
            if held + amount > MAX_OUTSTANDING_EXPOSURE:
                raise BetLimitExceeded(
                    f"Outstanding exposure would exceed {MAX_OUTSTANDING_EXPOSURE}")
            _move(conn, db_type, (group_id, user_id), HOLD_WALLET, amount,
                  "bet_escrow", ref_type="table", ref_id=table_id,
                  note="seat stake escrowed")
        bet_id = _insert(conn, db_type,
                         "INSERT INTO club_bets (table_id, user_id, amount) VALUES (%s,%s,%s)",
                         "INSERT INTO club_bets (table_id, user_id, amount) VALUES (?,?,?)",
                         (table_id, user_id, amount))
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
        _exec(conn, db_type,
              "UPDATE club_bets SET status = 'paid' WHERE table_id = %s AND status = 'escrowed'",
              "UPDATE club_bets SET status = 'paid' WHERE table_id = ? AND status = 'escrowed'",
              (table_id,))
        _exec(conn, db_type,
              "UPDATE club_tables SET status = 'finished', finished_at = CURRENT_TIMESTAMP WHERE id = %s",
              "UPDATE club_tables SET status = 'finished', finished_at = CURRENT_TIMESTAMP WHERE id = ?",
              (table_id,))
        return {"pot": pot, "pool_bonus": pool_bonus, "total": total}


# ---------------------------------------------- classic suite escrow
# The Classic Playing Cards Suite keeps its own stake table (it never creates
# a club_tables row) but every coin still travels through the same hold wallet
# and hash-chained ledger, so classic wins/losses show up in /club/ledger and
# pass verify_ledger() exactly like club bets do.

def place_classic_stake(game_id, user_id, amount, group_id=0):
    """Escrow one seat's stake for a Classic Suite game."""
    amount = int(amount or 0)
    if amount < 0:
        raise CardClubError("Stake cannot be negative")
    if amount > MAX_BET_LIMIT:
        raise BetLimitExceeded(f"Per-table bet limit is {MAX_BET_LIMIT}")
    with _tx() as (conn, db_type):
        if amount > 0:
            # Lock the payer's wallet before the exposure snapshot (see place_bet).
            _balance_locked(conn, db_type, group_id, user_id)
            outstanding = _one(
                conn, db_type,
                """SELECT COALESCE(SUM(amount),0) FROM classic_stakes
                   WHERE user_id = %s AND status = 'escrowed' FOR UPDATE""",
                """SELECT COALESCE(SUM(amount),0) FROM classic_stakes
                   WHERE user_id = ? AND status = 'escrowed'""",
                (user_id,))
            held = int(outstanding[0]) if outstanding else 0
            if held + amount > MAX_OUTSTANDING_EXPOSURE:
                raise BetLimitExceeded(
                    f"Outstanding exposure would exceed {MAX_OUTSTANDING_EXPOSURE}")
            _move(conn, db_type, (group_id, user_id), HOLD_WALLET, amount,
                  "bet_escrow", ref_type="classic_game", ref_id=game_id,
                  note="classic seat stake escrowed")
        return _insert(
            conn, db_type,
            "INSERT INTO classic_stakes (game_id, user_id, amount) VALUES (%s,%s,%s)",
            "INSERT INTO classic_stakes (game_id, user_id, amount) VALUES (?,?,?)",
            (game_id, user_id, amount))


def refund_classic_stakes(game_id, group_id=0, user_id=None):
    """Return escrowed stakes (abandoned or cancelled classic game). When
    ``user_id`` is given only that seat's stake is released."""
    with _tx() as (conn, db_type):
        if user_id is None:
            sql_m = ("SELECT id, user_id, amount FROM classic_stakes "
                     "WHERE game_id = %s AND status = 'escrowed'")
            sql_s = ("SELECT id, user_id, amount FROM classic_stakes "
                     "WHERE game_id = ? AND status = 'escrowed'")
            params = (game_id,)
        else:
            sql_m = ("SELECT id, user_id, amount FROM classic_stakes "
                     "WHERE game_id = %s AND user_id = %s AND status = 'escrowed'")
            sql_s = ("SELECT id, user_id, amount FROM classic_stakes "
                     "WHERE game_id = ? AND user_id = ? AND status = 'escrowed'")
            params = (game_id, user_id)
        rows = _all(conn, db_type, sql_m, sql_s, params)
        for st in rows or []:
            stake_id, user, amount = int(st[0]), int(st[1]), int(st[2])
            if amount > 0:
                _move(conn, db_type, HOLD_WALLET, (group_id, user), amount,
                      "bet_refund", ref_type="classic_game", ref_id=game_id,
                      note="classic stake refunded")
            _exec(conn, db_type,
                  "UPDATE classic_stakes SET status = 'refunded' WHERE id = %s",
                  "UPDATE classic_stakes SET status = 'refunded' WHERE id = ?",
                  (stake_id,))
        return len(rows or [])


def settle_classic(game_id, payouts, group_id=0):
    """Distribute a finished Classic Suite pot. Payouts must equal the pot
    exactly (zero-sum) and every leg is hash-chained onto the ledger."""
    with _tx() as (conn, db_type):
        stakes = _all(
            conn, db_type,
            "SELECT user_id, amount FROM classic_stakes "
            "WHERE game_id = %s AND status = 'escrowed'",
            "SELECT user_id, amount FROM classic_stakes "
            "WHERE game_id = ? AND status = 'escrowed'",
            (game_id,))
        pot = sum(int(s[1]) for s in stakes or [])
        total = sum(int(v) for v in payouts.values())
        if total != pot:
            raise ZeroSumViolation(f"Payouts {total} != pot {pot}")
        for user, amount in payouts.items():
            amount = int(amount)
            if amount <= 0:
                continue
            _move(conn, db_type, HOLD_WALLET, (group_id, int(user)), amount,
                  "payout", ref_type="classic_game", ref_id=game_id,
                  note="classic suite settlement")
        _exec(conn, db_type,
              "UPDATE classic_stakes SET status = 'paid' "
              "WHERE game_id = %s AND status = 'escrowed'",
              "UPDATE classic_stakes SET status = 'paid' "
              "WHERE game_id = ? AND status = 'escrowed'",
              (game_id,))
        return {"pot": pot, "total": total}


def classic_stakes(game_id, status=None):
    with _tx() as (conn, db_type):
        if status:
            sql_m = ("SELECT user_id, amount FROM classic_stakes "
                     "WHERE game_id = %s AND status = %s")
            sql_s = ("SELECT user_id, amount FROM classic_stakes "
                     "WHERE game_id = ? AND status = ?")
            params = (game_id, status)
        else:
            sql_m = "SELECT user_id, amount FROM classic_stakes WHERE game_id = %s"
            sql_s = "SELECT user_id, amount FROM classic_stakes WHERE game_id = ?"
            params = (game_id,)
        rows = _all(conn, db_type, sql_m, sql_s, params)
        return [{"user_id": int(r[0]), "amount": int(r[1])} for r in rows or []]


def ledger_for_user(user_id, group_id=0, limit=30):
    """Most recent hash-chained entries for one wallet (coin history feed)."""
    limit = max(1, min(int(limit or 30), 200))
    with _tx() as (conn, db_type):
        rows = _all(conn, db_type,
            """SELECT seq, amount, balance_after, entry_type, ref_type, ref_id,
                      note, entry_hash, created_at
                 FROM club_ledger
                WHERE owner_key = %s
                ORDER BY seq DESC LIMIT %s""",
            """SELECT seq, amount, balance_after, entry_type, ref_type, ref_id,
                      note, entry_hash, created_at
                 FROM club_ledger
                WHERE owner_key = ?
                ORDER BY seq DESC LIMIT ?""",
            (_owner_key(int(group_id or 0), user_id), limit))
        out = []
        for r in rows or []:
            seq, amount, after = int(r[0]), int(r[1]), int(r[2])
            out.append({
                "seq": seq,
                "amount": amount,
                "balance_after": after,
                "entry_type": r[3],
                "ref_type": r[4],
                "ref_id": int(r[5]) if r[5] is not None else None,
                "note": r[6] or "",
                "entry_hash": r[7],
                "created_at": str(r[8]) if r[8] is not None else "",
            })
        return out


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
                              entry_type, ref_type, ref_id, note,
                              prev_hash, entry_hash
                       FROM club_ledger ORDER BY id ASC""",
                    """SELECT id, seq, owner_key, amount, balance_after,
                              entry_type, ref_type, ref_id, note,
                              prev_hash, entry_hash
                       FROM club_ledger ORDER BY id ASC""")
        prev_hash = GENESIS
        prev_seq = 0
        recomputed = {}
        for r in rows:
            rid = int(r[0]); seq = int(r[1]); owner_key = r[2]
            amount = int(r[3]); balance_after = int(r[4]); entry_type = r[5]
            ref_type = r[6]; ref_id = r[7]; note = r[8]
            rprev = r[9]; rhash = r[10]
            if rprev != prev_hash:
                report["chain_ok"] = False
                report["violations"].append(f"entry {rid}: prev_hash mismatch")
            if prev_seq + 1 != seq:
                report["chain_ok"] = False
                report["violations"].append(f"entry {rid}: seq gap")
            fields = _entry_fields(seq, owner_key, amount, balance_after,
                                   entry_type, ref_type, ref_id, note)
            expect = _hash(prev_hash, fields)
            if expect != rhash:
                report["chain_ok"] = False
                report["violations"].append(f"entry {rid}: content hash mismatch (tampered?)")
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
            report["balances_ok"] = False
            report["violations"].append(
                f"reserve ledger sum {recomputed.get('reserve', 0)} != "
                f"current reserve {reserve} - supply {SUPPLY}")
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
