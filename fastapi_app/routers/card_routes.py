"""
Rubique - FastAPI Playing Card Router
=====================================
Mobile endpoints for the Classic Playing Card Suite:

* **Practice tables** - stakeless human-vs-3-bots deals stored in
  ``club_practice_games`` (``models.card_club.practice``). Every posted move
  goes through the same engine legality gate as the web arena.
* **Classic money tables** - the shared tables in ``models.classic_arena``:
  coin stake escrow, group lobbies, bots filling empty seats and a single
  zero-sum settlement pushed onto the hash-chained ledger when the deal ends.
* **Wallet / ledger reads** - balances plus the player's own hash-chained
  transaction history so the app can show its coin book.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from models import classic_arena as arena
from models.card_club import economy, practice
from models.card_club.errors import (
    CardClubError, NotFoundError, PermissionDenied,
)
from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/cards", tags=["Playing Cards"])


# --------------------------------------------------------------------- errors
def _http(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionDenied):
        code = 403
    elif isinstance(exc, NotFoundError):
        code = 404
    elif isinstance(exc, CardClubError):
        code = 400
    else:
        code = 400
    return HTTPException(status_code=code, detail=str(exc))


# ------------------------------------------------------------------- payloads
class PracticeCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    slug: str = "29"


class ActionRequest(BaseModel):
    """Any engine action - extra keys (level, amount, ...) pass straight
    through to the engine's own legal-action comparison."""
    model_config = ConfigDict(extra="allow")
    action: str
    card: Optional[str] = None
    suit: Optional[str] = None
    value: Optional[int] = None
    level: Optional[int] = None

    def as_action(self) -> dict:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class ClassicCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    slug: str = "29"
    mode: str = "ai"
    group_id: int = 0
    stake: int = 0


# ------------------------------------------------------------------ catalogue
@router.get("/catalog")
async def card_catalog():
    """Every game the mobile app can start, classic suite first."""
    from models.card_club.engines import CATALOG as CLUB_CATALOG
    club = []
    for slug, info in sorted(CLUB_CATALOG.items()):
        club.append({
            "slug": slug,
            "name": info.get("name", slug),
            "min": info.get("min"),
            "max": info.get("max"),
            "category": info.get("category", ""),
            "modes": list(info.get("modes", []) or []),
        })
    return {
        "success": True,
        "classic": practice.CATALOG,
        "club": club,
        "starting_grant": economy.STARTING_GRANT,
        "bet_limit": economy.MAX_BET_LIMIT,
    }


# --------------------------------------------------------------------- wallet
@router.get("/wallet")
async def wallet(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    balances = economy.balances_view(uid)
    return {
        "success": True,
        "balances": balances,
        "personal": int(balances.get("personal", 0)),
        "reserve": int(balances.get("reserve", 0)),
        "ledger": economy.ledger_for_user(uid, 0, 25),
    }


@router.get("/ledger")
async def ledger(limit: int = 30, current_user: dict = Depends(get_current_user)):
    """The player's own hash-chained coin entries, newest first."""
    return {
        "success": True,
        "entries": economy.ledger_for_user(current_user["id"], 0, limit),
    }


# ------------------------------------------------------------------- practice
@router.get("/practice")
async def practice_games(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    return {
        "success": True,
        "active": practice.active_game(uid),
        "games": practice.list_games(uid),
    }


@router.get("/practice/active")
async def practice_active(current_user: dict = Depends(get_current_user)):
    state = practice.active_game(current_user["id"])
    return {"success": True, "state": state}


@router.post("/practice")
async def practice_start(body: PracticeCreate,
                         current_user: dict = Depends(get_current_user)):
    try:
        state = practice.create_game(
            current_user["id"], body.slug,
            username=current_user.get("username"))
        return {"success": True, "state": state}
    except CardClubError as e:
        raise _http(e) from e


@router.get("/practice/{game_id}")
async def practice_state(game_id: int,
                         current_user: dict = Depends(get_current_user)):
    try:
        return {"success": True, "state": practice.view_for(
            current_user["id"], game_id)}
    except CardClubError as e:
        raise _http(e) from e


@router.post("/practice/{game_id}/action")
async def practice_move(game_id: int, body: ActionRequest,
                        current_user: dict = Depends(get_current_user)):
    try:
        state = practice.apply_action(
            current_user["id"], game_id, body.as_action(),
            username=current_user.get("username"))
        return {"success": True, "state": state}
    except CardClubError as e:
        raise _http(e) from e


@router.delete("/practice/{game_id}")
async def practice_abandon(game_id: int,
                           current_user: dict = Depends(get_current_user)):
    try:
        practice.abandon(current_user["id"], game_id)
        return {"success": True}
    except CardClubError as e:
        raise _http(e) from e


# ------------------------------------------------------------- classic tables
@router.get("/classic/active")
async def classic_active(current_user: dict = Depends(get_current_user)):
    game = arena.active_game_for(current_user["id"])
    if not game:
        return {"success": True, "state": None}
    return {"success": True, "game_id": int(game["id"]),
            "state": arena.view_for(int(game["id"]), current_user["id"])}


@router.get("/classic/tables")
async def classic_tables(group_id: int = 0,
                         current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    if group_id:
        try:
            from models.card_club import groups
            groups.require_member(group_id, uid)
        except CardClubError as e:
            raise _http(e) from e
    return {"success": True, "group_id": group_id,
            "tables": arena.list_group_games(group_id)}


@router.post("/classic")
async def classic_create(body: ClassicCreate,
                         current_user: dict = Depends(get_current_user)):
    try:
        game = arena.create_game(
            current_user["id"], body.slug, mode=body.mode,
            group_id=body.group_id, stake=body.stake)
        return {"success": True, "game_id": int(game["id"]),
                "state": arena.view_for(int(game["id"]), current_user["id"])}
    except CardClubError as e:
        raise _http(e) from e


@router.get("/classic/{game_id}")
async def classic_state(game_id: int,
                        current_user: dict = Depends(get_current_user)):
    game = arena.active_game_for(current_user["id"], game_id)
    if not game:
        raise HTTPException(status_code=404, detail="No classic table in play")
    return {"success": True, "game_id": int(game["id"]),
            "state": arena.view_for(int(game["id"]), current_user["id"])}


@router.post("/classic/{game_id}/join")
async def classic_join(game_id: int,
                       current_user: dict = Depends(get_current_user)):
    try:
        arena.join_game(current_user["id"], game_id)
        return {"success": True, "game_id": int(game_id),
                "state": arena.view_for(int(game_id), current_user["id"])}
    except CardClubError as e:
        raise _http(e) from e


@router.post("/classic/{game_id}/start")
async def classic_start(game_id: int,
                        current_user: dict = Depends(get_current_user)):
    try:
        arena.start_game(current_user["id"], game_id)
        return {"success": True, "game_id": int(game_id),
                "state": arena.view_for(int(game_id), current_user["id"])}
    except CardClubError as e:
        raise _http(e) from e


@router.post("/classic/{game_id}/leave")
async def classic_leave(game_id: int,
                        current_user: dict = Depends(get_current_user)):
    try:
        arena.leave_game(current_user["id"], game_id)
        return {"success": True}
    except CardClubError as e:
        raise _http(e) from e


@router.post("/classic/{game_id}/cancel")
async def classic_cancel(game_id: int,
                         current_user: dict = Depends(get_current_user)):
    try:
        arena.cancel_game(current_user["id"], game_id)
        return {"success": True}
    except CardClubError as e:
        raise _http(e) from e


@router.post("/classic/{game_id}/action")
async def classic_move(game_id: int, body: ActionRequest,
                       current_user: dict = Depends(get_current_user)):
    """Validated move - illegal or out-of-turn posts never reach the engine."""
    try:
        view, settlement = arena.apply_action(
            int(game_id), current_user["id"], body.as_action())
        return {"success": True, "state": view, "settlement": settlement}
    except CardClubError as e:
        raise _http(e) from e
