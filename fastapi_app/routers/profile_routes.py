"""
CubePermutation AI - FastAPI Profile & Analytics Router
=======================================================
Handles user profile management, speedcubing stats calculation,
and historical solve management.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from models.user_model import UserModel
from models.solve_model import SolveModel
from models.db import query_one
from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/profile", tags=["User Profile"])


class ProfileUpdateRequest(BaseModel):
    bio: Optional[str] = ""
    avatar_color: Optional[str] = "#818cf8"
    wca_id: Optional[str] = ""
    country: Optional[str] = ""
    main_cube: Optional[str] = "GAN 12 MagLev 3x3"
    preferred_method: Optional[str] = "CFOP"
    pb_single: Optional[str] = ""
    pb_ao5: Optional[str] = ""


@router.get("")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Returns full profile information, solve statistics, and recent solve logs
    from the single source of truth (MySQL).
    """
    user_id = current_user["id"]
    user = UserModel.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    stats = SolveModel.get_user_stats(user_id)
    history = SolveModel.get_user_history(user_id, limit=20)

    # Wallet balance
    wallet_row = query_one(
        "SELECT balance FROM club_wallets WHERE user_id = %s",
        "SELECT balance FROM club_wallets WHERE user_id = ?",
        (user_id,)
    )
    coins_balance = int(wallet_row["balance"]) if wallet_row and wallet_row.get("balance") is not None else 1000

    clean_history = []
    for item in history:
        entry = dict(item)
        if "created_at" in entry and entry["created_at"]:
            entry["created_at"] = str(entry["created_at"])
        clean_history.append(entry)

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email") or "",
            "role": user.get("role", "user"),
            "bio": user.get("bio") or "",
            "avatar_color": user.get("avatar_color") or "#818cf8",
            "wca_id": user.get("wca_id") or "",
            "country": user.get("country") or "",
            "main_cube": user.get("main_cube") or "GAN 12 MagLev 3x3",
            "preferred_method": user.get("preferred_method") or "CFOP",
            "pb_single": user.get("pb_single") or "",
            "pb_ao5": user.get("pb_ao5") or "",
            "created_at": str(user.get("created_at") or "")
        },
        "stats": {
            "total_solves": stats.get("total_solves", 0),
            "min_moves": stats.get("min_moves", 0),
            "avg_moves": stats.get("avg_moves", 0.0)
        },
        "coins_balance": coins_balance,
        "recent_solves": clean_history
    }


@router.post("/update")
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Updates user credentials and speedcubing personal records in MySQL"""
    user_id = current_user["id"]
    UserModel.update_profile(
        user_id=user_id,
        bio=req.bio or "",
        avatar_color=req.avatar_color or "#818cf8",
        wca_id=req.wca_id or "",
        country=req.country or "",
        main_cube=req.main_cube or "GAN 12 MagLev 3x3",
        preferred_method=req.preferred_method or "CFOP",
        pb_single=req.pb_single or "",
        pb_ao5=req.pb_ao5 or ""
    )

    updated_user = UserModel.find_by_id(user_id)
    return {
        "success": True,
        "message": "Profile updated successfully.",
        "user": {
            "id": updated_user["id"],
            "username": updated_user["username"],
            "bio": updated_user.get("bio") or "",
            "avatar_color": updated_user.get("avatar_color") or "#818cf8",
            "wca_id": updated_user.get("wca_id") or "",
            "country": updated_user.get("country") or "",
            "main_cube": updated_user.get("main_cube") or "GAN 12 MagLev 3x3",
            "preferred_method": updated_user.get("preferred_method") or "CFOP",
            "pb_single": updated_user.get("pb_single") or "",
            "pb_ao5": updated_user.get("pb_ao5") or ""
        }
    }


@router.post("/clear-history")
async def clear_history(current_user: dict = Depends(get_current_user)):
    """Clears all solve history for the authenticated user"""
    SolveModel.clear_all(current_user["id"])
    return {
        "success": True,
        "message": "Solve history successfully cleared."
    }
