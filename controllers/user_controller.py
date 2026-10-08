"""
CubePermutation AI - User Hub Controller (MVC Architecture)
===========================================================
Registered User Dashboard: Profile Management, Cube Solving Studio,
Competitions Arena, Courses Library, Trophy Cabinet, and Coupon Redemption.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user_model import UserModel
from models.solve_model import SolveModel
from models.admin_model import AdminModel
from models.db import query_one, query_all, execute_insert
from .auth_controller import login_required

user_bp = Blueprint('user', __name__, url_prefix='/dashboard')

@user_bp.route('/')
@login_required
def dashboard():
    """Registered User Main Hub Dashboard"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = SolveModel.get_user_stats(user_id)
    history = SolveModel.get_user_history(user_id, limit=15)
    competitions = AdminModel.get_all_competitions()
    courses = AdminModel.get_all_courses()
    
    # User's submitted competition entries
    user_entries = query_all(
        "SELECT * FROM competition_entries WHERE user_id = %s",
        "SELECT * FROM competition_entries WHERE user_id = ?",
        (user_id,)
    )

    return render_template(
        'user_dashboard.html',
        user=user,
        stats=stats,
        history=history,
        competitions=competitions,
        courses=courses,
        user_entries=user_entries
    )

@user_bp.route('/competitions/submit', methods=['POST'])
@login_required
def submit_competition():
    """Submits a solve solution to an active competition"""
    comp_id = request.form.get('competition_id')
    solution = request.form.get('solution', '').strip()
    move_count = len(solution.split()) if solution else 0
    time_seconds = float(request.form.get('time_seconds', 0.0))
    user_id = session.get('user_id')

    if comp_id and solution:
        execute_insert(
            "INSERT INTO competition_entries (competition_id, user_id, move_count, time_seconds, solution) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO competition_entries (competition_id, user_id, move_count, time_seconds, solution) VALUES (?, ?, ?, ?, ?)",
            (comp_id, user_id, move_count, time_seconds, solution)
        )
        flash(f'Competition solve submitted successfully! ({move_count} moves)', 'success')
    else:
        flash('Invalid submission! Please enter valid solution moves.', 'error')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/coupons/redeem', methods=['POST'])
@login_required
def redeem_coupon():
    """Redeems promo code for rewards or trophy unlocks"""
    code = request.form.get('code', '').strip().upper()
    coupon = query_one(
        "SELECT * FROM coupons WHERE code = %s AND status = 'active'",
        "SELECT * FROM coupons WHERE code = ? AND status = 'active'",
        (code,)
    )
    if coupon:
        flash(f'Coupon {code} Redeemed! Reward: {coupon["reward_text"]}', 'success')
    else:
        flash('Invalid or expired coupon code! Try "GROUPTHEORY2026".', 'error')
    return redirect(url_for('user.dashboard'))
