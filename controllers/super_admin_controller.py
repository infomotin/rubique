"""
CubePermutation AI - Super Admin Controller (MVC Architecture)
==============================================================
Executive Command Center: User Management, Competition Declaring,
Trophy Distribution, Courses Creation, and System Analytics.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.admin_model import AdminModel
from models.user_model import UserModel

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/admin')

def super_admin_required(f):
    """Super Admin authorization decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Access denied! Please login first.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('role') != 'super_admin':
            flash('Unauthorized! Super Admin access is required.', 'error')
            return redirect(url_for('home.index'))
        return f(*args, **kwargs)
    return decorated_function

@super_admin_bp.route('/dashboard')
@super_admin_required
def dashboard():
    """Super Admin Executive Command Center View"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    users_list = AdminModel.get_all_users()
    competitions = AdminModel.get_all_competitions()
    courses = AdminModel.get_all_courses()
    coupons = AdminModel.get_all_coupons()

    return render_template(
        'super_admin_dashboard.html',
        user=user,
        stats=stats,
        users_list=users_list,
        competitions=competitions,
        courses=courses,
        coupons=coupons
    )

@super_admin_bp.route('/users/role', methods=['POST'])
@super_admin_required
def change_role():
    """Changes a user's role (super_admin, developer, user)"""
    target_user_id = request.form.get('user_id')
    new_role = request.form.get('role')
    
    if target_user_id and new_role in ['super_admin', 'developer', 'user']:
        AdminModel.update_user_role(target_user_id, new_role)
        flash(f'User #{target_user_id} role successfully changed to {new_role}!', 'success')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/users/delete', methods=['POST'])
@super_admin_required
def delete_user():
    """Deletes a user account"""
    target_user_id = request.form.get('user_id')
    if target_user_id and int(target_user_id) != session.get('user_id'):
        AdminModel.delete_user(target_user_id)
        flash('User account deleted successfully.', 'info')
    else:
        flash('Cannot delete active Super Admin session!', 'error')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/competitions/create', methods=['POST'])
@super_admin_required
def create_competition():
    """Declares a new speedcubing competition"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    scramble = request.form.get('scramble', '').strip()
    prize_trophy = request.form.get('prize_trophy', 'Golden Polyhedron').strip()

    if title and scramble:
        AdminModel.create_competition(title, description, scramble, prize_trophy, session.get('user_id'))
        flash(f'Competition "{title}" declared successfully!', 'success')
    else:
        flash('Title and Scramble are required fields!', 'error')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/competitions/delete', methods=['POST'])
@super_admin_required
def delete_competition():
    comp_id = request.form.get('comp_id')
    if comp_id:
        AdminModel.delete_competition(comp_id)
        flash('Competition removed.', 'info')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/courses/create', methods=['POST'])
@super_admin_required
def create_course():
    """Publishes a new speedcubing / group theory course"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    difficulty = request.form.get('difficulty', 'Intermediate').strip()
    modules_count = int(request.form.get('modules_count', 5))

    if title:
        AdminModel.create_course(title, description, difficulty, modules_count, session.get('username'))
        flash(f'Course "{title}" published successfully!', 'success')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/courses/delete', methods=['POST'])
@super_admin_required
def delete_course():
    course_id = request.form.get('course_id')
    if course_id:
        AdminModel.delete_course(course_id)
        flash('Course removed.', 'info')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/coupons/create', methods=['POST'])
@super_admin_required
def create_coupon():
    """Generates a reward promo coupon"""
    code = request.form.get('code', '').strip()
    reward_text = request.form.get('reward_text', '').strip()
    discount_percent = int(request.form.get('discount_percent', 100))

    if code and reward_text:
        AdminModel.create_coupon(code, reward_text, discount_percent)
        flash(f'Coupon {code.upper()} created successfully!', 'success')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/coupons/delete', methods=['POST'])
@super_admin_required
def delete_coupon():
    coupon_id = request.form.get('coupon_id')
    if coupon_id:
        AdminModel.delete_coupon(coupon_id)
        flash('Coupon deleted.', 'info')
    return redirect(url_for('super_admin.dashboard'))
