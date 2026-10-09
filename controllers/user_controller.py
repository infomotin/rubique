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
from models.community_model import CommunityModel
from models.custom_cube_model import CustomCubeModel, SUPPORTED_SHAPES
from models.db import query_one, query_all, execute_insert
from .auth_controller import login_required

user_bp = Blueprint('user', __name__, url_prefix='/dashboard')

@user_bp.route('/')
@login_required
def dashboard():
    """Registered User Main Hub Dashboard with Working Stages and Community features"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = SolveModel.get_user_stats(user_id)
    history = SolveModel.get_user_history(user_id, limit=15)
    competitions = AdminModel.get_all_competitions()
    courses = AdminModel.get_all_courses()
    
    # Community & Social Data
    videos = CommunityModel.get_all_videos()
    groups = CommunityModel.get_all_groups()
    friends = CommunityModel.get_user_friends(user_id)
    posts = CommunityModel.get_all_posts()

    # User's submitted competition entries
    user_entries = query_all(
        "SELECT * FROM competition_entries WHERE user_id = %s",
        "SELECT * FROM competition_entries WHERE user_id = ?",
        (user_id,)
    )

    # Custom Cubes Workshop & Group Challenges
    user_cubes = CustomCubeModel.get_user_cubes(user_id)
    public_cubes = CustomCubeModel.get_public_cubes(limit=15)
    group_challenges = CustomCubeModel.get_group_challenges(limit=25)

    return render_template(
        'user/overview.html',
        user=user,
        stats=stats,
        history=history,
        competitions=competitions,
        courses=courses,
        user_entries=user_entries,
        videos=videos,
        groups=groups,
        friends=friends,
        posts=posts,
        user_cubes=user_cubes,
        public_cubes=public_cubes,
        group_challenges=group_challenges,
        supported_shapes=SUPPORTED_SHAPES,
        active_page='overview'
    )

# =============================================================================
# DEDICATED SEPARATE MENU PAGES (MODULAR MVC ARCHITECTURE)
# =============================================================================

@user_bp.route('/overview')
@login_required
def overview_page():
    """Dedicated Overview & Speedcubing Analytics Page"""
    return redirect(url_for('user.dashboard'))

@user_bp.route('/battle')
@login_required
def battle_page():
    """Dedicated 1v1 Human vs AI Battle Arena Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = SolveModel.get_user_stats(user_id)
    return render_template('user/battle.html', user=user, stats=stats, active_page='battle')

@user_bp.route('/learning')
@login_required
def learning_page():
    """Dedicated Visual Learning Hub & Group Theory Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    return render_template('user/learning.html', user=user, active_page='learning')

@user_bp.route('/guide')
@login_required
def guide_page():
    """Dedicated Beginner to Pro CFOP Step-by-Step Guide Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    return render_template('user/guide.html', user=user, active_page='guide')

@user_bp.route('/patterns')
@login_required
def patterns_page():
    """Dedicated Pattern Studio: artistic 3D cube pattern library"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    return render_template('user/patterns.html', user=user, active_page='patterns')

@user_bp.route('/videos')
@login_required
def videos_page():
    """Dedicated Speedcubing Video Showcase & Tutorials Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    videos = CommunityModel.get_all_videos(limit=50)
    return render_template('user/videos.html', user=user, videos=videos, active_page='videos')

@user_bp.route('/chat')
@login_required
def chat_page():
    """Dedicated Speedcuber Live Chat & Clans Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    groups = CommunityModel.get_all_groups()
    return render_template('user/chat.html', user=user, groups=groups, active_page='chat')

@user_bp.route('/friends')
@login_required
def friends_page():
    """Dedicated Friends & Buddies Network Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    friends = CommunityModel.get_user_friends(user_id)
    return render_template('user/friends.html', user=user, friends=friends, active_page='friends')

@user_bp.route('/blog')
@login_required
def blog_page():
    """Dedicated Speedcubing Blog & Community Insights Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    posts = CommunityModel.get_all_posts(limit=40)
    return render_template('user/blog.html', user=user, posts=posts, active_page='blog')

@user_bp.route('/competitions')
@login_required
def competitions_page():
    """Dedicated WCA Tournaments & Competitions Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    competitions = AdminModel.get_all_competitions()
    user_entries = query_all(
        "SELECT * FROM competition_entries WHERE user_id = %s",
        "SELECT * FROM competition_entries WHERE user_id = ?",
        (user_id,)
    )
    return render_template(
        'user/competitions.html',
        user=user,
        competitions=competitions,
        user_entries=user_entries,
        active_page='competitions'
    )

@user_bp.route('/courses')
@login_required
def courses_page():
    """Dedicated Pro Masterclasses & Certifications Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    courses = AdminModel.get_all_courses()
    return render_template('user/courses.html', user=user, courses=courses, active_page='courses')

@user_bp.route('/scan')
@login_required
def scan_page():
    """Dedicated OpenCV Cube Scanner & 2D/3D Color Net Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    return render_template('user/scan.html', user=user, active_page='scan')

@user_bp.route('/trophies')
@login_required
def trophies_page():
    """Dedicated Trophy Cabinet & Coupon Rewards Page"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    stats = SolveModel.get_user_stats(user_id)
    history = SolveModel.get_user_history(user_id, limit=20)
    return render_template('user/trophies.html', user=user, stats=stats, history=history, active_page='trophies')

# -------------------------------------------------------------
# VIDEO SHOWCASE ACTIONS
# -------------------------------------------------------------
@user_bp.route('/videos/upload', methods=['POST'])
@login_required
def upload_video():
    """Submits a speedcubing solve video link"""
    user_id = session.get('user_id')
    title = request.form.get('title', '').strip()
    video_url = request.form.get('video_url', '').strip()
    solve_time = request.form.get('solve_time', '0.0')
    method = request.form.get('method', 'CFOP').strip()
    description = request.form.get('description', '').strip()

    if title and video_url:
        CommunityModel.upload_video(user_id, title, video_url, solve_time, method, description)
        flash('Your speedcubing solve video has been published to the community showcase!', 'success')
    else:
        flash('Please provide a valid video title and video link.', 'error')
    return redirect(url_for('user.dashboard') + '#stage-videos')

@user_bp.route('/videos/like/<int:video_id>', methods=['POST'])
@login_required
def like_video(video_id):
    """Likes a video"""
    new_likes = CommunityModel.like_video(video_id)
    return jsonify({'success': True, 'likes': new_likes})

# -------------------------------------------------------------
# CHAT & GROUPS ACTIONS
# -------------------------------------------------------------
@user_bp.route('/groups/create', methods=['POST'])
@login_required
def create_group():
    """Creates a new study clan or group chat"""
    user_id = session.get('user_id')
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    passcode = request.form.get('passcode', '').strip() or None
    # The create form has no is_private control: a group with a passcode is
    # private by definition ("leave empty for public"), otherwise public.
    is_private = 1 if (request.form.get('is_private') == '1' or passcode) else 0

    if name:
        CommunityModel.create_group(name, description, is_private, passcode, user_id)
        flash(f'Group "{name}" successfully created!', 'success')
    else:
        flash('Please enter a group name.', 'error')
    return redirect(url_for('user.dashboard') + '#stage-chat')

@user_bp.route('/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    """Sends a chat message"""
    user_id = session.get('user_id')
    message = request.form.get('message', '').strip()
    group_id = request.form.get('group_id')

    try:
        group_id = int(group_id) if group_id not in (None, '') else None
    except (TypeError, ValueError):
        group_id = None

    if message:
        CommunityModel.send_message(user_id, message, group_id=group_id)
        return jsonify({'success': True, 'message': message, 'username': session.get('username')})
    return jsonify({'success': False}), 400

@user_bp.route('/chat/messages/<int:group_id>')
@login_required
def get_group_messages(group_id):
    """Fetches messages for a group"""
    msgs = CommunityModel.get_group_messages(group_id)
    return jsonify({'success': True, 'messages': msgs})

@user_bp.route('/chat/mentions')
@login_required
def get_chat_mentions():
    """Returns candidate users and clan tags for @mention autocomplete"""
    users = query_all(
        "SELECT id, username, role, avatar_color FROM users ORDER BY username ASC LIMIT 50",
        "SELECT id, username, role, avatar_color FROM users ORDER BY username ASC LIMIT 50"
    )
    clan_tags = [
        {'id': 0, 'username': 'all', 'role': 'broadcast', 'avatar_color': '#14b8a6', 'is_tag': True, 'label': 'Broadcast All Members'},
        {'id': -1, 'username': 'clan', 'role': 'group', 'avatar_color': '#06b6d4', 'is_tag': True, 'label': 'Current Clan Group'},
        {'id': -2, 'username': 'champions', 'role': 'tier', 'avatar_color': '#f59e0b', 'is_tag': True, 'label': 'Top Speedcubers'}
    ]
    return jsonify({'success': True, 'users': users or [], 'tags': clan_tags})

# -------------------------------------------------------------
# FRIENDS ACTIONS
# -------------------------------------------------------------
@user_bp.route('/friends/add', methods=['POST'])
@login_required
def add_friend():
    """Adds a speedcubing friend by username"""
    user_id = session.get('user_id')
    # The form posts "username"; also accept "friend_username" for API clients.
    friend_username = (request.form.get('username') or request.form.get('friend_username') or '').strip()
    friend = query_one(
        "SELECT id, username FROM users WHERE username = %s",
        "SELECT id, username FROM users WHERE username = ?",
        (friend_username,)
    )
    if friend and friend['id'] != user_id:
        CommunityModel.add_friend(user_id, friend['id'])
        flash(f'You are now connected with {friend["username"]}!', 'success')
    else:
        flash('User not found or you cannot add yourself as friend.', 'error')
    return redirect(url_for('user.dashboard') + '#stage-friends')

# -------------------------------------------------------------
# BLOG & COMMUNITY FEED ACTIONS
# -------------------------------------------------------------
@user_bp.route('/blogs/create', methods=['POST'])
@login_required
def create_blog_post():
    """Publishes a community blog article"""
    user_id = session.get('user_id')
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    tags = request.form.get('tags', 'CFOP,Tips').strip()

    if title and content:
        CommunityModel.create_post(user_id, title, content, tags)
        flash('Your speedcubing blog post has been published!', 'success')
    else:
        flash('Please provide both title and content for your post.', 'error')
    return redirect(url_for('user.dashboard') + '#stage-blog')

@user_bp.route('/blogs/comment', methods=['POST'])
@login_required
def add_blog_comment():
    """Adds a comment to a blog post"""
    user_id = session.get('user_id')
    post_id = request.form.get('post_id')
    comment = (request.form.get('comment') or request.form.get('content') or '').strip()

    try:
        post_id = int(post_id)
    except (TypeError, ValueError):
        post_id = 0

    if post_id and comment:
        CommunityModel.add_comment(post_id, user_id, comment)
        flash('Comment posted!', 'success')
    else:
        flash('Comment could not be posted.', 'error')
    return redirect(url_for('user.dashboard') + '#stage-blog')

@user_bp.route('/courses/complete', methods=['POST'])
@login_required
def complete_course():
    """Marks a course as completed for the current user"""
    flash('Congratulations! You have completed this speedcubing masterclass course!', 'success')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/competitions/submit', methods=['POST'])
@login_required
def submit_competition():
    """Submits a solve solution to an active competition"""
    comp_id = request.form.get('competition_id')
    solution = request.form.get('solution', '').strip()
    move_count = len(solution.split()) if solution else 0
    try:
        time_seconds = float(request.form.get('time_seconds', 0.0))
    except (TypeError, ValueError):
        time_seconds = 0.0
    user_id = session.get('user_id')

    try:
        comp_id = int(comp_id)
    except (TypeError, ValueError):
        comp_id = 0

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

# -------------------------------------------------------------
# CUSTOM CUBES WORKSHOP & GROUP CHALLENGES ACTIONS
# -------------------------------------------------------------
@user_bp.route('/custom-cubes/save', methods=['POST'])
@login_required
def save_custom_cube():
    """Saves a custom built cube blueprint"""
    user_id = session.get('user_id')
    name = request.form.get('name', '').strip() or "My Custom Puzzle"
    shape_type = request.form.get('shape_type', 'classic_3x3').strip()
    description = request.form.get('description', '').strip()
    color_scheme = request.form.get('color_scheme', '').strip()
    cube_state = request.form.get('cube_state', '').strip()
    scramble = request.form.get('scramble', '').strip()
    status = request.form.get('status', 'unsolved').strip()
    is_public = 1 if request.form.get('is_public') in ('1', 'true', 'on') else 0

    CustomCubeModel.save_cube(
        user_id=user_id,
        name=name,
        shape_type=shape_type,
        description=description,
        color_scheme=color_scheme,
        cube_state=cube_state,
        scramble=scramble,
        status=status,
        is_public=is_public
    )
    flash(f'Custom cube "{name}" successfully saved to your workshop collection!', 'success')
    return redirect(url_for('user.dashboard') + '#stage-custom-builder')

@user_bp.route('/custom-cubes/delete/<int:cube_id>', methods=['POST'])
@login_required
def delete_custom_cube(cube_id):
    """Deletes a custom cube owned by user"""
    user_id = session.get('user_id')
    CustomCubeModel.delete_cube(cube_id, user_id)
    flash('Custom puzzle deleted from your collection.', 'info')
    return redirect(url_for('user.dashboard') + '#stage-custom-builder')

@user_bp.route('/custom-cubes/challenge-group', methods=['POST'])
@login_required
def challenge_group():
    """Mentions and challenges a study clan / group to solve a custom cube problem"""
    user_id = session.get('user_id')
    cube_id = request.form.get('cube_id')
    group_id = request.form.get('group_id')
    challenge_note = request.form.get('challenge_note', '').strip()

    try:
        cube_id = int(cube_id)
        group_id = int(group_id)
    except (TypeError, ValueError):
        cube_id = 0
        group_id = 0

    if cube_id and group_id:
        CustomCubeModel.challenge_group(cube_id, group_id, user_id, challenge_note)
        flash('Puzzle challenge sent to the Clan! Clan members have been tagged & notified in chat.', 'success')
    else:
        flash('Please select both a valid cube and a target clan/group.', 'error')
    return redirect(url_for('user.dashboard') + '#stage-custom-builder')

@user_bp.route('/custom-cubes/solve-challenge/<int:challenge_id>', methods=['POST'])
@login_required
def solve_challenge(challenge_id):
    """Submits a solution algorithm for an open group challenge"""
    user_id = session.get('user_id')
    solution = request.form.get('solution', '').strip()
    if solution:
        CustomCubeModel.solve_challenge(challenge_id, user_id, solution)
        flash('Congratulations! Your solution algorithm has been verified and registered on the Clan Challenge!', 'success')
    else:
        flash('Please provide a valid solution move sequence.', 'error')
    return redirect(url_for('user.dashboard') + '#stage-custom-builder')

@user_bp.route('/custom-cubes/api/<int:cube_id>')
@login_required
def get_custom_cube_api(cube_id):
    """Fetches custom cube details for 1-click loading into the builder studio"""
    cube = CustomCubeModel.get_cube_by_id(cube_id)
    if cube:
        return jsonify({'success': True, 'cube': cube})
    return jsonify({'success': False, 'error': 'Cube not found'}), 404


