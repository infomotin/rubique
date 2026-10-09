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
from models.custom_cube_model import CustomCubeModel, SUPPORTED_SHAPES
from models.dev_model import DevModel
from models.security_model import SecurityModel

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/admin')

def super_admin_required(f):
    """Super Admin authorization decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Access denied! Please login first.', 'warning')
            return redirect(url_for('auth.login', next=request.full_path.rstrip('?')))
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
        coupons=coupons,
        active_page='overview'
    )

# =============================================================================
# DEDICATED SEPARATE SUPER ADMIN MENU PAGES (MODULAR MVC ARCHITECTURE)
# =============================================================================

@super_admin_bp.route('/overview')
@super_admin_required
def overview_page():
    """Dedicated Super Admin Executive Overview Page"""
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/users')
@super_admin_required
def users_page():
    """Dedicated User Directory & RBAC Roles Management Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    users_list = AdminModel.get_all_users()
    return render_template(
        'super_admin/users.html',
        user=user,
        stats=stats,
        users_list=users_list,
        active_page='users'
    )

@super_admin_bp.route('/competitions')
@super_admin_required
def competitions_page():
    """Dedicated Tournament & Competition Declaration Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    competitions = AdminModel.get_all_competitions()
    return render_template(
        'super_admin/competitions.html',
        user=user,
        stats=stats,
        competitions=competitions,
        active_page='competitions'
    )

@super_admin_bp.route('/courses')
@super_admin_required
def courses_page():
    """Dedicated Courses & Curriculum Management Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    courses = AdminModel.get_all_courses()
    return render_template(
        'super_admin/courses.html',
        user=user,
        stats=stats,
        courses=courses,
        active_page='courses'
    )

@super_admin_bp.route('/coupons')
@super_admin_required
def coupons_page():
    """Dedicated Promo Coupons & Rewards Management Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    coupons = AdminModel.get_all_coupons()
    return render_template(
        'super_admin/coupons.html',
        user=user,
        stats=stats,
        coupons=coupons,
        active_page='coupons'
    )

@super_admin_bp.route('/custom-cubes')
@super_admin_required
def custom_cubes_page():
    """Dedicated Custom Cubes & Clans Moderation Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    cubes = CustomCubeModel.get_public_cubes(limit=50)
    challenges = CustomCubeModel.get_group_challenges(limit=50)
    return render_template(
        'super_admin/custom_cubes.html',
        user=user,
        stats=stats,
        cubes=cubes,
        challenges=challenges,
        supported_shapes=SUPPORTED_SHAPES,
        active_page='custom_cubes'
    )

@super_admin_bp.route('/logs')
@super_admin_required
def logs_page():
    """Dedicated System Audit & Security Trail Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    logs = DevModel.get_logs(limit=50)
    return render_template(
        'super_admin/logs.html',
        user=user,
        stats=stats,
        logs=logs,
        active_page='logs'
    )

@super_admin_bp.route('/games')
@super_admin_required
def games_page():
    """Dedicated Game Toggles & Real-Time Security Observation Command Center"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = AdminModel.get_system_stats()
    game_settings = SecurityModel.get_all_game_settings()
    activities = SecurityModel.get_all_game_activities(limit=60)
    security_events = SecurityModel.get_recent_security_events(limit=60)
    game_stats = SecurityModel.get_game_activity_stats()
    
    return render_template(
        'super_admin/games.html',
        user=user,
        stats=stats,
        game_settings=game_settings,
        activities=activities,
        security_events=security_events,
        game_stats=game_stats,
        active_page='games'
    )

@super_admin_bp.route('/games/toggle', methods=['POST'])
@super_admin_required
def toggle_game_setting():
    """Toggles or updates game module status (Chess, Card, Speedcube, Anti-Cheat)"""
    if request.is_json:
        data = request.get_json() or {}
        setting_key = data.get('setting_key')
        setting_value = '1' if data.get('setting_value') in [1, '1', True, 'true'] else '0'
    else:
        setting_key = request.form.get('setting_key')
        setting_value = '1' if request.form.get('setting_value') in ['1', 'on', 'true', True] else '0'

    valid_keys = [
        'chess_game_enabled',
        'card_game_enabled',
        'speedcube_game_enabled',
        'game_anti_cheat_enabled',
        'security_audit_logging',
        'bit_telemetry_enabled'
    ]

    if setting_key in valid_keys:
        SecurityModel.set_setting(setting_key, setting_value)
        status_text = "ENABLED" if setting_value == '1' else "DISABLED"
        friendly_name = setting_key.replace('_', ' ').title()
        
        # Log to telemetry
        SecurityModel.log_telemetry_bit(
            module="AdminSecurity",
            action=f"TOGGLE_{setting_key.upper()}",
            payload_data=f"{setting_key}={setting_value}",
            user_id=session.get('user_id'),
            role=session.get('role'),
            client_ip=request.remote_addr
        )

        if request.is_json:
            return jsonify({'success': True, 'setting_key': setting_key, 'setting_value': setting_value, 'status': status_text})
        flash(f"{friendly_name} is now {status_text} globally across the platform.", 'success')
    else:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid setting key'}), 400
        flash('Invalid setting key specified!', 'error')

    return redirect(url_for('super_admin.games_page'))

@super_admin_bp.route('/games/action', methods=['POST'])
@super_admin_required
def game_action():
    """Intervenes in live game sessions: Freeze or Terminate"""
    game_type = request.form.get('game_type', '').strip().lower()
    game_id = request.form.get('game_id')
    action = request.form.get('action', '').strip().lower()

    if game_type in ['chess', 'card'] and game_id:
        if action == 'freeze':
            SecurityModel.freeze_game(game_type, game_id)
            flash(f"Game session #{game_id} ({game_type.title()}) has been FROZEN by Super Admin.", 'warning')
        elif action == 'terminate':
            SecurityModel.terminate_game(game_type, game_id)
            flash(f"Game session #{game_id} ({game_type.title()}) has been TERMINATED immediately.", 'info')

        SecurityModel.log_telemetry_bit(
            module="AdminOversight",
            action=f"{action.upper()}_SESSION",
            payload_data=f"{game_type}#{game_id}",
            user_id=session.get('user_id'),
            role=session.get('role'),
            client_ip=request.remote_addr
        )

    return redirect(url_for('super_admin.games_page'))

@super_admin_bp.route('/security/dismiss', methods=['POST'])
@super_admin_required
def dismiss_security_event():
    """Dismisses / acknowledges a security anomaly event"""
    event_id = request.form.get('event_id')
    if event_id:
        SecurityModel.dismiss_security_event(event_id)
        flash('Security incident alert acknowledged and cleared.', 'info')
    return redirect(url_for('super_admin.games_page'))

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
    """Deletes a user account together with every dependent record"""
    target_user_id = request.form.get('user_id', '')
    try:
        target_user_id = int(target_user_id)
    except (TypeError, ValueError):
        target_user_id = 0

    if target_user_id and target_user_id != session.get('user_id'):
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
    try:
        modules_count = int(request.form.get('modules_count', 5))
    except (TypeError, ValueError):
        modules_count = 5
    modules_count = max(1, min(modules_count, 50))

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
    try:
        discount_percent = int(request.form.get('discount_percent', 100))
    except (TypeError, ValueError):
        discount_percent = 100
    discount_percent = max(0, min(discount_percent, 100))

    if code and reward_text:
        if AdminModel.find_coupon(code.upper()):
            flash(f'Coupon {code.upper()} already exists! Pick a different code.', 'error')
        else:
            AdminModel.create_coupon(code, reward_text, discount_percent)
            flash(f'Coupon {code.upper()} created successfully!', 'success')
    else:
        flash('Coupon code and reward text are required!', 'error')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/coupons/delete', methods=['POST'])
@super_admin_required
def delete_coupon():
    coupon_id = request.form.get('coupon_id')
    if coupon_id:
        AdminModel.delete_coupon(coupon_id)
        flash('Coupon deleted.', 'info')
    return redirect(url_for('super_admin.dashboard'))
