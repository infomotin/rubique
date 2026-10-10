"""Table lifecycle: seats, stakes, engine moves, zero-sum settlement."""

import json
import random

from models.db import query_one, query_all, execute_insert, execute_update
from models.card_club import economy, groups
from models.card_club.errors import (
    CardClubError, IllegalMove, NotFoundError, PermissionDenied,
)
from models.card_club.engines import CATALOG


def _loads(text):
    try:
        return json.loads(text or "{}")
    except Exception:
        return {}


def catalog_entry(slug):
    info = CATALOG.get(slug)
    if not info:
        raise CardClubError(f"Unknown game '{slug}'")
    return info


def get_table(table_id):
    return query_one("SELECT * FROM club_tables WHERE id = %s",
                     "SELECT * FROM club_tables WHERE id = ?", (table_id,))


def seats(table_id):
    t = get_table(table_id)
    is_priv = bool(t.get("is_private", 1) if isinstance(t, dict) else 1) if t else 1
    rows = query_all(
        """SELECT s.id, s.user_id, s.seat_index, s.status, s.rules_read, s.camera_active, s.fake_name, u.username
           FROM club_seats s JOIN users u ON u.id = s.user_id
           WHERE s.table_id = %s ORDER BY s.seat_index ASC""",
        """SELECT s.id, s.user_id, s.seat_index, s.status, s.rules_read, s.camera_active, s.fake_name, u.username
           FROM club_seats s JOIN users u ON u.id = s.user_id
           WHERE s.table_id = ? ORDER BY s.seat_index ASC""",
        (table_id,))
    out = []
    for r in rows or []:
        d = dict(r) if isinstance(r, dict) else {
            "id": r[0], "user_id": r[1], "seat_index": r[2], "status": r[3],
            "rules_read": r[4], "camera_active": r[5], "fake_name": r[6], "username": r[7]
        }
        if is_priv and d.get("fake_name"):
            d["display_name"] = d["fake_name"]
            d["username"] = d["fake_name"]  # Mask real username in private tables
        else:
            d["display_name"] = d.get("fake_name") or d.get("username")
        out.append(d)
    return out



def list_tables(group_id, include_finished=False):
    sql_m = "SELECT * FROM club_tables WHERE group_id = %s"
    sql_s = "SELECT * FROM club_tables WHERE group_id = ?"
    if not include_finished:
        sql_m += " AND status != 'finished'"
        sql_s += " AND status != 'finished'"
    return query_all(sql_m + " ORDER BY id DESC", sql_s + " ORDER BY id DESC",
                     (group_id,))


def table_pot(table_id):
    row = query_one(
        "SELECT COALESCE(SUM(amount),0) FROM club_bets WHERE table_id = %s AND status = 'escrowed'",
        "SELECT COALESCE(SUM(amount),0) FROM club_bets WHERE table_id = ? AND status = 'escrowed'",
        (table_id,))
    return int(row[0] if not isinstance(row, dict) else list(row.values())[0])


def create_table(group_id, user_id, slug, stake=0, pool_bonus=0, name="",
                 max_seats=None, is_private=1, mode="multiplayer", fake_name=""):
    groups.require_member(group_id, user_id)
    info = catalog_entry(slug)
    stake = int(stake or 0)
    pool_bonus = int(pool_bonus or 0)
    if stake < 0 or pool_bonus < 0:
        raise CardClubError("Stake and bonus must be non-negative")
    if stake > economy.MAX_BET_LIMIT:
        raise CardClubError(
            f"Stake exceeds personal bet limit ({economy.MAX_BET_LIMIT})")
    if pool_bonus:
        pool = economy.balances_view(user_id, group_id)["pool"]
        if pool < pool_bonus:
            raise CardClubError("Group pool cannot cover this table bonus")

    # Determine max_seats from user selection or defaults
    if max_seats is not None:
        try:
            max_seats = int(max_seats)
            if max_seats < info["min"] or max_seats > info["max"]:
                max_seats = info["max"]
        except (ValueError, TypeError):
            max_seats = info["max"]
    else:
        max_seats = info["max"]

    is_priv = 1 if is_private else 0

    # Strict coin check: If player has 0 coins or less than stake, block creation
    if stake > 0:
        bal_view = economy.balances_view(user_id, group_id)
        if bal_view["group_balance"] < stake and bal_view["personal"] < stake:
            raise CardClubError("Coins finished! You do not have enough coins to play with this stake. Please add coins first.")

    tid = execute_insert(
        """INSERT INTO club_tables
           (group_id, game_slug, name, stake, pool_bonus, max_seats, created_by, is_private, mode)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        """INSERT INTO club_tables
           (group_id, game_slug, name, stake, pool_bonus, max_seats, created_by, is_private, mode)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (group_id, slug, name or info["name"], stake, pool_bonus,
         max_seats, user_id, is_priv, mode))

    join_table(group_id, user_id, tid, fake_name=fake_name)          # creator sits first
    return get_table(tid)


def join_table(group_id, user_id, table_id, fake_name=""):
    groups.require_member(group_id, user_id)
    t = get_table(table_id)
    if not t or int(t["group_id"]) != group_id:
        raise NotFoundError("Table not found")
    if t["status"] != "waiting":
        raise CardClubError("Table already started")
    info = catalog_entry(t["game_slug"])
    seated = seats(table_id)
    if any(int(s["user_id"]) == int(user_id) for s in seated):
        raise CardClubError("Already seated")

    # Strict Quota limit: First-come, first-served
    max_limit = int(t["max_seats"] or info["max"])
    if len(seated) >= max_limit:
        raise CardClubError("Table quota is full (কোটা পূর্ণ হয়েছে). No new players can join.")

    stake = int(t["stake"] or 0)
    if stake > 0:
        bal_view = economy.balances_view(user_id, group_id)
        if bal_view["group_balance"] < stake:
            # If user has personal balance, auto fund into group balance
            needed = stake - bal_view["group_balance"]
            if bal_view["personal"] >= needed:
                economy.fund_group_balance(group_id, user_id, needed)
            else:
                raise CardClubError("Coins finished! You do not have enough coins to join this table. Please add coins first.")

    bet_id = economy.place_bet(table_id, group_id, user_id, stake)
    next_idx = max([int(s["seat_index"]) for s in seated] or [-1]) + 1
    fn = (fake_name or "").strip() or None
    try:
        execute_insert(
            "INSERT INTO club_seats (table_id, user_id, seat_index, fake_name) VALUES (%s,%s,%s,%s)",
            "INSERT INTO club_seats (table_id, user_id, seat_index, fake_name) VALUES (?,?,?,?)",
            (table_id, user_id, next_idx, fn))
    except Exception:
        if stake > 0:
            _refund_one(table_id, group_id, user_id, stake)
        raise
    return bet_id


def leave_table(group_id, user_id, table_id):
    """Only before start: refunds the escrowed stake."""
    groups.require_member(group_id, user_id)
    t = get_table(table_id)
    if not t or int(t["group_id"]) != group_id:
        raise NotFoundError("Table not found")
    if t["status"] != "waiting":
        raise CardClubError("Cannot leave once started (play or abandon)")
    row = query_one(
        "SELECT id FROM club_seats WHERE table_id = %s AND user_id = %s",
        "SELECT id FROM club_seats WHERE table_id = ? AND user_id = ?",
        (table_id, user_id))
    if not row:
        raise CardClubError("Not seated")
    sid = int(row["id"] if isinstance(row, dict) else row[0])
    _refund_one(table_id, group_id, user_id, stake_amount(t, table_id))
    execute_update(
        "UPDATE club_bets SET status = 'refunded' WHERE table_id = %s AND user_id = %s AND status = 'escrowed'",
        "UPDATE club_bets SET status = 'refunded' WHERE table_id = ? AND user_id = ? AND status = 'escrowed'",
        (table_id, user_id))
    execute_update("DELETE FROM club_seats WHERE id = %s",
                   "DELETE FROM club_seats WHERE id = ?", (sid,))
    return True


def stake_amount(t, table_id):
    return int(t["stake"] or 0)


def _refund_one(table_id, group_id, user_id, amount):
    if amount <= 0:
        return
    from models.card_club.economy import _tx, _move, HOLD_WALLET
    with _tx() as (conn, db_type):
        _move(conn, db_type, HOLD_WALLET, (group_id, user_id), amount,
              "bet_refund", ref_type="table", ref_id=table_id,
              note="stake refunded")


def start_table(group_id, user_id, table_id):
    groups.require_member(group_id, user_id)
    t = get_table(table_id)
    if not t or int(t["group_id"]) != group_id:
        raise NotFoundError("Table not found")
    if t["status"] != "waiting":
        raise CardClubError("Table already started")
    info = catalog_entry(t["game_slug"])
    seated = seats(table_id)
    n = len(seated)
    if n < info["min"] or n > info["max"] or n > int(t["max_seats"]):
        raise CardClubError(
            f"{info['name']} needs {info['min']}-{info['max']} players (seated: {n})")
    players = [int(s["user_id"]) for s in seated]
    state = info["cls"].create(players, seed=random.randrange(1 << 30))
    execute_update(
        """UPDATE club_tables SET status = 'active', state = %s,
           started_at = CURRENT_TIMESTAMP WHERE id = %s""",
        """UPDATE club_tables SET status = 'active', state = ?,
           started_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (json.dumps(state), table_id))
    execute_insert(
        "INSERT INTO club_moves (table_id, seq, user_id, move_json) VALUES (%s,%s,%s,%s)",
        "INSERT INTO club_moves (table_id, seq, user_id, move_json) VALUES (?,?,?,?)",
        (table_id, 0, user_id, json.dumps({"action": "start",
                                            "game": t["game_slug"]})))
    return get_table(table_id)


def seat_index_of(table_id, user_id):
    row = query_one(
        "SELECT seat_index FROM club_seats WHERE table_id = %s AND user_id = %s",
        "SELECT seat_index FROM club_seats WHERE table_id = ? AND user_id = ?",
        (table_id, user_id))
    return None if not row else int(row["seat_index"] if isinstance(row, dict) else row[0])


def _engine_for(t):
    info = catalog_entry(t["game_slug"])
    return info, info["cls"].from_state(_loads(t["state"]))


def get_view(table_id, user_id=None):
    t = get_table(table_id)
    if not t:
        raise NotFoundError("Table not found")
    seat = seat_index_of(table_id, user_id) if user_id else None
    all_seats = seats(table_id)
    seat_list = []
    my_rules_read = False
    my_camera_active = False
    for s in all_seats:
        s_uid = int(s["user_id"] if isinstance(s, dict) else s[1])
        r_read = bool(s.get("rules_read") if isinstance(s, dict) else s[4])
        c_act = bool(s.get("camera_active") if isinstance(s, dict) else s[5])
        if user_id and s_uid == int(user_id):
            my_rules_read = r_read
            my_camera_active = c_act
        disp_name = s.get("display_name") or s.get("username") if isinstance(s, dict) else s[6]
        seat_list.append({
            "seat_index": int(s["seat_index"] if isinstance(s, dict) else s[2]),
            "user_id": s_uid,
            "username": disp_name,
            "display_name": disp_name,
            "fake_name": s.get("fake_name") if isinstance(s, dict) else None,
            "rules_read": r_read,
            "camera_active": c_act,
        })
    table_keys = ("id", "group_id", "game_slug", "name", "stake",
                  "pool_bonus", "max_seats", "status", "created_by",
                  "is_private", "mode")
    view = {"table": {k: t[k] for k in table_keys if k in t},
            "seat": seat, "pot": table_pot(table_id),
            "seats": seat_list,
            "my_rules_read": my_rules_read,
            "my_camera_active": my_camera_active}
    if t["status"] == "active" and t["state"]:
        info, eng = _engine_for(t)
        view["game"] = eng.view(seat)
        view["game_name"] = info["name"]
        view["real_time"] = info["real_time"]
        if seat is not None:
            try:
                view["legal"] = eng.legal_actions(seat)
            except Exception:
                view["legal"] = []
        view["finish"] = eng.finish_order()
        view["scores"] = eng.scores()
    elif t["status"] == "waiting":
        info = catalog_entry(t["game_slug"])
        view["game_name"] = info["name"]
        view["min_players"] = info["min"]
        view["max_players"] = info["max"]
        view["rules"] = info["rules"]
    return view


def acknowledge_strict_rules(table_id, user_id):
    """Player marks that they have read and agreed to strict tournament rules.
    Required before camera sharing can be activated."""
    s = query_one(
        "SELECT id FROM club_seats WHERE table_id = %s AND user_id = %s",
        "SELECT id FROM club_seats WHERE table_id = ? AND user_id = ?",
        (table_id, user_id))
    if not s:
        raise PermissionDenied("You must take a seat at the table first.")
    execute_update(
        "UPDATE club_seats SET rules_read = 1 WHERE table_id = %s AND user_id = %s",
        "UPDATE club_seats SET rules_read = 1 WHERE table_id = ? AND user_id = ?",
        (table_id, user_id))
    return True


def toggle_camera(table_id, user_id, active):
    """Enables or disables camera stream on the player's seat pod.
    STRICT CHECK: Player MUST read and agree to strict tournament rules first!"""
    s = query_one(
        "SELECT id, rules_read FROM club_seats WHERE table_id = %s AND user_id = %s",
        "SELECT id, rules_read FROM club_seats WHERE table_id = ? AND user_id = ?",
        (table_id, user_id))
    if not s:
        raise PermissionDenied("You must take a seat at the table first.")
    rules_read = bool(s.get("rules_read") if isinstance(s, dict) else s[1])
    if not rules_read:
        raise CardClubError("Strict Rules must be read and acknowledged before camera sharing is unlocked.")
    val = 1 if active else 0
    execute_update(
        "UPDATE club_seats SET camera_active = %s WHERE table_id = %s AND user_id = %s",
        "UPDATE club_seats SET camera_active = ? WHERE table_id = ? AND user_id = ?",
        (val, table_id, user_id))
    return bool(val)



def perform_move(group_id, user_id, table_id, action):
    """Shared by HTTP route and the WebSocket handler."""
    groups.require_member(group_id, user_id)
    t = get_table(table_id)
    if not t or int(t["group_id"]) != group_id:
        raise NotFoundError("Table not found")
    if t["status"] != "active":
        raise CardClubError("Table is not in play")
    seat = seat_index_of(table_id, user_id)
    if seat is None:
        raise PermissionDenied("You are not seated at this table")
    srow = query_one(
        "SELECT id, rules_read FROM club_seats WHERE table_id = %s AND user_id = %s",
        "SELECT id, rules_read FROM club_seats WHERE table_id = ? AND user_id = ?",
        (table_id, user_id))
    rules_read = bool(srow.get("rules_read") if isinstance(srow, dict)
                      else (srow[1] if srow else False))
    if not rules_read:
        raise CardClubError("Strict Rules must be read and acknowledged "
                            "before you can play at this table.")
    info, eng = _engine_for(t)
    eng.apply(seat, action)
    seq = query_one(
        "SELECT COALESCE(MAX(seq),0) FROM club_moves WHERE table_id = %s",
        "SELECT COALESCE(MAX(seq),0) FROM club_moves WHERE table_id = ?",
        (table_id,))
    seq = int(seq[0] if not isinstance(seq, dict) else list(seq.values())[0]) + 1
    execute_update(
        "UPDATE club_tables SET state = %s WHERE id = %s",
        "UPDATE club_tables SET state = ? WHERE id = ?",
        (json.dumps(eng.state), table_id))
    execute_insert(
        "INSERT INTO club_moves (table_id, seq, user_id, move_json) VALUES (%s,%s,%s,%s)",
        "INSERT INTO club_moves (table_id, seq, user_id, move_json) VALUES (?,?,?,?)",
        (table_id, seq, user_id, json.dumps(action)))
    settlement = None
    if eng.is_over():
        settlement = _settle(t, eng)
    return {"view": get_view(table_id, user_id), "settlement": settlement}


def _settle(t, eng):
    """Winner-takes-all (or exact split on ties): payouts == pot + bonus."""
    table_id = int(t["id"])
    pot = table_pot(table_id)
    bonus = int(t["pool_bonus"] or 0)
    total = pot + bonus
    winners = eng.winners() if hasattr(eng, "winners") else None
    if not winners:
        finish = eng.finish_order()
        winners = finish[:1]
    seat_to_user = {int(s["seat_index"]): int(s["user_id"]) for s in seats(table_id)}
    payouts = {}
    if total > 0 and winners:
        base = total // len(winners)
        rem = total - base * len(winners)
        for i, w in enumerate(winners):
            uid = seat_to_user.get(w)
            if uid is None:
                continue
            payouts[uid] = base + (1 if i < rem else 0)
    result = economy.settle_zero_sum(table_id, payouts, bonus)
    result["winners"] = [seat_to_user.get(w) for w in winners]
    return result


def vacate_member_seats(group_id, user_id):
    """Member removal: refund/cancel every seat this user holds in the group."""
    rows = query_all(
        """SELECT s.id AS seat_id, t.id AS table_id, t.status AS tstatus
           FROM club_seats s JOIN club_tables t ON t.id = s.table_id
           WHERE t.group_id = %s AND s.user_id = %s""",
        """SELECT s.id AS seat_id, t.id AS table_id, t.status AS tstatus
           FROM club_seats s JOIN club_tables t ON t.id = s.table_id
           WHERE t.group_id = ? AND s.user_id = ?""",
        (group_id, user_id))
    for r in rows or []:
        d = dict(r) if isinstance(r, dict) else {}
        seat_id = int(d.get("seat_id") or r[0])
        tid = int(d.get("table_id") or r[1])
        status = d.get("tstatus") or r[2]
        if status == "waiting":
            try:
                leave_table(group_id, user_id, tid)
                continue
            except CardClubError:
                pass
        elif status == "active":
            _abandon_active(tid)
        execute_update("DELETE FROM club_seats WHERE id = %s",
                       "DELETE FROM club_seats WHERE id = ?", (seat_id,))


def _abandon_active(table_id):
    """Active seat vacated: whole table settles as abandoned - every escrowed
    stake returns (zero-sum preserved), pool obligations untouched."""
    economy.refund_bets_for_table(table_id)
    execute_update(
        "UPDATE club_tables SET status = 'abandoned', finished_at = CURRENT_TIMESTAMP WHERE id = %s",
        "UPDATE club_tables SET status = 'abandoned', finished_at = CURRENT_TIMESTAMP WHERE id = ?",
        (table_id,))


def cancel_waiting_table(group_id, user_id, table_id):
    groups.require_admin(group_id, user_id)
    t = get_table(table_id)
    if not t or int(t["group_id"]) != group_id:
        raise NotFoundError("Table not found")
    if t["status"] != "waiting":
        raise CardClubError("Only waiting tables can be cancelled")
    economy.refund_bets_for_table(table_id)
    execute_update("DELETE FROM club_seats WHERE table_id = %s",
                   "DELETE FROM club_seats WHERE table_id = ?", (table_id,))
    execute_update("DELETE FROM club_tables WHERE id = %s",
                   "DELETE FROM club_tables WHERE id = ?", (table_id,))
    return True
