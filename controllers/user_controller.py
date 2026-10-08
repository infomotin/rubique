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

    return render_template(
        'user_dashboard.html',
        user=user,
        stats=stats,
        history=history,
        competitions=competitions,
        courses=courses,
        user_entries=user_entries,
        videos=videos,
        groups=groups,
        friends=friends,
        posts=posts
    )

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
    is_private = 1 if request.form.get('is_private') == '1' else 0
    passcode = request.form.get('passcode', '').strip() or None

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

# -------------------------------------------------------------
# FRIENDS ACTIONS
# -------------------------------------------------------------
@user_bp.route('/friends/add', methods=['POST'])
@login_required
def add_friend():
    """Adds a speedcubing friend by username"""
    user_id = session.get('user_id')
    friend_username = request.form.get('username', '').strip()
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

    if post_id and comment:
        CommunityModel.add_comment(post_id, user_id, comment)
        flash('Comment posted!', 'success')
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

