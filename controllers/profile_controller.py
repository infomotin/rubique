"""
CubePermutation AI - User Profile Controller (MVC Pattern)
==========================================================
Handles User Profile dashboard, Statistics, and Solve History storage.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user_model import UserModel
from models.solve_model import SolveModel
from .auth_controller import login_required

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/')
@login_required
def index():
    """User Profile Dashboard with solve statistics and history"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    if not user:
        flash('User account khuje paoa jayni!', 'error')
        return redirect(url_for('auth.logout'))

    stats = SolveModel.get_user_stats(user_id)
    history = SolveModel.get_user_history(user_id, limit=30)
    
    return render_template('profile.html', user=user, stats=stats, history=history)

@profile_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Profile bio and avatar color update"""
    user_id = session.get('user_id')
    bio = request.form.get('bio', '').strip()
    avatar_color = request.form.get('avatar_color', '#818cf8').strip()

    UserModel.update_profile(user_id, bio, avatar_color)
    flash('Profile successfully updated!', 'success')
    return redirect(url_for('profile.index'))

@profile_bp.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    """Clears all solve history for current user"""
    user_id = session.get('user_id')
    SolveModel.clear_all(user_id)
    flash('Solve history successfully cleared!', 'info')
    return redirect(url_for('profile.index'))
