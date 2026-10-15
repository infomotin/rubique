"""
CubePermutation AI - FastAPI Authentication Dependencies
========================================================
Authenticates requests using either:
1. Flask Session Cookie (via standard 'session' cookie or 'X-Session-Cookie' header)
2. Firebase ID Token (via 'Authorization: Bearer <token>' header)

Validates the identity against the single source of truth: the MySQL users table.
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from models.user_model import UserModel
from fastapi_app.session_manager import decode_flask_cookie
from fastapi_app.firebase_auth import verify_firebase_id_token, map_firebase_user_to_mysql


async def get_optional_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract and validate the authenticated user from:
    - Flask session cookie (request.cookies['session'])
    - Custom header (request.headers['X-Session-Cookie'])
    - Bearer token (request.headers['Authorization'])
    Returns MySQL user record or None.
    """
    # 1. Check Flask session cookie
    cookie_str = request.cookies.get("session") or request.headers.get("X-Session-Cookie")
    if cookie_str:
        session_data = decode_flask_cookie(cookie_str)
        if session_data and "user_id" in session_data:
            user = UserModel.find_by_id(session_data["user_id"])
            if user:
                return user

    # 2. Check Authorization Header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        # A. Try as Flask session cookie passed in Bearer
        session_data = decode_flask_cookie(token)
        if session_data and "user_id" in session_data:
            user = UserModel.find_by_id(session_data["user_id"])
            if user:
                return user

        # B. Try as Firebase ID Token
        is_fb, claims, _err = verify_firebase_id_token(token)
        if is_fb and claims:
            user = map_firebase_user_to_mysql(claims)
            if user:
                return user

    return None


async def get_current_user(user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)) -> Dict[str, Any]:
    """
    Guarantees the request has a valid authenticated user.
    Raises 401 Unauthorized if missing or invalid.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Flask session cookie or Firebase token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
