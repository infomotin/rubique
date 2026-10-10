"""
CubePermutation AI - News Feed & Social Inbox Controller (MVC Pattern)
=======================================================================
Handles the default landing experience for subscribers:
- Facebook-like News Feed with Public Posts and Game Invitations (Card Club & Chess)
- Direct 1-on-1 Inbox Messaging with Real-Time Threads
- Real-Time Notification Bell & Dropdown Dispatcher
- Universal Live Search (Posts, Invitations, Users)
- Strict Privacy Profile System (Public vs Private Profile Toggle)
"""

import os
import uuid
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from models.feed_model import FeedModel
from models.db import query_all, query_one

feed_bp = Blueprint('feed', __name__, url_prefix='/feed')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'm4v'}
FEED_UPLOAD_FOLDER = os.path.join('static', 'uploads', 'feed')
os.makedirs(FEED_UPLOAD_FOLDER, exist_ok=True)


from utils.decorators import login_required
from utils.security import sanitize_input
from services.feed_service import FeedService


# -----------------------------------------------------------------
# 1. MAIN FACEBOOK-STYLE NEWS FEED
# -----------------------------------------------------------------
@feed_bp.route('/', methods=['GET'])
@login_required
def newsfeed():
    """
    Default Subscriber Landing Page: Facebook-style News Feed.
    Features Top Navigation Bar, Live Search, Inbox, Notification Bar,
    Left Profile Card with 1-Click Privacy Toggle, Center Post/Invite Stream,
    and Right Pending Invitations & Online Members.
    """
    user_id = session['user_id']
    filter_type = request.args.get('filter', 'all')
    search_q = request.args.get('q', '').strip()
    active_inbox_id = request.args.get('inbox')

    # 1. Basic user info with privacy state
    current_user = FeedModel.get_user_basic_info(user_id, viewer_id=user_id)

    # 2. News Feed stream
    posts = FeedModel.get_newsfeed(user_id=user_id, filter_type=filter_type, query=search_q, limit=60)

    # 3. Pending game invitations for this subscriber
    pending_invitations = FeedModel.get_pending_invitations_for_user(user_id)

    # 4. User notifications & unread count
    notifications = FeedModel.get_notifications(user_id, limit=25)
    unread_notifs_count = FeedModel.get_unread_notification_count(user_id)

    # 5. Inbox conversations & unread direct messages
    inbox_threads = FeedModel.get_inbox_threads(user_id)
    unread_messages_count = FeedModel.get_unread_messages_count(user_id)

    # 6. Active chat conversation if opened directly
    active_conversation = []
    active_chat_user = None
    if active_inbox_id:
        try:
            active_chat_uid = int(active_inbox_id)
            active_conversation = FeedModel.get_conversation(user_id, active_chat_uid)
            active_chat_user = FeedModel.get_user_basic_info(active_chat_uid, viewer_id=user_id)
        except Exception:
            pass

    # 7. Community members for discovery
    all_users = query_all(
        """SELECT id, username, avatar_color, role, is_profile_private
           FROM users WHERE id != %s ORDER BY id ASC LIMIT 12""",
        """SELECT id, username, avatar_color, role, is_profile_private
           FROM users WHERE id != ? ORDER BY id ASC LIMIT 12""",
        (user_id,)
    ) or []

    return render_template(
        'feed/newsfeed.html',
        current_user=current_user,
        posts=posts,
        filter_type=filter_type,
        search_q=search_q,
        pending_invitations=pending_invitations,
        notifications=notifications,
        unread_notifs_count=unread_notifs_count,
        inbox_threads=inbox_threads,
        unread_messages_count=unread_messages_count,
        active_conversation=active_conversation,
        active_chat_user=active_chat_user,
        community_users=[dict(u) for u in all_users]
    )


# -----------------------------------------------------------------
# 2. CREATE POST & CREATE INVITATION (WITH IMAGE & VIDEO SUPPORT)
# -----------------------------------------------------------------
@feed_bp.route('/post', methods=['POST'])
@login_required
def create_post():
    """Publishes a public post, photo/video media post, or game invitation."""
    user_id = session['user_id']
    content = request.form.get('content', '').strip()
    title = request.form.get('title', '').strip()
    post_type = request.form.get('post_type', 'post')
    privacy = request.form.get('privacy', 'public')
    game_type = request.form.get('game_type') or None
    invite_code = request.form.get('invite_code') or None
    image_url = request.form.get('image_url', '').strip() or None
    video_url = request.form.get('video_url', '').strip() or None

    # Handle Image File Upload
    img_file = request.files.get('image_file')
    if img_file and img_file.filename:
        ext = img_file.filename.rsplit('.', 1)[-1].lower() if '.' in img_file.filename else ''
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            clean_filename = secure_filename(img_file.filename)
            unique_name = f"img_{uuid.uuid4().hex[:8]}_{clean_filename}"
            save_path = os.path.join(FEED_UPLOAD_FOLDER, unique_name)
            img_file.save(save_path)
            image_url = f"/static/uploads/feed/{unique_name}"

    # Handle Video File Upload
    vid_file = request.files.get('video_file')
    if vid_file and vid_file.filename:
        ext = vid_file.filename.rsplit('.', 1)[-1].lower() if '.' in vid_file.filename else ''
        if ext in ALLOWED_VIDEO_EXTENSIONS:
            clean_filename = secure_filename(vid_file.filename)
            unique_name = f"vid_{uuid.uuid4().hex[:8]}_{clean_filename}"
            save_path = os.path.join(FEED_UPLOAD_FOLDER, unique_name)
            vid_file.save(save_path)
            video_url = f"/static/uploads/feed/{unique_name}"

    if not content and not title and not image_url and not video_url:
        flash('Post content, image, or video must be provided.', 'error')
        return redirect(url_for('feed.newsfeed'))

    media_type = 'text'
    if video_url:
        media_type = 'video'
    elif image_url:
        media_type = 'image'

    post_id = FeedModel.create_post(
        user_id=user_id,
        content=content,
        title=title,
        post_type=post_type,
        privacy=privacy,
        game_type=game_type,
        invite_code=invite_code,
        image_url=image_url,
        video_url=video_url,
        media_type=media_type
    )

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'post_id': post_id,
            'image_url': image_url,
            'video_url': video_url,
            'media_type': media_type,
            'message': 'Post published successfully!'
        })

    flash('Your post has been published to the News Feed!', 'success')
    return redirect(url_for('feed.newsfeed'))


# -----------------------------------------------------------------
# 3. LIKE & COMMENT CONTROLLERS
# -----------------------------------------------------------------
@feed_bp.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    """Likes or unlikes a post."""
    user_id = session['user_id']
    result = FeedModel.toggle_like(post_id, user_id)
    return jsonify({'success': True, **result})


@feed_bp.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    """Adds a comment to a post."""
    user_id = session['user_id']
    comment_text = request.form.get('comment') or (request.json.get('comment') if request.is_json else '')
    
    if not comment_text or not comment_text.strip():
        return jsonify({'success': False, 'message': 'Comment cannot be blank.'}), 400

    comment = FeedModel.add_comment(post_id, user_id, comment_text)
    return jsonify({'success': True, 'comment': comment})


# -----------------------------------------------------------------
# 4. PRIVACY TOGGLE CONTROLLER
# -----------------------------------------------------------------
@feed_bp.route('/privacy-toggle', methods=['POST'])
@login_required
def toggle_privacy():
    """
    Toggles between Public and Private profile mode.
    When Private is ON, other users will only see username and public items.
    """
    user_id = session['user_id']
    is_private_input = None
    if request.is_json and 'is_private' in request.json:
        is_private_input = request.json.get('is_private')
    elif 'is_private' in request.form:
        is_private_input = request.form.get('is_private') in ('1', 'true', 'True')

    new_state = FeedModel.toggle_profile_privacy(user_id, is_private_input)

    status_str = "Private (Only Name & Public posts are shown to others)" if new_state else "Public (Profile details are visible to all subscribers)"
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'is_private': new_state, 'message': f"Profile is now {status_str}."})

    flash(f"Profile privacy updated: Your profile is now {status_str}.", 'success')
    return redirect(url_for('feed.newsfeed'))


# -----------------------------------------------------------------
# 5. USER BASIC INFO API (RESPECTING PRIVACY)
# -----------------------------------------------------------------
@feed_bp.route('/api/user/<int:target_user_id>', methods=['GET'])
@login_required
def get_user_info(target_user_id):
    """
    Returns user basic info.
    If target user set profile to Private, returns only username and public items.
    """
    user_id = session['user_id']
    info = FeedModel.get_user_basic_info(target_user_id, viewer_id=user_id)
    if not info:
        return jsonify({'success': False, 'message': 'User not found.'}), 404
    return jsonify({'success': True, 'user': info})


# -----------------------------------------------------------------
# 6. UNIVERSAL SEARCH API (POSTS, INVITATIONS, USERS)
# -----------------------------------------------------------------
@feed_bp.route('/api/search', methods=['GET'])
@login_required
def search_api():
    """Universal search across Posts, Invitations, and Users."""
    user_id = session['user_id']
    q = request.args.get('q', '').strip()
    results = FeedModel.universal_search(q, viewer_id=user_id)
    return jsonify({'success': True, 'query': q, 'results': results})


# -----------------------------------------------------------------
# 7. NOTIFICATIONS API
# -----------------------------------------------------------------
@feed_bp.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications_api():
    """Fetches user notifications and unread badge count."""
    user_id = session['user_id']
    notifications = FeedModel.get_notifications(user_id, limit=30)
    unread_count = FeedModel.get_unread_notification_count(user_id)
    return jsonify({'success': True, 'notifications': notifications, 'unread_count': unread_count})


@feed_bp.route('/api/notifications/read', methods=['POST'])
@login_required
def mark_read_api():
    """Marks notifications as read."""
    user_id = session['user_id']
    FeedModel.mark_notifications_as_read(user_id)
    return jsonify({'success': True})


# -----------------------------------------------------------------
# 8. INBOX & DIRECT MESSAGING API
# -----------------------------------------------------------------
@feed_bp.route('/api/inbox/threads', methods=['GET'])
@login_required
def get_threads_api():
    """Fetches list of inbox conversation threads."""
    user_id = session['user_id']
    threads = FeedModel.get_inbox_threads(user_id)
    unread_total = FeedModel.get_unread_messages_count(user_id)
    return jsonify({'success': True, 'threads': threads, 'unread_total': unread_total})


@feed_bp.route('/api/inbox/messages', methods=['GET'])
@login_required
def get_messages_api():
    """Fetches conversation messages between current user and target user."""
    user_id = session['user_id']
    contact_id = request.args.get('with_user_id')
    if not contact_id:
        return jsonify({'success': False, 'message': 'with_user_id is required'}), 400

    messages = FeedModel.get_conversation(user_id, int(contact_id))
    contact_info = FeedModel.get_user_basic_info(int(contact_id), viewer_id=user_id)
    return jsonify({'success': True, 'messages': messages, 'contact': contact_info})


@feed_bp.route('/api/inbox/send', methods=['POST'])
@login_required
def send_message_api():
    """Sends a 1-on-1 direct message."""
    user_id = session['user_id']
    data = request.get_json(silent=True) or request.form
    receiver_id = data.get('receiver_id')
    message_text = data.get('message', '').strip()

    if not receiver_id or not message_text:
        return jsonify({'success': False, 'message': 'Receiver and message text are required.'}), 400

    msg = FeedModel.send_direct_message(user_id, int(receiver_id), message_text)
    return jsonify({'success': True, 'message': msg})
