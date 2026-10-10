"""
CubePermutation AI - Authentication Controller (MVC Architecture)
==================================================================
Handles HTTP requests for user registration, user login, session teardown,
and invite-link routing. Delegates business logic to AuthService.

Easy Description:
- Receives login and registration form submissions from web visitors.
- Passes input to AuthService for validation and password verification.
- Directs logged-in members to their appropriate dashboard or invited card club table.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.auth_service import AuthService
from models.card_club import groups as club_groups
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration View & Submission Handler
    Enforces 18+ age verification, single-device constraints, and invite acceptance.
    """
    invite_code = request.args.get('invite') or request.form.get('invite') or session.get('pending_invite_code')
    next_url = request.args.get('next') or request.form.get('next')

    invite_group = None
    if invite_code:
        invite_group = club_groups.get_group_by_invite_code(invite_code)
        if invite_group:
            session['pending_invite_code'] = invite_code
            if not next_url:
                next_url = url_for('card_club.group_page', gid=invite_group['id'])

    # If already logged in, redirect immediately
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

        # Delegate business logic and validation to AuthService
        success, user_id, error_msg = AuthService.register(
            username=username,
            email=email,
            password=password,
            confirm_password=confirm_password,
            date_of_birth=date_of_birth,
            request_obj=request
        )

        if not success:
            flash(error_msg, 'error')
            return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)

        # Handle Card Club invitation auto-join if registered via invite
        inv_code = request.form.get('invite') or session.pop('pending_invite_code', None)
        if inv_code:
            AuthService.establish_session({'id': user_id, 'username': username, 'role': 'user'})
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

    return render_template('register.html', invite_code=invite_code, invite_group=invite_group, next_url=next_url)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login View & Authentication Handler
    Verifies credentials, checks device binding, and routes to appropriate role page.
    """
    invite_code = request.args.get('invite') or session.get('pending_invite_code')
    next_url = request.args.get('next')

    # If already logged in, redirect
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
        return redirect(AuthService.get_post_login_redirect_url(session.get('role', 'user'), next_url))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        success, user, error_msg = AuthService.authenticate(username, password, request_obj=request)
        if success and user:
            # Set up session using AuthService
            AuthService.establish_session(user)
            flash(f'Welcome back, {user["username"]} ({user.get("role", "user").upper()})!', 'success')

            # Handle invite code auto-join
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
            destination = AuthService.get_post_login_redirect_url(session['role'], target_next)
            return redirect(destination)

        flash(error_msg or 'Invalid username or password. Please verify your credentials and try again.', 'error')

    return render_template('login.html', invite_code=invite_code, next=next_url)


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    User Logout Handler
    Clears all active session tokens and returns visitor to the home page.
    """
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home.index'))
