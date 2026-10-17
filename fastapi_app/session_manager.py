"""
CubePermutation AI - FastAPI Flask Session Bridge
=================================================
Provides 100% cryptographic and binary compatibility with Flask's signed
session cookies (SecureCookieSessionInterface + itsdangerous).

Allows FastAPI endpoints to validate session cookies created by Flask and
issue session cookies that Flask transparently accepts.
"""

from typing import Dict, Any, Optional
import hashlib
from flask import Flask
from config import Config

# Re-use Flask's native signing serializer to ensure exact salt, key derivation,
# serializer tag logic, and secret key match Flask runtime.
_flask_app = Flask("session_bridge")
_flask_app.config.from_object(Config)
_signer = _flask_app.session_interface.get_signing_serializer(_flask_app)


def decode_flask_cookie(cookie_value: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and cryptographically validates a Flask session cookie.
    Returns session dict (e.g. {'user_id': 1, 'username': 'admin', 'role': 'super_admin'})
    or None if invalid/tampered/expired.
    """
    if not cookie_value:
        return None
    try:
        data = _signer.loads(
            cookie_value,
            max_age=int(Config.PERMANENT_SESSION_LIFETIME.total_seconds())
        )
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def encode_flask_cookie(session_data: Dict[str, Any]) -> str:
    """
    Encodes session dictionary into a signed Flask session cookie string.
    """
    return _signer.dumps(session_data)
