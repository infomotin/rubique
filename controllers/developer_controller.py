"""
CubePermutation AI - Developer Controller (MVC Architecture)
============================================================
DevOps HUD & Telemetry: Live System Load, Process Health, Error Logs,
Algorithm Latency Benchmarks, and Diagnostic Testing.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.dev_model import DevModel
from models.user_model import UserModel

developer_bp = Blueprint('developer', __name__, url_prefix='/developer')

def developer_required(f):
    """Developer / Super Admin authorization decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Access denied! Please login first.', 'warning')
            return redirect(url_for('auth.login', next=request.full_path.rstrip('?')))
        if session.get('role') not in ['developer', 'super_admin']:
            flash('Unauthorized! Developer access is required.', 'error')
            return redirect(url_for('home.index'))
        return f(*args, **kwargs)
    return decorated_function

@developer_bp.route('/dashboard')
@developer_required
def dashboard():
    """Developer HUD Telemetry View with Full Cyber Suite & Diagnostics"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    telemetry = DevModel.get_telemetry()
    logs = DevModel.get_logs(limit=40)
    db_stats = DevModel.get_database_stats()
    
    return render_template(
        'developer_dashboard.html',
        user=user,
        telemetry=telemetry,
        logs=logs,
        db_stats=db_stats,
        active_page='telemetry'
    )

# =============================================================================
# DEDICATED SEPARATE DEVELOPER WORKSPACE PAGES (MODULAR MVC ARCHITECTURE)
# =============================================================================

@developer_bp.route('/telemetry')
@developer_required
def telemetry_page():
    """Dedicated Live Telemetry HUD & System Gauges Page"""
    return redirect(url_for('developer.dashboard'))

@developer_bp.route('/solver')
@developer_required
def solver_page():
    """Dedicated Kociemba Two-Phase Algorithm Benchmark & Profiler Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    telemetry = DevModel.get_telemetry()
    return render_template(
        'developer/solver.html',
        user=user,
        telemetry=telemetry,
        active_page='solver'
    )

@developer_bp.route('/opencv')
@developer_required
def opencv_page():
    """Dedicated OpenCV Computer Vision HSV Sandbox & Calibrator Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    telemetry = DevModel.get_telemetry()
    return render_template(
        'developer/opencv.html',
        user=user,
        telemetry=telemetry,
        active_page='opencv'
    )

@developer_bp.route('/database')
@developer_required
def database_page():
    """Dedicated Database Schema & SQL Query Inspector Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    telemetry = DevModel.get_telemetry()
    db_stats = DevModel.get_database_stats()
    return render_template(
        'developer/database.html',
        user=user,
        telemetry=telemetry,
        db_stats=db_stats,
        active_page='database'
    )

@developer_bp.route('/api-sandbox')
@developer_required
def api_page():
    """Dedicated API Documentation & Sandbox Testing Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    telemetry = DevModel.get_telemetry()
    return render_template(
        'developer/api.html',
        user=user,
        telemetry=telemetry,
        active_page='api'
    )

@developer_bp.route('/logs')
@developer_required
def logs_page():
    """Dedicated System Logs & Exception Traces Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    telemetry = DevModel.get_telemetry()
    logs = DevModel.get_logs(limit=60)
    return render_template(
        'developer/logs.html',
        user=user,
        telemetry=telemetry,
        logs=logs,
        active_page='logs'
    )

@developer_bp.route('/shapes')
@developer_required
def shapes_page():
    """Dedicated 10 Rubik's Cube Shape Geometries Engine Debugger Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    telemetry = DevModel.get_telemetry()
    from models.custom_cube_model import SUPPORTED_SHAPES
    return render_template(
        'developer/shapes.html',
        user=user,
        telemetry=telemetry,
        supported_shapes=SUPPORTED_SHAPES,
        active_page='shapes'
    )

@developer_bp.route('/diagnostics', methods=['POST'])
@developer_required
def run_diagnostics():
    """Runs live self-diagnostics suite on Kociemba, OpenCV, and DB"""
    results = DevModel.run_diagnostics()
    DevModel.log_event('DIAGNOSTIC', 'SelfTest', 'Ran automated system benchmark diagnostics suite.')
    return jsonify({'success': True, 'results': results})

@developer_bp.route('/logs/clear', methods=['POST'])
@developer_required
def clear_logs():
    """Clears system logs"""
    DevModel.clear_logs()
    flash('Technical system logs cleared.', 'info')
    return redirect(url_for('developer.dashboard'))

@developer_bp.route('/logs/create', methods=['POST'])
@developer_required
def create_log():
    """Injects a diagnostic log"""
    level = request.form.get('level', 'INFO').strip()
    module = request.form.get('module', 'DevConsole').strip()
    message = request.form.get('message', '').strip()
    if message:
        DevModel.log_event(level, module, message)
        flash('Log injected successfully.', 'success')
    return redirect(url_for('developer.dashboard'))
