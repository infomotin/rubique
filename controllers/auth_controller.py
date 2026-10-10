"""
CubePermutation AI - Authentication Controller (MVC Pattern)
============================================================
Handles user registration, login, session security, and logout.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user_model import UserModel
from models.db import execute_update
from models.card_club import groups as club_groups
from models.card_club import economy as club_economy
from models.card_club import devices as club_devices

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Route protection decorator for authenticated members"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.full_path.rstrip('?')))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Separate User Registration Controller"""
    invite_code = request.args.get('invite') or request.form.get('invite') or session.get('pending_invite_code')
    next_url = request.args.get('next') or request.form.get('next')

    invite_group = None
    if invite_code:
        invite_group = club_groups.get_group_by_invite_code(invite_code)
        if invite_group:
            session['pending_invite_code'] = invite_code
            if not next_url:
                next_url = url_for('card_club.group_page', gid=invite_group['id'])

    if 'user_id' in session:
        if invite_code and invite_group:
            try:
                gid = club_groups.join_group_by_invite_code(invite_code, session['user_id'])
                session.pop('pending_invite_code', None)
                flash(f"Welcome to {invite_group['name']}! You are now a member.", 'success')
                return redirect(url_for('card_club.group_page', gid=gid))
            except Exception:
                pass
        return redirect(next_url or url_for('visualizer.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip()

        # Validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

        # Age gate (Card Club is 18+): date of birth is mandatory
        if not date_of_birth:
            flash('Date of birth is required (18+ services on this site).', 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)
        dob = club_groups.parse_dob(date_of_birth)
        if dob is None:
            flash('Date of birth must be in YYYY-MM-DD format.', 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)
        if not club_groups.is_adult(dob):
            flash('You must be at least 18 years old to register.', 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

        # Device binding (one account per device - multi-account guard)
        _strength, device_key = club_devices.compose_device_key(request)
        ok, device_msg = club_devices.check_registration(0, device_key)
        if not ok:
            flash(device_msg, 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

        # Check unique username
        existing_user = UserModel.find_by_username(username)
        if existing_user:
            flash('Username is already taken. Please choose another username.', 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

        # Create user in database (MySQL / SQLite).
        user_id = None
        try:
            user_id = UserModel.create_user(username, email, password)
        except Exception:
            user_id = None

        if user_id:
            # Card Club: store verified DOB, bind device, seed starting coins
            execute_update(
                "UPDATE users SET date_of_birth = %s WHERE id = %s",
                "UPDATE users SET date_of_birth = ? WHERE id = ?",
                (dob.isoformat(), user_id))
            club_devices.bind_device(user_id, device_key)
            try:
                club_economy.grant_starting_balance(user_id)
            except Exception:
                flash('Account created, but your starting coin grant failed. '
                      'Please contact support.', 'warning')

            # If user registered via Card Club invite:
            inv_code = request.form.get('invite') or session.pop('pending_invite_code', None)
            if inv_code:
                session.clear()
                session['user_id'] = user_id
                session['username'] = username
                session['role'] = 'user'
                try:
                    target_gid = club_groups.join_group_by_invite_code(inv_code, user_id)
                    g_info = club_groups.get_group(target_gid)
                    flash(f"Account created! Welcome to {g_info['name'] if g_info else 'the group'}. Let's play!", 'success')
                    return redirect(url_for('card_club.group_page', gid=target_gid))
                except Exception:
                    pass

            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                flash('Registration successful! Please sign in to continue.', 'success')
                return redirect(url_for('auth.login', next=next_url))

            flash('Registration successful! Please sign in to continue.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Please try again.', 'error')

    return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Separate User Login Controller with Role Redirection"""
    invite_code = request.args.get('invite') or session.get('pending_invite_code')
    next_url = request.args.get('next')

    if 'user_id' in session:
        if invite_code:
            try:
                target_gid = club_groups.join_group_by_invite_code(invite_code, session['user_id'])
                session.pop('pending_invite_code', None)
                g_info = club_groups.get_group(target_gid)
                flash(f"Joined {g_info['name'] if g_info else 'the group'}.", 'success')
                return redirect(url_for('card_club.group_page', gid=target_gid))
            except Exception:
                pass
        role = session.get('role', 'user')
        if role == 'super_admin':
            return redirect(url_for('super_admin.dashboard'))
        elif role == 'developer':
            return redirect(url_for('developer.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = UserModel.find_by_username(username)
        if user and UserModel.verify_password(user['password_hash'], password):
            # Device binding check (bound accounts may not sign in elsewhere)
            device_key = club_devices.compose_device_key(request)
            device_ok, device_msg = club_devices.check_login(user, device_key)
            if not device_ok:
                flash(device_msg, 'error')
                return render_template('login.html', invite_code=invite_code, next=next_url)

            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            
            flash(f'Welcome back, {user["username"]} ({user.get("role", "user").upper()})!', 'success')
            
            # Check invite code for Card Club group redirect
            inv_code = request.form.get('invite') or request.args.get('invite') or session.pop('pending_invite_code', None)
            if inv_code:
                try:
                    target_gid = club_groups.join_group_by_invite_code(inv_code, user['id'])
                    g_info = club_groups.get_group(target_gid)
                    flash(f"Welcome back! You have joined {g_info['name'] if g_info else 'the group'}.", 'success')
                    return redirect(url_for('card_club.group_page', gid=target_gid))
                except Exception:
                    pass

            target_next = request.form.get('next') or request.args.get('next')
            # Only honour same-origin relative paths (prevents open redirect)
            if target_next and target_next.startswith('/') and not target_next.startswith('//'):
                return redirect(target_next)
                
            # Role-Specific Dashboard Redirection
            if session['role'] == 'super_admin':
                return redirect(url_for('super_admin.dashboard'))
            elif session['role'] == 'developer':
                return redirect(url_for('developer.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
            
        flash('Invalid username or password. Please verify your credentials and try again.', 'error')

    return render_template('login.html', invite_code=invite_code, next=next_url)

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """User Logout Controller"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home.index'))
