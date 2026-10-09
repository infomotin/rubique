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
    return query_all(
        """SELECT s.id, s.user_id, s.seat_index, s.status, u.username
           FROM club_seats s JOIN users u ON u.id = s.user_id
           WHERE s.table_id = %s ORDER BY s.seat_index ASC""",
        """SELECT s.id, s.user_id, s.seat_index, s.status, u.username
           FROM club_seats s JOIN users u ON u.id = s.user_id
           WHERE s.table_id = ? ORDER BY s.seat_index ASC""",
        (table_id,))


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


def create_table(group_id, user_id, slug, stake=0, pool_bonus=0, name=""):
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
    tid = execute_insert(
        """INSERT INTO club_tables
           (group_id, game_slug, name, stake, pool_bonus, max_seats, created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        """INSERT INTO club_tables
           (group_id, game_slug, name, stake, pool_bonus, max_seats, created_by)
           VALUES (?,?,?,?,?,?,?)""",
        (group_id, slug, name or info["name"], stake, pool_bonus,
         info["max"], user_id))
    join_table(group_id, user_id, tid)          # creator sits first
    return get_table(tid)


def join_table(group_id, user_id, table_id):
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
    if len(seated) + 1 > int(t["max_seats"]):
        raise CardClubError("Table is full")
    if len(seated) + 1 < info["min"]:
        pass                                  # allowed: table waits for more
    stake = int(t["stake"] or 0)
    bet_id = economy.place_bet(table_id, group_id, user_id, stake)
    next_idx = max([int(s["seat_index"]) for s in seated] or [-1]) + 1
    try:
        execute_insert(
            "INSERT INTO club_seats (table_id, user_id, seat_index) VALUES (%s,%s,%s)",
            "INSERT INTO club_seats (table_id, user_id, seat_index) VALUES (?,?,?)",
            (table_id, user_id, next_idx))
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
    view = {"table": {k: t[k] for k in
                      ("id", "group_id", "game_slug", "name", "stake",
                       "pool_bonus", "max_seats", "status", "created_by")},
            "seat": seat, "pot": table_pot(table_id),
            "seats": [{"seat_index": int(s["seat_index"]),
                       "user_id": int(s["user_id"]),
                       "username": s["username"]} for s in seats(table_id)]}
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
