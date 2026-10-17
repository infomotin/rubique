"""Classic Playing Cards Suite - server-side game store.

`/cards/classic` used to keep its whole game inside the Flask session cookie,
trusted whatever the browser posted and never touched the coin economy. This
module is the authoritative store instead:

* every game lives in ``classic_games`` with its seat map in ``classic_seats``
  so a group of humans (plus bots in the empty seats) can share one table;
* every move is validated against the engine's own ``legal_actions()`` before
  it is applied, so a client can never post an out-of-turn or out-of-suit card;
* every stake is escrowed from the player's personal wallet and, on the final
  whistle, the whole pot is pushed back out in one zero-sum ``settle_classic``
  call - which appends a hash-chained entry to the Card Club ledger, so classic
  wins and losses are auditable by ``economy.verify_ledger()``.
"""

import json

from models.db import execute_insert, execute_update, query_all, query_one
from models.card_club import bots as bot_identity
from models.card_club import economy, groups
from models.card_club.errors import (
    CardClubError, IllegalMove, NotFoundError, PermissionDenied,
)
from models.card_club.engines.classic_tricks import (
    CLASSIC_CATALOG, GAME_ENGINES, SEAT_ROLES, acting_seat, assert_legal,
    create_classic_game, get_game_view, human_seats, seat_name,
    step_ai_until_human,
)

MAX_SEATS = 4
ECON_GROUP = 0                     # classic stakes use personal wallets
SLUGS = [entry["slug"] for entry in CLASSIC_CATALOG]
BOT_SLOTS = [0, 1, 2, 3]           # stable bot identity per seat


def _loads(raw):
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _dumps(obj):
    return json.dumps(obj)


# ---------------------------------------------------------------- store lookups
def get_game(game_id):
    return query_one("SELECT * FROM classic_games WHERE id = %s",
                     "SELECT * FROM classic_games WHERE id = ?", (game_id,))


def game_seats(game_id):
    rows = query_all(
        """SELECT seat_index, user_id, is_bot, display_name
           FROM classic_seats WHERE game_id = %s ORDER BY seat_index ASC""",
        """SELECT seat_index, user_id, is_bot, display_name
           FROM classic_seats WHERE game_id = ? ORDER BY seat_index ASC""",
        (game_id,))
    out = []
    for r in rows or []:
        d = dict(r) if isinstance(r, dict) else {
            "seat_index": r[0], "user_id": r[1], "is_bot": r[2],
            "display_name": r[3]}
        out.append({
            "seat_index": int(d["seat_index"]),
            "user_id": int(d["user_id"]) if d.get("user_id") is not None else None,
            "is_bot": bool(d.get("is_bot")),
            "display_name": d.get("display_name") or "",
        })
    return out


def seat_index_of(game_id, user_id):
    row = query_one(
        "SELECT seat_index FROM classic_seats WHERE game_id = %s AND user_id = %s",
        "SELECT seat_index FROM classic_seats WHERE game_id = ? AND user_id = ?",
        (game_id, user_id))
    if not row:
        return None
    return int(row["seat_index"] if isinstance(row, dict) else row[0])


def _require(game_id):
    game = get_game(game_id)
    if not game:
        raise NotFoundError("Classic table not found")
    return game


def _username(user_id):
    row = query_one("SELECT username FROM users WHERE id = %s",
                    "SELECT username FROM users WHERE id = ?", (user_id,))
    if not row:
        return f"Player {user_id}"
    return row["username"] if isinstance(row, dict) else row[0]


def _seat(game_id, index, user_id, is_bot, display_name):
    execute_insert(
        """INSERT INTO classic_seats
           (game_id, seat_index, user_id, is_bot, display_name)
           VALUES (%s,%s,%s,%s,%s)""",
        """INSERT INTO classic_seats
           (game_id, seat_index, user_id, is_bot, display_name)
           VALUES (?,?,?,?,?)""",
        (game_id, index, user_id, 1 if is_bot else 0, display_name))


# ---------------------------------------------------------------- create / join
def create_game(user_id, slug, mode="ai", group_id=0, stake=0, start=None):
    """Open a classic table.

    ``mode='ai'``  - solo seat against three bots, dealt straight away.
    ``mode='group'`` - lobby table other group members join before it starts.
    """
    if slug not in SLUGS:
        raise CardClubError(f"Unknown classic game '{slug}'")
    mode = "group" if str(mode).lower() == "group" else "ai"
    group_id = int(group_id or 0)
    stake = int(stake or 0)
    if stake < 0 or stake > economy.MAX_BET_LIMIT:
        raise CardClubError(
            f"Stake must be between 0 and {economy.MAX_BET_LIMIT}")
    if group_id:
        groups.require_member(group_id, user_id)
    if stake > 0 and economy.balances_view(user_id)["personal"] < stake:
        raise CardClubError(
            "Coins finished! You do not have enough coins for this stake.")

    game_id = execute_insert(
        """INSERT INTO classic_games
           (slug, mode, group_id, owner_id, stake, status)
           VALUES (%s,%s,%s,%s,%s,'waiting')""",
        """INSERT INTO classic_games
           (slug, mode, group_id, owner_id, stake, status)
           VALUES (?,?,?,?,?,'waiting')""",
        (slug, mode, group_id, int(user_id), stake))
    game_id = int(game_id)
    _seat(game_id, 0, int(user_id), 0, _username(user_id))
    economy.place_classic_stake(game_id, user_id, stake, ECON_GROUP)

    if start is None:
        start = (mode == "ai")
    if start:
        return start_game(user_id, game_id)
    return get_game(game_id)


def join_game(user_id, game_id):
    """Take the next free seat at a waiting group table."""
    game = _require(game_id)
    if game["status"] != "waiting":
        raise CardClubError("This table has already started")
    if game["mode"] != "group":
        raise CardClubError("This table is solo play against the house bots")
    group_id = int(game["group_id"] or 0)
    if group_id:
        groups.require_member(group_id, user_id)
    seats = game_seats(game_id)
    if any(int(s["user_id"] or 0) == int(user_id) for s in seats):
        raise CardClubError("You are already seated at this table")
    taken = {int(s["seat_index"]) for s in seats}
    free = [i for i in range(MAX_SEATS) if i not in taken]
    if not free:
        raise CardClubError("This table is full")
    stake = int(game["stake"] or 0)
    if stake > 0 and economy.balances_view(user_id)["personal"] < stake:
        raise CardClubError(
            "Coins finished! You do not have enough coins to join this table.")
    index = free[0]
    _seat(game_id, index, int(user_id), 0, _username(user_id))
    economy.place_classic_stake(game_id, user_id, stake, ECON_GROUP)
    return index


def leave_game(user_id, game_id):
    """Leave a table that has not started yet; the stake is refunded."""
    game = _require(game_id)
    if game["status"] != "waiting":
        raise CardClubError("Cannot leave once the deal has started")
    index = seat_index_of(game_id, user_id)
    if index is None:
        raise CardClubError("You are not seated at this table")
    if int(game["owner_id"]) == int(user_id) and index == 0:
        raise CardClubError("The table owner cannot leave - cancel the table")
    economy.refund_classic_stakes(game_id, ECON_GROUP, user_id)
    execute_update(
        "DELETE FROM classic_seats WHERE game_id = %s AND user_id = %s",
        "DELETE FROM classic_seats WHERE game_id = ? AND user_id = ?",
        (game_id, user_id))
    return True


def cancel_game(user_id, game_id):
    """Owner cancels a waiting table; every escrowed stake is returned."""
    game = _require(game_id)
    if int(game["owner_id"]) != int(user_id):
        raise PermissionDenied("Only the table owner can cancel this table")
    if game["status"] != "waiting":
        raise CardClubError("Only a waiting table can be cancelled")
    economy.refund_classic_stakes(game_id, ECON_GROUP)
    execute_update("DELETE FROM classic_seats WHERE game_id = %s",
                   "DELETE FROM classic_seats WHERE game_id = ?", (game_id,))
    execute_update("UPDATE classic_games SET status = 'cancelled', "
                   "finished_at = CURRENT_TIMESTAMP WHERE id = %s",
                   "UPDATE classic_games SET status = 'cancelled', "
                   "finished_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (game_id,))
    return True


def list_group_games(group_id, include_finished=False):
    """Lobby feed: tables a group can still sit down at."""
    sql_m = "SELECT * FROM classic_games WHERE group_id = %s"
    sql_s = "SELECT * FROM classic_games WHERE group_id = ?"
    if not include_finished:
        sql_m += " AND status NOT IN ('finished','cancelled')"
        sql_s += " AND status NOT IN ('finished','cancelled')"
    rows = query_all(sql_m + " ORDER BY id DESC",
                     sql_s + " ORDER BY id DESC", (group_id,))
    out = []
    for row in rows or []:
        d = dict(row) if isinstance(row, dict) else {}
        seats = game_seats(d.get("id"))
        out.append({
            "id": int(d.get("id")),
            "slug": d.get("slug"),
            "name": _slug_title(d.get("slug")),
            "mode": d.get("mode"),
            "status": d.get("status"),
            "owner_id": int(d.get("owner_id") or 0),
            "stake": int(d.get("stake") or 0),
            "seated": len(seats),
            "max_seats": MAX_SEATS,
            "players": [s["display_name"] for s in seats],
            "seats": seats,
        })
    return out


def _slug_title(slug):
    for entry in CLASSIC_CATALOG:
        if entry["slug"] == slug:
            return entry["name"]
    return slug


# ------------------------------------------------------------------ start / AI
def start_game(user_id, game_id):
    """Fill every empty seat with a bot, deal, then play the bots out until a
    human seat is on move."""
    game = _require(game_id)
    if game["status"] != "waiting":
        raise CardClubError("This table has already started")
    group_id = int(game["group_id"] or 0)
    if group_id:
        groups.require_member(group_id, user_id)
    stake = int(game["stake"] or 0)

    occupied = {int(s["seat_index"]) for s in game_seats(game_id)}
    for index in range(MAX_SEATS):
        if index in occupied:
            continue
        bot_uid, bot_name = bot_identity.ensure_bot(
            BOT_SLOTS[index % len(BOT_SLOTS)])
        _seat(game_id, index, bot_uid, 1, f"{bot_name} (Bot)")
        if stake > 0 and economy.balances_view(bot_uid)["personal"] < stake:
            economy.replenish_wallet(bot_uid, stake)
        economy.place_classic_stake(game_id, bot_uid, stake, ECON_GROUP)

    seats = {int(s["seat_index"]): s for s in game_seats(game_id)}
    humans = sorted(i for i in range(MAX_SEATS) if not seats[i]["is_bot"])
    if not humans:
        raise CardClubError("At least one human player must be seated")

    state = create_classic_game(game["slug"])
    state["human_seats"] = humans
    state["seat_names"] = [
        seats[i]["display_name"] or seat_name(state, i) for i in range(MAX_SEATS)
    ]
    state["log"].insert(
        0, "Table seated: " + ", ".join(
            f"{SEAT_ROLES[i]} = {state['seat_names'][i]}" for i in range(MAX_SEATS)))
    state = step_ai_until_human(state)

    execute_update(
        "UPDATE classic_games SET status = 'active', state = %s, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        "UPDATE classic_games SET status = 'active', state = ?, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (_dumps(state), game_id))
    if state.get("over"):
        settle(game_id)
    return get_game(game_id)


def active_game_for(user_id, game_id=None):
    """Most recent classic table this player is seated at (for page restore)."""
    if game_id:
        game = get_game(game_id)
        if game and seat_index_of(game["id"], user_id) is not None:
            return game
        return None
    row = query_one(
        """SELECT cg.* FROM classic_games cg
           JOIN classic_seats cs ON cs.game_id = cg.id
           WHERE cs.user_id = %s AND cg.status IN ('active','waiting')
           ORDER BY cg.id DESC LIMIT 1""",
        """SELECT cg.* FROM classic_games cg
           JOIN classic_seats cs ON cs.game_id = cg.id
           WHERE cs.user_id = ? AND cg.status IN ('active','waiting')
           ORDER BY cg.id DESC LIMIT 1""",
        (user_id,))
    if row:
        return dict(row) if isinstance(row, dict) else row
    return None


# ---------------------------------------------------------------------- moves
def apply_action(game_id, user_id, action):
    """Validate, apply, let the bots answer, then settle if the game ended."""
    game = _require(game_id)
    if game["status"] != "active":
        raise CardClubError("This table is not in play")
    state = _loads(game.get("state"))
    if not state:
        raise CardClubError("This table has not been dealt yet")
    index = seat_index_of(game_id, user_id)
    if index is None:
        raise PermissionDenied("You are not seated at this table")
    if not isinstance(action, dict):
        raise IllegalMove("Action object required")

    slug = state.get("slug", game["slug"])
    engine = GAME_ENGINES.get(slug)
    if not engine:
        raise CardClubError(f"Unknown game '{slug}'")

    move_seat = acting_seat(state, index)           # declarer drives dummy
    assert_legal(engine, state, move_seat, action)  # rejects illegal posts
    engine.apply(state, move_seat, action)
    state = step_ai_until_human(state)

    execute_update(
        "UPDATE classic_games SET state = %s, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s",
        "UPDATE classic_games SET state = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (_dumps(state), game_id))

    settlement = settle(game_id) if state.get("over") else None
    return view_for(game_id, user_id), settlement


def save_state(game_id, state):
    execute_update(
        "UPDATE classic_games SET state = %s, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s",
        "UPDATE classic_games SET state = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (_dumps(state), game_id))


# ------------------------------------------------------------------ settlement
def winner_seats(state):
    """Which seats take the pot when the engine calls the game."""
    if state.get("winner") is not None:
        try:
            return [int(state["winner"])]
        except (TypeError, ValueError):
            return []
    team = state.get("winner_team")
    if team == "team0":
        return [0, 2]
    if team == "team1":
        return [1, 3]
    return []


def settle(game_id):
    """Push the whole escrowed pot to the winning side, in one zero-sum
    transaction that is hash-chained onto the coin ledger."""
    game = _require(game_id)
    if game["status"] in ("finished", "cancelled"):
        return _result(game)
    state = _loads(game.get("state"))
    stakes = economy.classic_stakes(game_id, "escrowed")
    pot = sum(int(s["amount"]) for s in stakes)
    seats = {int(s["seat_index"]): s for s in game_seats(game_id)}
    winners = winner_seats(state or {}) if state else []
    winners = [w for w in winners
               if w in seats and seats[w]["user_id"] is not None]

    if pot > 0 and winners:
        share = pot // len(winners)
        remainder = pot - share * len(winners)
        payouts = {}
        for i, w in enumerate(winners):
            uid = int(seats[w]["user_id"])
            payouts[uid] = payouts.get(uid, 0) + share + (1 if i < remainder else 0)
        economy.settle_classic(game_id, payouts, ECON_GROUP)
        result = {
            "kind": "settlement",
            "pot": pot,
            "payouts": payouts,
            "winners": winners,
            "winner_names": [seats[w]["display_name"] for w in winners],
        }
    else:
        economy.refund_classic_stakes(game_id, ECON_GROUP)
        result = {"kind": "refund", "pot": pot, "payouts": {},
                  "winners": [], "winner_names": []}

    execute_update(
        "UPDATE classic_games SET status = 'finished', result = %s, "
        "finished_at = CURRENT_TIMESTAMP WHERE id = %s",
        "UPDATE classic_games SET status = 'finished', result = ?, "
        "finished_at = CURRENT_TIMESTAMP WHERE id = ?",
        (_dumps(result), game_id))
    return result


def _result(game):
    if isinstance(game.get("result"), dict):
        return game["result"]
    return _loads(game.get("result")) or {}


# ----------------------------------------------------------------------- views
def view_for(game_id, user_id=None):
    game = _require(game_id)
    seat = seat_index_of(game_id, user_id) if user_id else None
    seats = game_seats(game_id)
    stakes = economy.classic_stakes(game_id, "escrowed")
    meta = {
        "game_id": int(game["id"]),
        "mode": game["mode"],
        "group_id": int(game["group_id"] or 0),
        "owner_id": int(game["owner_id"] or 0),
        "status": game["status"],
        "stake": int(game["stake"] or 0),
        "pot": sum(int(s["amount"]) for s in stakes),
        "players": [{
            "seat": s["seat_index"],
            "user_id": s["user_id"],
            "name": s["display_name"] or seat_name({}, s["seat_index"]),
            "is_me": user_id is not None and s["user_id"] == int(user_id),
            "is_bot": s["is_bot"],
        } for s in seats],
        "settlement": _result(game) if game["status"] in (
            "finished", "cancelled") else None,
    }

    state = _loads(game.get("state"))
    if state and game["status"] in ("active", "finished"):
        view = get_game_view(state, seat if seat is not None else 0)
        view.update(meta)
        view["is_my_turn"] = bool(view["legal_actions"]) and not view["over"]
        return view

    taken = {int(s["seat_index"]): s for s in seats}
    meta.update({
        "slug": game["slug"], "title": _slug_title(game["slug"]),
        "description": "", "phase": "waiting", "over": False,
        "my_seat": seat, "legal_actions": [], "counts": {}, "hand": [],
        "log": ["Waiting for players - press Start when the table is full."],
        "seat_labels": [
            (taken[i]["display_name"] if i in taken else None)
            or seat_name({}, i)
            for i in range(MAX_SEATS)],
        "is_my_turn": False,
    })
    return meta


def seats_name(entry):
    return entry.get("display_name") or seat_name({}, entry["seat_index"])


# ------------------------------------------------------------------ guardrails
def ensure_logged_in(user_id):
    if not user_id:
        raise PermissionDenied("Login required to play the Classic Suite")
    return user_id
