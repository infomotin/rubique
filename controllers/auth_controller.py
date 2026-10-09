"""
CubePermutation AI - Authentication Controller (MVC Pattern)
============================================================
Handles user registration, login, session security, and logout.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user_model import UserModel

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
    if 'user_id' in session:
        return redirect(url_for('visualizer.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('register.html')

        # Check unique username
        existing_user = UserModel.find_by_username(username)
        if existing_user:
            flash('Username is already taken. Please choose another username.', 'error')
            return render_template('register.html')

        # Create user in database (MySQL / SQLite).
        # Public registration always creates a standard 'user' account so the
        # RBAC roles (developer / super_admin) can only be granted by an admin.
        user_id = None
        try:
            user_id = UserModel.create_user(username, email, password)
        except Exception:
            user_id = None

        if user_id:
            flash('Registration successful! Please sign in to continue.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Please try again.', 'error')

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Separate User Login Controller with Role Redirection"""
    if 'user_id' in session:
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
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            
            flash(f'Welcome back, {user["username"]} ({user.get("role", "user").upper()})!', 'success')
            
            next_url = request.args.get('next')
            # Only honour same-origin relative paths (prevents open redirect)
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
                
            # Role-Specific Dashboard Redirection
            if session['role'] == 'super_admin':
                return redirect(url_for('super_admin.dashboard'))
            elif session['role'] == 'developer':
                return redirect(url_for('developer.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
            
        flash('Invalid username or password. Please verify your credentials and try again.', 'error')

    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """User Logout Controller"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home.index'))
