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
from datetime import timedelta

# Attempt to load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed, rely on system os.environ


class Config:
    """
    Application Configuration Class
    Holds all cryptographic keys, database connections, and session policies.
    """

    # Flask Secret Key for signing session cookies and CSRF tokens
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cube_permutation_group_theory_mvc_super_key_2026')

    # Environment mode (development / production / testing)
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # MySQL Database Connection Settings (Default for Laragon / XAMPP)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
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
    # Secure flag enables HTTPS-only cookie transmission
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    # Session lifespan (default 7 days)
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('PERMANENT_SESSION_LIFETIME_DAYS', 7)))
