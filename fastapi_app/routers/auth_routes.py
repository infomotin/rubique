"""
CubePermutation AI - FastAPI Authentication Router
==================================================
Handles:
- Web-compatible login (validates credentials against MySQL, issues Flask session cookie)
- Registration (enforces username, password strength, and 18+ DOB age gate)
- Firebase Auth token verification & MySQL account linking
- Current session identity verification (/me)
- Session teardown (/logout)
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Response, Depends, HTTPException, status
from services.auth_service import AuthService
from models.user_model import UserModel
from fastapi_app.session_manager import encode_flask_cookie
from fastapi_app.firebase_auth import verify_firebase_id_token, map_firebase_user_to_mysql
from fastapi_app.dependencies import get_current_user

router = APIRouter(tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: Optional[str] = ""
    password: str
    confirm_password: str
    date_of_birth: str  # YYYY-MM-DD (18+ verification)


class FirebaseLoginRequest(BaseModel):
    id_token: str


def _clean_user_dict(user: dict) -> dict:
    """Strips internal password hash before sending to client"""
    return {
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
    }


@router.post("/api/v1/auth/login")
@router.post("/login")
async def login(req: LoginRequest, response: Response):
    """
    Authenticates username and password against MySQL user table.
    Issues a native signed Flask session cookie.
    """
    success, user, error_msg = AuthService.authenticate(req.username, req.password)
    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Invalid username or password."
        )

    # Encode Flask session cookie
    session_data = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user.get("role", "user")
    }
    cookie_str = encode_flask_cookie(session_data)

    response.set_cookie(
        key="session",
        value=cookie_str,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400
    )

    return {
        "success": True,
        "message": f"Welcome back, {user['username']}!",
        "session_cookie": cookie_str,
        "user": _clean_user_dict(user)
    }


@router.post("/api/v1/auth/register")
@router.post("/register")
async def register(req: RegisterRequest, response: Response):
    """
    Registers a new speedcubing account in MySQL with 18+ age verification.
    Issues a native signed Flask session cookie.
    """
    success, user_id, error_msg = AuthService.register(
        username=req.username,
        email=req.email or "",
        password=req.password,
        confirm_password=req.confirm_password,
        date_of_birth=req.date_of_birth
    )

    if not success or not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg or "Registration failed."
        )

    user = UserModel.find_by_id(user_id)
    session_data = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user.get("role", "user")
    }
    cookie_str = encode_flask_cookie(session_data)

    response.set_cookie(
        key="session",
        value=cookie_str,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400
    )

    return {
        "success": True,
        "message": "Account created successfully!",
        "session_cookie": cookie_str,
        "user": _clean_user_dict(user)
    }


@router.post("/api/v1/auth/firebase-login")
async def firebase_login(req: FirebaseLoginRequest, response: Response):
    """
    Verifies Firebase Auth token, resolves/maps identity to existing MySQL account,
    and returns a valid Flask session cookie.
    """
    valid, claims, error_msg = verify_firebase_id_token(req.id_token)
    if not valid or not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Invalid Firebase authentication token."
        )

    user = map_firebase_user_to_mysql(claims)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to map Firebase user onto MySQL user repository."
        )

    session_data = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user.get("role", "user")
    }
    cookie_str = encode_flask_cookie(session_data)

    response.set_cookie(
        key="session",
        value=cookie_str,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400
    )

    return {
        "success": True,
        "message": f"Authenticated via Firebase as {user['username']}",
        "session_cookie": cookie_str,
        "user": _clean_user_dict(user)
    }


@router.get("/api/v1/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Returns the authenticated user's profile information"""
    return {
        "success": True,
        "user": _clean_user_dict(user)
    }


@router.post("/api/v1/auth/logout")
@router.post("/logout")
async def logout(response: Response):
    """Teardown active session and clear cookie"""
    response.delete_cookie("session")
    return {
        "success": True,
        "message": "Successfully logged out."
    }
