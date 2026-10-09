"""
CubePermutation AI - User Profile Controller (MVC Architecture)
===============================================================
Comprehensive Speedcuber Profile Hub:
- Personal Profile Information & Speedcubing Credentials (WCA ID, Main Cube, Method, PB)
- Groups & Speedcubing Study Clans
- Speedcubing Friends & Connections
- Problem Build (Custom Built Rubik's Cubes & Geometries)
- Solver (Solve History, Competition Solutions & Clan Challenge Solutions)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user_model import UserModel
from models.solve_model import SolveModel
from models.community_model import CommunityModel
from models.custom_cube_model import CustomCubeModel, SUPPORTED_SHAPES
from models.db import query_all, query_one
from .auth_controller import login_required

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/')
@login_required
def index():
    """User Profile Dashboard with Groups, Friends, Problem Builds, and Solves"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    if not user:
        flash('User account not found.', 'error')
        return redirect(url_for('auth.logout'))

    # 1. Performance & Solves
    stats = SolveModel.get_user_stats(user_id)
    history = SolveModel.get_user_history(user_id, limit=50)

    # 2. Groups / Study Clans
    groups = CommunityModel.get_all_groups()

    # 3. Friends List
    friends = CommunityModel.get_user_friends(user_id)

    # 4. Problem Build: Custom Rubik's Cubes Authored by User
    custom_cubes = CustomCubeModel.get_user_cubes(user_id)

    # 5. Solver & Solutions: Solved Clan Challenges & Competition Entries
    solved_challenges = query_all(
        """SELECT cgc.*, cc.name as cube_name, cg.name as group_name 
           FROM cube_group_challenges cgc 
           JOIN custom_cubes cc ON cgc.cube_id = cc.id 
           JOIN chat_groups cg ON cgc.group_id = cg.id 
           WHERE cgc.solver_id = %s ORDER BY cgc.id DESC""",
        """SELECT cgc.*, cc.name as cube_name, cg.name as group_name 
           FROM cube_group_challenges cgc 
           JOIN custom_cubes cc ON cgc.cube_id = cc.id 
           JOIN chat_groups cg ON cgc.group_id = cg.id 
           WHERE cgc.solver_id = ? ORDER BY cgc.id DESC""",
        (user_id,)
    )

    competition_solves = query_all(
        """SELECT ce.*, c.title as comp_title, c.prize_trophy 
           FROM competition_entries ce 
           JOIN competitions c ON ce.competition_id = c.id 
           WHERE ce.user_id = %s ORDER BY ce.id DESC""",
        """SELECT ce.*, c.title as comp_title, c.prize_trophy 
           FROM competition_entries ce 
           JOIN competitions c ON ce.competition_id = c.id 
           WHERE ce.user_id = ? ORDER BY ce.id DESC""",
        (user_id,)
    )

    return render_template(
        'profile.html',
        user=user,
        stats=stats,
        history=history,
        groups=groups,
        friends=friends,
        custom_cubes=custom_cubes,
        solved_challenges=solved_challenges,
        competition_solves=competition_solves,
        supported_shapes=SUPPORTED_SHAPES
    )

@profile_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Update personal information, speedcubing credentials, bio, and avatar"""
    user_id = session.get('user_id')
    bio = request.form.get('bio', '').strip()
    avatar_color = request.form.get('avatar_color', '#818cf8').strip()
    wca_id = request.form.get('wca_id', '').strip()
    country = request.form.get('country', '').strip()
    main_cube = request.form.get('main_cube', '').strip() or 'GAN 12 MagLev 3x3'
    preferred_method = request.form.get('preferred_method', 'CFOP').strip()
    pb_single = request.form.get('pb_single', '').strip()
    pb_ao5 = request.form.get('pb_ao5', '').strip()

    UserModel.update_profile(
        user_id=user_id,
        bio=bio,
        avatar_color=avatar_color,
        wca_id=wca_id,
        country=country,
        main_cube=main_cube,
        preferred_method=preferred_method,
        pb_single=pb_single,
        pb_ao5=pb_ao5
    )
    flash('Personal information and speedcubing credentials successfully updated!', 'success')
    return redirect(url_for('profile.index'))

@profile_bp.route('/add-friend', methods=['POST'])
@login_required
def add_friend():
    """Adds a speedcubing friend directly from profile"""
    user_id = session.get('user_id')
    username = request.form.get('username', '').strip()
    friend = query_one(
        "SELECT id, username FROM users WHERE username = %s",
        "SELECT id, username FROM users WHERE username = ?",
        (username,)
    )
    if friend and friend['id'] != user_id:
        CommunityModel.add_friend(user_id, friend['id'])
        flash(f'You are now connected with {friend["username"]}!', 'success')
    else:
        flash('Speedcuber not found or you cannot add yourself as friend.', 'error')
    return redirect(url_for('profile.index') + '#friends')

@profile_bp.route('/create-group', methods=['POST'])
@login_required
def create_group():
    """Creates a new study clan directly from profile"""
    user_id = session.get('user_id')
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    passcode = request.form.get('passcode', '').strip() or None
    is_private = 1 if passcode else 0

    if name:
        CommunityModel.create_group(name, description, is_private, passcode, user_id)
        flash(f'Clan "{name}" successfully founded!', 'success')
    else:
        flash('Please enter a valid clan name.', 'error')
    return redirect(url_for('profile.index') + '#groups')

@profile_bp.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    """Clears all solve history for current user"""
    user_id = session.get('user_id')
    SolveModel.clear_all(user_id)
    flash('Solve history successfully cleared!', 'info')
    return redirect(url_for('profile.index') + '#solves')
