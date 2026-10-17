"""Stakeless practice tables for the mobile app.

One row of ``club_practice_games`` holds one human-vs-bots deal of a Classic
Suite game.  The rules, the server-side legality gate and the bot heuristics
are exactly the ones the web arena uses (``models.card_club.engines``), so a
practice move can never differ from a money move:

* the state is written back after every human move, so the phone can resume
  the deal it left open;
* ``assert_legal`` runs before the engine ever sees the action - an
  out-of-turn or out-of-suit card is rejected with ``IllegalMove``;
* after the move ``step_ai_until_human`` plays the three bots out until the
  human is back on move or the deal is over.

Practice tables never touch the coin ledger.
"""

import json

from models.db import execute_insert, execute_update, query_all, query_one
from models.card_club.errors import (
    CardClubError, IllegalMove, NotFoundError, PermissionDenied,
)
from models.card_club.engines.classic_tricks import (
    CLASSIC_CATALOG, GAME_ENGINES, acting_seat, assert_legal,
    create_classic_game, get_game_view, seat_name, step_ai_until_human,
)

SLUGS = [entry["slug"] for entry in CLASSIC_CATALOG]
CATALOG = [
    {
        "slug": entry["slug"],
        "name": entry["name"],
        "players": "4 players",
        "deck_size": entry.get("deck_size"),
        "description": entry.get("desc", ""),
    }
    for entry in CLASSIC_CATALOG
]
MAX_SEATS = 4


def _dumps(obj):
    return json.dumps(obj, separators=(",", ":"))


def _loads(raw):
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _row_of(game_id):
    row = query_one(
        "SELECT * FROM club_practice_games WHERE id = %s",
        "SELECT * FROM club_practice_games WHERE id = ?", (int(game_id),))
    return dict(row) if row else None


def _require_owned(user_id, game_id):
    try:
        game_id = int(game_id)
    except (TypeError, ValueError):
        raise NotFoundError("Practice table not found")
    row = _row_of(game_id)
    if not row:
        raise NotFoundError("Practice table not found")
    if int(row["user_id"]) != int(user_id):
        raise PermissionDenied("This practice table belongs to another player")
    return row


def _seat_names(state, username):
    """Seat 0 is the human; the other three read as bots in every log line."""
    return [
        (username or "You") if i == 0 else f"{seat_name(state, i)} (AI)"
        for i in range(MAX_SEATS)
    ]


def _view(state, row, username=None):
    view = get_game_view(state, 0)
    view.update({
        "game_id": int(row["id"]),
        "kind": "practice",
        "slug": row["game_slug"],
        "status": row["status"],
        "created_at": str(row.get("created_at") or ""),
        "updated_at": str(row.get("updated_at") or ""),
    })
    view["is_my_turn"] = bool(view.get("legal_actions")) and not view.get("over")
    return view


# ------------------------------------------------------------------- lifecycle
def create_game(user_id, slug="29", username=None):
    """Deal a fresh stakeless table for this player against three bots."""
    slug = str(slug or "29").lower()
    if slug not in SLUGS:
        raise CardClubError(f"Unknown classic game '{slug}'")
    state = create_classic_game(slug)
    state["human_seats"] = [0]
    state["seat_names"] = _seat_names(state, username)
    state["log"].insert(
        0, "Practice deal: " + ", ".join(
            state["seat_names"][i] for i in range(MAX_SEATS)))
    state = step_ai_until_human(state)

    game_id = execute_insert(
        """INSERT INTO club_practice_games
           (user_id, game_slug, opponents, status, state)
           VALUES (%s, %s, %s, 'active', %s)""",
        """INSERT INTO club_practice_games
           (user_id, game_slug, opponents, status, state)
           VALUES (?, ?, ?, 'active', ?)""",
        (int(user_id), slug, MAX_SEATS - 1, _dumps(state)))
    row = _row_of(game_id)
    return _view(state, row, username)


def active_game(user_id):
    """The practice deal still open for this player (page/refresh restore)."""
    row = query_one(
        """SELECT * FROM club_practice_games
           WHERE user_id = %s AND status = 'active'
           ORDER BY id DESC LIMIT 1""",
        """SELECT * FROM club_practice_games
           WHERE user_id = ? AND status = 'active'
           ORDER BY id DESC LIMIT 1""",
        (int(user_id),))
    if not row:
        return None
    row = dict(row)
    state = _loads(row.get("state"))
    if not state:
        return None
    return _view(state, row)


def list_games(user_id, limit=20):
    rows = query_all(
        """SELECT id, game_slug, status, created_at, updated_at
             FROM club_practice_games
            WHERE user_id = %s
            ORDER BY id DESC LIMIT %s""",
        """SELECT id, game_slug, status, created_at, updated_at
             FROM club_practice_games
            WHERE user_id = ?
            ORDER BY id DESC LIMIT ?""",
        (int(user_id), int(limit)))
    return [{
        "game_id": int(r["id"] if isinstance(r, dict) else r[0]),
        "slug": r["game_slug"] if isinstance(r, dict) else r[1],
        "status": r["status"] if isinstance(r, dict) else r[2],
        "created_at": str(r["created_at"] if isinstance(r, dict) else r[3]),
        "updated_at": str(r["updated_at"] if isinstance(r, dict) else r[4]),
    } for r in rows or []]


def view_for(user_id, game_id):
    row = _require_owned(user_id, game_id)
    state = _loads(row.get("state"))
    if not state:
        raise CardClubError("This practice table has no deal in play")
    return _view(state, row)


def abandon(user_id, game_id):
    """Drop a practice deal without a result (it never held coins)."""
    _require_owned(user_id, game_id)
    execute_update(
        "UPDATE club_practice_games SET status = 'abandoned', "
        "updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        "UPDATE club_practice_games SET status = 'abandoned', "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (int(game_id),))
    return True


# ----------------------------------------------------------------------- moves
def apply_action(user_id, game_id, action, username=None):
    """Validate, apply, play the bots out, then return the fresh view."""
    row = _require_owned(user_id, game_id)
    if row["status"] != "active":
        raise CardClubError("This practice table is not in play")
    state = _loads(row.get("state"))
    if not state:
        raise CardClubError("This practice table has not been dealt yet")
    if state.get("over"):
        raise CardClubError("This deal is already finished")

    engine = GAME_ENGINES.get(state.get("slug", row["game_slug"]))
    if not engine:
        raise CardClubError(f"Unknown game '{state.get('slug')}'")
    if not isinstance(action, dict):
        raise IllegalMove("Action object required")

    move_seat = acting_seat(state, 0)
    assert_legal(engine, state, move_seat, action)     # rejects illegal posts
    engine.apply(state, move_seat, action)
    state = step_ai_until_human(state)

    status = "finished" if state.get("over") else "active"
    execute_update(
        "UPDATE club_practice_games SET state = %s, status = %s, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        "UPDATE club_practice_games SET state = ?, status = ?, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (_dumps(state), status, int(game_id)))

    fresh = _row_of(game_id)
    return _view(state, fresh, username)
