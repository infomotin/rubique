"""
CubePermutation AI - Firebase Authentication Bridge
===================================================
Verifies Firebase Auth tokens and maps Firebase identities onto the existing
MySQL user table. Prevents competing user stores by ensuring the MySQL
database remains the sole source of truth.
"""

import os
import re
import secrets
from typing import Dict, Any, Optional, Tuple
import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from models.user_model import UserModel
from models.db import query_one, execute_insert
from config import Config

# Initialize Firebase Admin SDK if credentials provided or default app
_FIREBASE_INITIALIZED = False

def init_firebase_admin():
    global _FIREBASE_INITIALIZED
    if _FIREBASE_INITIALIZED or len(firebase_admin._apps) > 0:
        _FIREBASE_INITIALIZED = True
        return True

    cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    try:
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _FIREBASE_INITIALIZED = True
            return True
        else:
            # Try default initialization (e.g. standard GCP env or dummy for dev)
            firebase_admin.initialize_app()
            _FIREBASE_INITIALIZED = True
            return True
    except Exception:
        # Development mode fallback: will use dev token decoding
        return False


def verify_firebase_id_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Verifies a Firebase ID token.

    Production: firebase_admin.auth.verify_id_token (signature, audience,
    expiry) - nothing else is ever accepted.
    Development/testing: literal ``test_token_``/``mock_token_`` shortcuts are
    tolerated, but only outside production (ALLOW_DEV_AUTH_TOKENS=0/1 to
    override) and never for the unsigned-JWT payload trick this function used
    to allow (a 3-part JWT with no signature check = full auth bypass).
    """
    if not token or not isinstance(token, str):
        return False, None, "Missing or invalid token string."

    # 1. Development & testing shortcut (unsigned test tokens).
    allow_dev = os.environ.get("ALLOW_DEV_AUTH_TOKENS")
    if allow_dev is not None:
        dev_tokens_ok = allow_dev.lower() in ("1", "true", "yes")
    else:
        dev_tokens_ok = Config.FLASK_ENV in ("development", "testing")

    if dev_tokens_ok and (token.startswith("test_token_") or token.startswith("mock_token_")):
        parts = token.split(":")
        email = parts[1] if len(parts) > 1 else "test_cuber@example.com"
        username = email.split("@")[0]
        claims = {
            "uid": f"uid_{username}",
            "email": email,
            "name": username.title(),
            "email_verified": True
        }
        return True, claims, None

    # 2. Real tokens: strict Firebase Admin verification (fail closed).
    init_firebase_admin()
    if _FIREBASE_INITIALIZED:
        try:
            decoded_claims = fb_auth.verify_id_token(token)
            return True, decoded_claims, None
        except Exception:
            return False, None, "Invalid Firebase authentication token."

    # 3. No verifier configured and not a dev token: refuse.
    return False, None, "Invalid Firebase authentication token."


def map_firebase_user_to_mysql(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps Firebase token claims onto the existing MySQL user table.
    Ensures single source of truth:
    1. Looks up existing user by email
    2. If found, returns existing user
    3. If not found, provisions new user in MySQL with random secure password hash
    """
    email = claims.get("email") or ""
    uid = claims.get("uid") or claims.get("sub") or ""
    display_name = claims.get("name") or claims.get("display_name") or ""

    user = None
    if email:
        user = query_one(
            "SELECT * FROM users WHERE email = %s LIMIT 1",
            "SELECT * FROM users WHERE email = ? LIMIT 1",
            (email,)
        )

    if not user and uid:
        # Check by username if uid used
        user = UserModel.find_by_username(f"fb_{uid[:8]}")

    if not user:
        # Create user in MySQL
        base_name = display_name if display_name else (email.split("@")[0] if email else f"cuber_{uid[:6]}")
        # Sanitize username
        safe_username = re.sub(r'[^a-zA-Z0-9_]', '', base_name)[:20]
        if not safe_username:
            safe_username = f"cuber_{secrets.token_hex(4)}"

        # Ensure uniqueness
        original_uname = safe_username
        counter = 1
        while UserModel.find_by_username(safe_username):
            safe_username = f"{original_uname[:15]}_{counter}"
            counter += 1

        random_pw = secrets.token_urlsafe(16)
        user_id = UserModel.create_user(
            username=safe_username,
            email=email,
            password=random_pw,
            bio="Registered via Firebase Mobile Auth",
            avatar_color="#38bdf8"
        )
        user = UserModel.find_by_id(user_id)

    return user
