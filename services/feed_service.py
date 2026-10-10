"""
CubePermutation AI - Newsfeed & Social Domain Service
=====================================================
Encapsulates subscriber news feed streams, media verification, direct inbox
conversations, game invitations, notification dispatching, and profile privacy guards.

Easy Description:
- Aggregates community posts, card game invites, and chess challenges for subscribers.
- Safely handles image and video file uploads.
- Strictly guards user privacy by masking personal information if a user sets their profile to private.
"""

import os
import uuid
from typing import Dict, Any, Optional, List
from werkzeug.utils import secure_filename
from models.feed_model import FeedModel
from models.db import query_all
from utils.security import sanitize_input

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'm4v'}
FEED_UPLOAD_FOLDER = os.path.join('static', 'uploads', 'feed')


class FeedService:
    """
    Social Feed & Direct Messaging Domain Service
    """

    @staticmethod
    def allowed_file(filename: str, allowed_extensions: set) -> bool:
        """
        Validates safe file extensions for user-uploaded media.
        """
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def get_feed_overview(user_id: int, filter_type: str = 'all', search_q: str = '', active_inbox_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches comprehensive newsfeed bundle for active subscriber session.

        Easy Description:
        Loads the subscriber's personal profile card, posts stream, pending game invites, and inbox threads.
        """
        os.makedirs(FEED_UPLOAD_FOLDER, exist_ok=True)

        current_user = FeedModel.get_user_basic_info(user_id, viewer_id=user_id)
        posts = FeedModel.get_newsfeed(user_id=user_id, filter_type=filter_type, query=search_q, limit=60)
        pending_invitations = FeedModel.get_pending_invitations_for_user(user_id)
        notifications = FeedModel.get_notifications(user_id, limit=25)
        unread_notifs_count = FeedModel.get_unread_notification_count(user_id)
        inbox_threads = FeedModel.get_inbox_threads(user_id)
        unread_messages_count = FeedModel.get_unread_messages_count(user_id)

        active_conversation = []
        active_chat_user = None
        if active_inbox_id:
            try:
                active_chat_uid = int(active_inbox_id)
                active_conversation = FeedModel.get_conversation(user_id, active_chat_uid)
                active_chat_user = FeedModel.get_user_basic_info(active_chat_uid, viewer_id=user_id)
            except Exception:
                pass

        all_users = query_all(
            """SELECT id, username, avatar_color, role, is_profile_private
               FROM users WHERE id != %s ORDER BY id ASC LIMIT 12""",
            """SELECT id, username, avatar_color, role, is_profile_private
               FROM users WHERE id != ? ORDER BY id ASC LIMIT 12""",
            (user_id,)
        ) or []

        return {
            'current_user': current_user,
            'posts': posts,
            'pending_invitations': pending_invitations,
            'notifications': notifications,
            'unread_notifs_count': unread_notifs_count,
            'inbox_threads': inbox_threads,
            'unread_messages_count': unread_messages_count,
            'active_conversation': active_conversation,
            'active_chat_user': active_chat_user,
            'all_users': all_users,
        }

    @staticmethod
    def create_post(
        user_id: int,
        title: str,
        content: str,
        post_type: str = 'post',
        game_type: Optional[str] = None,
        invite_code: Optional[str] = None,
        privacy: str = 'public',
        image_file=None,
        video_file=None
    ) -> Optional[int]:
        """
        Sanitizes and publishes a community feed post or game invitation with optional media attachments.

        Easy Description:
        Cleans user text, verifies uploaded photos/videos, and saves the new post to the community feed.
        """
        os.makedirs(FEED_UPLOAD_FOLDER, exist_ok=True)
        sanitized_title = sanitize_input(title or '')
        sanitized_content = sanitize_input(content or '')

        image_url = None
        if image_file and image_file.filename:
            if FeedService.allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                ext = secure_filename(image_file.filename).rsplit('.', 1)[1].lower()
                uniq_img = f"img_{uuid.uuid4().hex[:8]}.{ext}"
                target_path = os.path.join(FEED_UPLOAD_FOLDER, uniq_img)
                image_file.save(target_path)
                image_url = f"/static/uploads/feed/{uniq_img}"

        video_url = None
        if video_file and video_file.filename:
            if FeedService.allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                ext = secure_filename(video_file.filename).rsplit('.', 1)[1].lower()
                uniq_vid = f"vid_{uuid.uuid4().hex[:8]}.{ext}"
                target_path = os.path.join(FEED_UPLOAD_FOLDER, uniq_vid)
                video_file.save(target_path)
                video_url = f"/static/uploads/feed/{uniq_vid}"

        post_id = FeedModel.create_post(
            user_id=user_id,
            title=sanitized_title,
            content=sanitized_content,
            post_type=post_type or 'post',
            game_type=game_type or None,
            invite_code=invite_code or None,
            privacy=privacy or 'public',
            image_url=image_url,
            video_url=video_url
        )
        return post_id

    @staticmethod
    def send_direct_message(sender_id: int, recipient_id: int, message_text: str) -> Optional[int]:
        """
        Sanitizes and dispatches a direct 1-to-1 inbox message and triggers notifications.

        Easy Description:
        Sends a private message to another member and alerts them with a notification.
        """
        if not message_text or not recipient_id or sender_id == recipient_id:
            return None
        clean_text = sanitize_input(message_text)
        return FeedModel.send_direct_message(sender_id, recipient_id, clean_text)

    @staticmethod
    def search_all(query: str, viewer_id: int) -> Dict[str, Any]:
        """
        Executes multi-domain search across posts, game invitations, and users with privacy filtering.

        Easy Description:
        Finds posts, active game tables, and community members matching the search query.
        """
        clean_query = (query or '').strip()
        return FeedModel.universal_search(clean_query, viewer_id=viewer_id)
