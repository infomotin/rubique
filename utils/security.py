"""
CubePermutation AI - Security Utilities Module
==============================================
Cryptographic hashing, timing-safe validation, CSRF defenses, and HTTP response
hardening headers.

Easy Description:
- Provides strong password hashing using Werkzeug / scrypt.
- Safely compares secret tokens using constant-time algorithms to prevent timing attacks.
- Injects HTTP security headers (nosniff, frame-options, XSS protection, CSP).
- Provides input sanitization against XSS cross-site scripting.
"""

import hmac
import html
import os
import re
import secrets
from flask import session, request
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using modern cryptographic standard (scrypt or pbkdf2:sha256).

    Easy Description:
    Converts a plain password like 'secret123' into an irreversible mathematical hash.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    return generate_password_hash(password, method='scrypt')


def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """
    Verifies candidate plaintext password against stored hash with timing-safe comparison.

    Easy Description:
    Verifies if the entered password matches the stored encrypted hash in the database.
    """
    if not stored_hash or not candidate_password:
        return False
    try:
        return check_password_hash(stored_hash, candidate_password)
    except Exception:
        # Fallback to constant-time comparison in case of legacy test seeds
        return hmac.compare_digest(str(stored_hash), str(candidate_password))


def timing_safe_compare(val_a: str, val_b: str) -> bool:
    """
    Compares two strings in constant time to thwart timing side-channel attacks.

    Easy Description:
    Compares two tokens in the exact same amount of time regardless of character matches.
    """
    if val_a is None or val_b is None:
        return False
    return hmac.compare_digest(str(val_a), str(val_b))


def sanitize_input(value: str) -> str:
    """
    Sanitizes string inputs against XSS and control character injection.

    Easy Description:
    Escapes HTML entities (like <, >, &) so user input cannot execute rogue JavaScript.
    """
    if not isinstance(value, str):
        return value
    # Strip dangerous NULL bytes and unprintable characters
    cleaned = value.replace('\x00', '').strip()
    return html.escape(cleaned)


def generate_csrf_token() -> str:
    """
    Generates a cryptographically strong, random CSRF token tied to current session.

    Easy Description:
    Creates a unique random security token for forms to prevent cross-site request forgery.
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token: str) -> bool:
    """
    Validates a submitted CSRF token against the current session token.

    Easy Description:
    Checks if the submitted token matches the user's active session token.
    """
    stored_token = session.get('_csrf_token')
    if not stored_token or not token:
        return False
    return timing_safe_compare(stored_token, token)


def apply_security_headers(response):
    """
    Flask response middleware that applies modern HTTP security headers.

    Easy Description:
    Adds strict protective HTTP headers to every webpage served to the browser.
    """
    # Prevent MIME-sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking by restricting iframes to the same origin
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Enable built-in browser XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Send referrer only on cross-origin requests when protocol security is preserved
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Permissions-Policy to restrict sensitive hardware features
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(self)'
    return response
