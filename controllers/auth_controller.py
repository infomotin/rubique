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
            flash('Ai page access korte hole age login korun!', 'warning')
            return redirect(url_for('auth.login', next=request.url))
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
            flash('Username ebong Password dewa baddhotamulok!', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password ontoto 6 character er hote hobe!', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Password duto match koreni! Abar cheshta korun.', 'error')
            return render_template('register.html')

        # Check unique username
        existing_user = UserModel.find_by_username(username)
        if existing_user:
            flash('Ai username ti already ache! Onno username select korun.', 'error')
            return render_template('register.html')

        # Create user in database (MySQL / SQLite) with selected role
        role = request.form.get('role', 'user')
        if role not in ['super_admin', 'developer', 'user']:
            role = 'user'

        user_id = UserModel.create_user(username, email, password)
        if user_id:
            # Update role if selected
            from models.admin_model import AdminModel
            AdminModel.update_user_role(user_id, role)
            flash(f'Registration successful as {role.upper()}! Ekhon sign in korun.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration e somoshya hoyeche! Abar cheshta korun.', 'error')

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
            
            flash(f'Swagotom, {user["username"]} ({user.get("role", "user").upper()})!', 'success')
            
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
                
            # Role-Specific Dashboard Redirection
            if session['role'] == 'super_admin':
                return redirect(url_for('super_admin.dashboard'))
            elif session['role'] == 'developer':
                return redirect(url_for('developer.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
            
        flash('Invalid username ba password! Sothik tottho din.', 'error')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User Logout Controller"""
    session.clear()
    flash('Apni successfully logged out hoyechen.', 'info')
    return redirect(url_for('home.index'))
