"""
CubePermutation AI - Authentication Service
============================================
Encapsulates user authentication, registration validation, password checking,
age-gate verification, and role resolution.

Easy Description:
- Handles the business rules for logging in and signing up.
- Validates passwords, checks whether users are at least 18 years old, and prevents duplicate accounts.
- Prepares session variables safely so users get sent to the right dashboard.
"""

from typing import Tuple, Optional, Dict, Any
from flask import session, url_for
from models.user_model import UserModel
from models.db import execute_update
from models.card_club import groups as club_groups
from models.card_club import economy as club_economy
from models.card_club import devices as club_devices
from utils.validators import validate_username, validate_email, validate_password_strength
from utils.security import verify_password


class AuthService:
    """
    Authentication & Identity Domain Service
    """

    @staticmethod
    def authenticate(username: str, password: str, request_obj=None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticates username and password credentials.
        Performs device binding security check when request object is supplied.

        Easy Description:
        Verifies login credentials and makes sure the device matches the user's bound device.
        """
        if not username or not password:
            return False, None, "Username and password are required."

        user = UserModel.find_by_username(username.strip())
        if not user:
            return False, None, "Invalid username or password. Please verify your credentials."

        # Verify password using secure hash verification
        is_valid = UserModel.verify_password(user['password_hash'], password.strip())
        if not is_valid:
            return False, None, "Invalid username or password. Please verify your credentials."

        # Device binding check (one account per device security policy)
        if request_obj:
            device_key = club_devices.compose_device_key(request_obj)[1]
            device_ok, device_msg = club_devices.check_login(user, device_key)
            if not device_ok:
                return False, None, device_msg

        return True, user, None

    @staticmethod
    def register(
        username: str,
        email: str,
        password: str,
        confirm_password: str,
        date_of_birth: str,
        request_obj=None
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validates registration constraints, enforces 18+ age gate, creates user record,
        and initializes welcome bonus coins.

        Easy Description:
        Validates user registration input, enforces age restrictions, saves the account, and gives welcome coins.
        """
        # 1. Input format validations
        u_ok, u_err = validate_username(username)
        if not u_ok:
            return False, None, u_err

        p_ok, p_err = validate_password_strength(password, min_length=6)
        if not p_ok:
            return False, None, p_err

        if password != confirm_password:
            return False, None, "Passwords do not match. Please try again."

        # 2. Age gate validation (18+ requirement for gaming services)
        if not date_of_birth:
            return False, None, "Date of birth is required (18+ services on this site)."
        
        dob = club_groups.parse_dob(date_of_birth.strip())
        if dob is None:
            return False, None, "Date of birth must be in YYYY-MM-DD format."
        if not club_groups.is_adult(dob):
            return False, None, "You must be at least 18 years old to register."

        # 3. Device binding check (prevent multi-account fraud)
        device_key = None
        if request_obj:
            _strength, device_key = club_devices.compose_device_key(request_obj)
            dev_ok, dev_msg = club_devices.check_registration(0, device_key)
            if not dev_ok:
                return False, None, dev_msg

        # 4. Check for existing username
        if UserModel.find_by_username(username.strip()):
            return False, None, "Username is already taken. Please choose another username."

        # 5. Create user in database
        try:
            user_id = UserModel.create_user(username.strip(), email.strip() if email else '', password.strip())
        except Exception:
            return False, None, "Registration failed due to a database error. Please try again."

        if not user_id:
            return False, None, "Registration failed. Please try again."

        # 6. Store verified DOB and bind device
        execute_update(
            "UPDATE users SET date_of_birth = %s WHERE id = %s",
            "UPDATE users SET date_of_birth = ? WHERE id = ?",
            (dob.isoformat(), user_id)
        )
        if device_key:
            club_devices.bind_device(user_id, device_key)

        # 7. Grant starting economy coins
        try:
            club_economy.grant_starting_balance(user_id)
        except Exception:
            pass  # Non-fatal: starting balance can be claimed via support

        return True, user_id, None

    @staticmethod
    def establish_session(user: Dict[str, Any]) -> None:
        """
        Initializes fresh Flask session parameters for the authenticated user.

        Easy Description:
        Clears old session data and logs in the current user with their ID, name, and role.
        """
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user.get('role', 'user')

    @staticmethod
    def get_post_login_redirect_url(user_role: str, target_next: Optional[str] = None) -> str:
        """
        Resolves safe destination URL after login based on RBAC role and safe relative redirect.

        Easy Description:
        Determines where the user should be redirected after successful sign-in.
        """
        # Prevent open-redirect attacks by only honoring local relative URLs
        if target_next and target_next.startswith('/') and not target_next.startswith('//'):
            return target_next

        if user_role == 'super_admin':
            return url_for('super_admin.dashboard')
        elif user_role == 'developer':
            return url_for('developer.dashboard')
        return url_for('feed.newsfeed')
