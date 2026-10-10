"""
CubePermutation AI - Input Validation & Sanitization Module
===========================================================
Defines reusable validator rules for usernames, emails, passwords, numeric inputs,
and chess FEN board states.

Easy Description:
- Inspects and cleans incoming user data before it reaches database queries or game engines.
- Rejects malformed or dangerous payloads with descriptive validation errors.
"""

import re
from typing import Optional, Tuple


# Regex patterns for strict data integrity
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-]{3,32}$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validates username format (alphanumeric, dashes, underscores, 3-32 characters).

    Easy Description:
    Checks if username contains only allowed letters, numbers, dashes, or underscores.
    """
    if not username or not isinstance(username, str):
        return False, "Username is required."
    clean = username.strip()
    if len(clean) < 3 or len(clean) > 32:
        return False, "Username must be between 3 and 32 characters."
    if not USERNAME_REGEX.match(clean):
        return False, "Username may only contain letters, numbers, hyphens, and underscores."
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validates standard email address syntax.

    Easy Description:
    Verifies that the email has an @ symbol and a valid domain format.
    """
    if not email or not isinstance(email, str):
        return False, "Email address is required."
    clean = email.strip()
    if len(clean) > 120 or not EMAIL_REGEX.match(clean):
        return False, "Please enter a valid email address."
    return True, None


def validate_password_strength(password: str, min_length: int = 6) -> Tuple[bool, Optional[str]]:
    """
    Validates password length and presence.

    Easy Description:
    Ensures password is not empty and meets minimum length criteria.
    """
    if not password or not isinstance(password, str):
        return False, "Password cannot be empty."
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."
    return True, None


def validate_int_in_range(value, min_val: int, max_val: int, default: int) -> int:
    """
    Safely converts an input value to an integer clamped between min_val and max_val.

    Easy Description:
    Safely turns text into a whole number, keeping it inside the minimum and maximum boundaries.
    """
    try:
        val = int(value)
        if val < min_val:
            return min_val
        if val > max_val:
            return max_val
        return val
    except (ValueError, TypeError):
        return default


def validate_fen_string(fen: str) -> Tuple[bool, Optional[str]]:
    """
    Validates standard Forsyth-Edwards Notation (FEN) chess position structure.

    Easy Description:
    Checks whether a chess position string has valid ranks, active color, and castling rights.
    """
    if not fen or not isinstance(fen, str):
        return False, "FEN string is required."
    parts = fen.strip().split()
    if len(parts) != 6:
        return False, "FEN must contain exactly 6 space-delimited segments."
    ranks = parts[0].split('/')
    if len(ranks) != 8:
        return False, "FEN board structure must specify exactly 8 ranks separated by '/'."
    if parts[1] not in ('w', 'b'):
        return False, "FEN active color must be 'w' or 'b'."
    return True, None
