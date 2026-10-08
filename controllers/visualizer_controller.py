"""
CubePermutation AI - Visualizer Controller (MVC Pattern)
========================================================
Handles Group Theory Permutation Visualizer main interactive laboratory.
"""

from flask import Blueprint, render_template, session
from models.user_model import UserModel
from .auth_controller import login_required

visualizer_bp = Blueprint('visualizer', __name__, url_prefix='/visualizer')

@visualizer_bp.route('/')
@login_required
def index():
    """Main Permutation Network & 3D Isometric Cube Visualizer (Protected)"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id) if user_id else None
    return render_template('visualizer.html', user=user, username=session.get('username') or 'Speedcuber')

