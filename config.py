"""
CubePermutation AI - Enterprise Configuration Module
=====================================================
Centralized configuration manager supporting dotenv loading, database connection
credentials, session security parameters, and upload bounds.

Easy Description:
- Reads system settings and secrets from the .env file.
- Provides fallback defaults if .env is missing.
- Sets secure session cookie policies (HttpOnly, SameSite) to protect against session hijacking.
"""

import os
import secrets
from datetime import timedelta

# Attempt to load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed, rely on system os.environ


def _load_secret_key() -> str:
    """
    Session/CSRF signing key resolution (no hardcoded fallback):
    1. SECRET_KEY from the environment / .env (never committed).
    2. Otherwise a machine-local random key persisted under .instance/
       (git-ignored, mode 0600) so Flask and FastAPI sign the same cookies.
    """
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key

    base_dir = os.path.abspath(os.path.dirname(__file__))
    key_dir = os.path.join(base_dir, '.instance')
    key_file = os.path.join(key_dir, 'secret_key')
    try:
        if os.path.exists(key_file):
            with open(key_file, 'r', encoding='utf-8') as fh:
                stored = fh.read().strip()
            if stored:
                return stored
        os.makedirs(key_dir, exist_ok=True)
        generated = secrets.token_urlsafe(48)
        fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write(generated)
        return generated
    except FileExistsError:
        # Another process created it first - reuse it.
        with open(key_file, 'r', encoding='utf-8') as fh:
            return fh.read().strip()
    except OSError:
        # Read-only filesystem: still boot, but sessions will not survive a
        # process restart (Flask and FastAPI in one process stay consistent).
        return secrets.token_urlsafe(48)


class Config:
    """
    Application Configuration Class
    Holds all cryptographic keys, database connections, and session policies.
    """

    # Flask Secret Key for signing session cookies and CSRF tokens
    SECRET_KEY = _load_secret_key()

    # Environment mode (development / production / testing)
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # Demo accounts (admin/admin123 etc.) are auto-created outside production.
    # Set SEED_DEMO_ACCOUNTS=0/1 to override explicitly (None = env-driven).
    SEED_DEMO_ACCOUNTS = os.environ.get('SEED_DEMO_ACCOUNTS')

    # MySQL Database Connection Settings (Default for Laragon / XAMPP)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'toor')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'cube_permutation')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

    # SQLite Fallback DB Path for portable operation
    SQLITE_DB = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cubedata.db')

    # Uploads directory and maximum file size limits
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH_MB', 16)) * 1024 * 1024  # Default 16 MB

    # Enterprise Session Hardening Policies
    # HTTPOnly prevents JavaScript access to session cookies (stops XSS session theft)
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() in ('true', '1')
    # SameSite=Lax prevents CSRF attacks during cross-site navigations
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    # Secure flag enables HTTPS-only cookie transmission (forced on in production)
    SESSION_COOKIE_SECURE = os.environ.get(
        'SESSION_COOKIE_SECURE', 'True' if FLASK_ENV == 'production' else 'False'
    ).lower() in ('true', '1')
    # Session lifespan (default 7 days)
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('PERMANENT_SESSION_LIFETIME_DAYS', 7)))
