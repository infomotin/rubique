"""
CubePermutation AI - News Feed, Social Inbox & Privacy Model (MVC Pattern)
=============================================================================
Handles Facebook-style News Feed, Public Posts, Game Invitations,
Direct 1-on-1 Inbox Messaging, Real-time Notification Dispatch, Universal Search,
and Strict Privacy Access Control (Public vs Private Profiles).
"""

from datetime import datetime
from models.db import query_one, query_all, execute_insert, execute_update


class FeedModel:

    # -------------------------------------------------------------
    # 1. NEWS FEED & POSTS
    # -------------------------------------------------------------
    @staticmethod
    def get_newsfeed(user_id=None, filter_type='all', query=None, limit=50):
        """
        Fetches feed stream: Public Posts and Game Invitations.
        Includes author privacy checks, like state, and comments.
        """
        where_clauses = ["(b.privacy = 'public' OR b.user_id = %s)"]
        where_clauses_sqlite = ["(b.privacy = 'public' OR b.user_id = ?)"]
        params = [user_id or 0]

        if filter_type == 'invitations':
            where_clauses.append("b.post_type IN ('card_invite', 'chess_invite', 'invite')")
            where_clauses_sqlite.append("b.post_type IN ('card_invite', 'chess_invite', 'invite')")
        elif filter_type == 'posts':
            where_clauses.append("b.post_type = 'post'")
            where_clauses_sqlite.append("b.post_type = 'post'")
        elif filter_type == 'mine' and user_id:
            where_clauses.append("b.user_id = %s")
            where_clauses_sqlite.append("b.user_id = ?")
            params.append(user_id)

        if query:
            q_like = f"%{query.strip()}%"
            where_clauses.append("(b.content LIKE %s OR b.title LIKE %s OR b.tags LIKE %s OR b.game_type LIKE %s OR u.username LIKE %s)")
            where_clauses_sqlite.append("(b.content LIKE ? OR b.title LIKE ? OR b.tags LIKE ? OR b.game_type LIKE ? OR u.username LIKE ?)")
            params.extend([q_like, q_like, q_like, q_like, q_like])

        sql_where = " AND ".join(where_clauses)
        sql_where_sqlite = " AND ".join(where_clauses_sqlite)

        mysql_sql = f"""
            SELECT b.*, u.username, u.avatar_color, u.role, u.is_profile_private,
                   (SELECT COUNT(*) FROM blog_comments c WHERE c.post_id = b.id) as comment_count
            FROM blog_posts b
            JOIN users u ON b.user_id = u.id
            WHERE {sql_where}
            ORDER BY b.created_at DESC LIMIT %s
        """
        sqlite_sql = f"""
            SELECT b.*, u.username, u.avatar_color, u.role, u.is_profile_private,
                   (SELECT COUNT(*) FROM blog_comments c WHERE c.post_id = b.id) as comment_count
            FROM blog_posts b
            JOIN users u ON b.user_id = u.id
            WHERE {sql_where_sqlite}
            ORDER BY b.created_at DESC LIMIT ?
        """
        all_params = list(params) + [limit]
        posts = query_all(mysql_sql, sqlite_sql, tuple(all_params)) or []

        # Enrich each post
        results = []
        for p in posts:
            post = dict(p)
            post_id = post['id']

            # Check if viewer liked this post
            post['liked_by_me'] = False
            if user_id:
                like_row = query_one(
                    "SELECT id FROM post_likes WHERE post_id = %s AND user_id = %s",
                    "SELECT id FROM post_likes WHERE post_id = ? AND user_id = ?",
                    (post_id, user_id)
                )
                post['liked_by_me'] = bool(like_row)

            # Fetch recent comments
            comments = query_all(
                """SELECT c.*, u.username, u.avatar_color, u.is_profile_private
                   FROM blog_comments c
                   JOIN users u ON c.user_id = u.id
                   WHERE c.post_id = %s
                   ORDER BY c.created_at ASC LIMIT 10""",
                """SELECT c.*, u.username, u.avatar_color, u.is_profile_private
                   FROM blog_comments c
                   JOIN users u ON c.user_id = u.id
                   WHERE c.post_id = ?
                   ORDER BY c.created_at ASC LIMIT 10""",
                (post_id,)
            ) or []
            post['comments'] = [dict(c) for c in comments]

            # Privacy indication
            is_priv = bool(post.get('is_profile_private'))
            post['author_is_private'] = is_priv and (post['user_id'] != user_id)

            # Media formatting for Images and Videos
            vid = post.get('video_url')
            if vid:
                vid_str = str(vid).strip()
                if 'youtube.com' in vid_str or 'youtu.be' in vid_str:
                    post['is_youtube'] = True
                    import re
                    m1 = re.search(r'v=([a-zA-Z0-9_-]+)', vid_str)
                    m2 = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', vid_str)
                    vid_code = m1.group(1) if m1 else (m2.group(1) if m2 else '')
                    post['video_embed_url'] = f"https://www.youtube.com/embed/{vid_code}" if vid_code else vid_str
                else:
                    post['is_youtube'] = False
                    post['video_embed_url'] = vid_str
            else:
                post['is_youtube'] = False
                post['video_embed_url'] = None

            results.append(post)

        return results

    @staticmethod
    def create_post(user_id, content, title='', post_type='post', privacy='public',
                    game_type=None, invite_code=None, target_group_id=None,
                    image_url=None, video_url=None, media_type=None):
        """Creates a feed post, photo/video media post, or game invitation post."""
        clean_content = (content or '').strip()
        clean_title = (title or '').strip()
        clean_img = (image_url or '').strip() or None
        clean_vid = (video_url or '').strip() or None

        if not media_type:
            if clean_vid:
                media_type = 'video'
            elif clean_img:
                media_type = 'image'
            else:
                media_type = 'text'

        if not clean_title:
            if post_type == 'card_invite':
                game_label = (game_type or 'Card Game').replace('_', ' ').title()
                clean_title = f"Invitation: Join {game_label} Match"
            elif post_type == 'chess_invite':
                clean_title = "Invitation: GoChess 3D Battle Arena Challenge"
            elif clean_content:
                clean_title = clean_content[:40] + ('...' if len(clean_content) > 40 else '')
            elif clean_vid:
                clean_title = "Solve Video Breakdown"
            elif clean_img:
                clean_title = "Speedcubing & Game Snapshot"

        post_id = execute_insert(
            """INSERT INTO blog_posts (user_id, title, content, tags, likes, post_type, privacy, game_type, invite_code, target_group_id, image_url, video_url, media_type)
               VALUES (%s, %s, %s, %s, 0, %s, %s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO blog_posts (user_id, title, content, tags, likes, post_type, privacy, game_type, invite_code, target_group_id, image_url, video_url, media_type)
               VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, clean_title, clean_content, post_type, post_type, privacy, game_type, invite_code, target_group_id, clean_img, clean_vid, media_type)
        )

        # If it's a game invitation, notify all active subscribers!
        if post_type in ('card_invite', 'chess_invite'):
            author = query_one(
                "SELECT username FROM users WHERE id = %s",
                "SELECT username FROM users WHERE id = ?",
                (user_id,)
            )
            author_name = author['username'] if author else 'A player'
            FeedModel.broadcast_notification(
                actor_id=user_id,
                notif_type='invite',
                title=f"{author_name} posted a {post_type.replace('_', ' ').title()}!",
                content=clean_title,
                link=f"/feed#post-{post_id}"
            )

        return post_id

    @staticmethod
    def toggle_like(post_id, user_id):
        """Likes or unlikes a post. Returns dict with status and count."""
        existing = query_one(
            "SELECT id FROM post_likes WHERE post_id = %s AND user_id = %s",
            "SELECT id FROM post_likes WHERE post_id = ? AND user_id = ?",
            (post_id, user_id)
        )
        if existing:
            execute_update(
                "DELETE FROM post_likes WHERE id = %s",
                "DELETE FROM post_likes WHERE id = ?",
                (existing['id'],)
            )
            execute_update(
                "UPDATE blog_posts SET likes = CASE WHEN likes > 0 THEN likes - 1 ELSE 0 END WHERE id = %s",
                "UPDATE blog_posts SET likes = CASE WHEN likes > 0 THEN likes - 1 ELSE 0 END WHERE id = ?",
                (post_id,)
            )
            liked = False
        else:
            execute_insert(
                "INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)",
                "INSERT INTO post_likes (post_id, user_id) VALUES (?, ?)",
                (post_id, user_id)
            )
            execute_update(
                "UPDATE blog_posts SET likes = likes + 1 WHERE id = %s",
                "UPDATE blog_posts SET likes = likes + 1 WHERE id = ?",
                (post_id,)
            )
            liked = True

            # Send notification to post author if not self
            post = query_one(
                "SELECT user_id, title FROM blog_posts WHERE id = %s",
                "SELECT user_id, title FROM blog_posts WHERE id = ?",
                (post_id,)
            )
            if post and post['user_id'] != user_id:
                actor = query_one(
                    "SELECT username FROM users WHERE id = %s",
                    "SELECT username FROM users WHERE id = ?",
                    (user_id,)
                )
                actor_name = actor['username'] if actor else 'Someone'
                FeedModel.create_notification(
                    user_id=post['user_id'],
                    actor_id=user_id,
                    notif_type='like',
                    title=f"{actor_name} liked your post",
                    content=f"{actor_name} liked: \"{post['title'][:50]}\"",
                    link=f"/feed#post-{post_id}"
                )

        row = query_one(
            "SELECT likes FROM blog_posts WHERE id = %s",
            "SELECT likes FROM blog_posts WHERE id = ?",
            (post_id,)
        )
        likes_count = row['likes'] if row and 'likes' in row else (1 if liked else 0)
        return {'liked': liked, 'likes_count': likes_count}

    @staticmethod
    def add_comment(post_id, user_id, comment_text):
        """Adds a comment to a post and notifies the post author."""
        clean_text = (comment_text or '').strip()
        if not clean_text:
            return None

        comment_id = execute_insert(
            "INSERT INTO blog_comments (post_id, user_id, comment) VALUES (%s, %s, %s)",
            "INSERT INTO blog_comments (post_id, user_id, comment) VALUES (?, ?, ?)",
            (post_id, user_id, clean_text)
        )

        # Notify post author
        post = query_one(
            "SELECT user_id, title FROM blog_posts WHERE id = %s",
            "SELECT user_id, title FROM blog_posts WHERE id = ?",
            (post_id,)
        )
        if post and post['user_id'] != user_id:
            actor = query_one(
                "SELECT username FROM users WHERE id = %s",
                "SELECT username FROM users WHERE id = ?",
                (user_id,)
            )
            actor_name = actor['username'] if actor else 'Someone'
            FeedModel.create_notification(
                user_id=post['user_id'],
                actor_id=user_id,
                notif_type='comment',
                title=f"{actor_name} commented on your post",
                content=f"\"{clean_text[:60]}\"",
                link=f"/feed#post-{post_id}"
            )

        u = query_one(
            "SELECT username, avatar_color FROM users WHERE id = %s",
            "SELECT username, avatar_color FROM users WHERE id = ?",
            (user_id,)
        )
        return {
            'id': comment_id,
            'post_id': post_id,
            'user_id': user_id,
            'comment': clean_text,
            'username': u['username'] if u else 'Anonymous',
            'avatar_color': u['avatar_color'] if u else '#818cf8',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    # -------------------------------------------------------------
    # 2. PRIVACY CONTROLS & BASIC USER INFO
    # -------------------------------------------------------------
    @staticmethod
    def toggle_profile_privacy(user_id, is_private=None):
        """Toggles or sets is_profile_private for a user (1=private, 0=public)."""
        current = query_one(
            "SELECT is_profile_private FROM users WHERE id = %s",
            "SELECT is_profile_private FROM users WHERE id = ?",
            (user_id,)
        )
        curr_val = int(current['is_profile_private'] or 0) if current else 0
        new_val = (1 if is_private else 0) if is_private is not None else (0 if curr_val == 1 else 1)

        execute_update(
            "UPDATE users SET is_profile_private = %s WHERE id = %s",
            "UPDATE users SET is_profile_private = ? WHERE id = ?",
            (new_val, user_id)
        )
        return bool(new_val)

    @staticmethod
    def get_user_basic_info(user_id, viewer_id=None):
        """
        Fetches user basic info.
        If user profile is set to Private (is_profile_private=1) and viewer != user:
        ONLY returns Name/Username, Avatar, and Public info. Hides private details.
        """
        u = query_one(
            """SELECT id, username, email, role, bio, avatar_color, country,
                      main_cube, preferred_method, pb_single, pb_ao5, date_of_birth,
                      is_profile_private, created_at
               FROM users WHERE id = %s""",
            """SELECT id, username, email, role, bio, avatar_color, country,
                      main_cube, preferred_method, pb_single, pb_ao5, date_of_birth,
                      is_profile_private, created_at
               FROM users WHERE id = ?""",
            (user_id,)
        )
        if not u:
            return None

        user_data = dict(u)
        is_private = bool(user_data.get('is_profile_private', 0))
        is_owner = (viewer_id and int(viewer_id) == int(user_id))

        # Count public posts
        pub_posts = query_one(
            "SELECT COUNT(*) c FROM blog_posts WHERE user_id = %s AND privacy = 'public'",
            "SELECT COUNT(*) c FROM blog_posts WHERE user_id = ? AND privacy = 'public'",
            (user_id,)
        )
        user_data['public_posts_count'] = int(pub_posts['c'] if pub_posts else 0)

        # Total solves count
        solves_row = query_one(
            "SELECT COUNT(*) c FROM solves WHERE user_id = %s",
            "SELECT COUNT(*) c FROM solves WHERE user_id = ?",
            (user_id,)
        )
        user_data['total_solves'] = int(solves_row['c'] if solves_row else 0)

        # Card wallet balance
        wallet_row = query_one(
            "SELECT balance FROM club_wallets WHERE user_id = %s",
            "SELECT balance FROM club_wallets WHERE user_id = ?",
            (user_id,)
        )
        user_data['coins_balance'] = int(wallet_row['balance']) if wallet_row and wallet_row.get('balance') is not None else 1000

        # Privacy Redaction Enforcement
        if is_private and not is_owner:
            user_data['is_private_view'] = True
            user_data['bio'] = "🔒 This subscriber's profile is set to Private."
            user_data['email'] = "[Hidden - Private Profile]"
            user_data['date_of_birth'] = "[Hidden]"
            user_data['country'] = "[Hidden]"
            user_data['main_cube'] = "[Hidden]"
            user_data['preferred_method'] = "[Hidden]"
            user_data['pb_single'] = "[Hidden]"
            user_data['pb_ao5'] = "[Hidden]"
            user_data['total_solves'] = "[Hidden]"
            user_data['coins_balance'] = "[Hidden]"
        else:
            user_data['is_private_view'] = False

        return user_data

    # -------------------------------------------------------------
    # 3. NOTIFICATIONS SYSTEM
    # -------------------------------------------------------------
    @staticmethod
    def create_notification(user_id, actor_id, notif_type, title, content, link=None):
        """Creates an in-app notification for a user."""
        return execute_insert(
            """INSERT INTO notifications (user_id, actor_id, notif_type, title, content, link, is_read)
               VALUES (%s, %s, %s, %s, %s, %s, 0)""",
            """INSERT INTO notifications (user_id, actor_id, notif_type, title, content, link, is_read)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (user_id, actor_id, notif_type, title, content, link)
        )

    @staticmethod
    def broadcast_notification(actor_id, notif_type, title, content, link=None):
        """Broadcasts a notification to all other active subscribers."""
        users = query_all(
            "SELECT id FROM users WHERE id != %s LIMIT 100",
            "SELECT id FROM users WHERE id != ? LIMIT 100",
            (actor_id,)
        ) or []
        for u in users:
            uid = u['id'] if isinstance(u, dict) else u[0]
            FeedModel.create_notification(uid, actor_id, notif_type, title, content, link)

    @staticmethod
    def get_notifications(user_id, limit=25):
        """Fetches notifications for a user."""
        rows = query_all(
            """SELECT n.*, u.username as actor_name, u.avatar_color as actor_color
               FROM notifications n
               LEFT JOIN users u ON n.actor_id = u.id
               WHERE n.user_id = %s
               ORDER BY n.created_at DESC LIMIT %s""",
            """SELECT n.*, u.username as actor_name, u.avatar_color as actor_color
               FROM notifications n
               LEFT JOIN users u ON n.actor_id = u.id
               WHERE n.user_id = ?
               ORDER BY n.created_at DESC LIMIT ?""",
            (user_id, limit)
        ) or []
        return [dict(r) for r in rows]

    @staticmethod
    def get_unread_notification_count(user_id):
        """Returns number of unread notifications."""
        row = query_one(
            "SELECT COUNT(*) c FROM notifications WHERE user_id = %s AND is_read = 0",
            "SELECT COUNT(*) c FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,)
        )
        return int(row['c'] if row else 0)

    @staticmethod
    def mark_notifications_as_read(user_id):
        """Marks all notifications for a user as read."""
        execute_update(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s",
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
            (user_id,)
        )
        return True

    # -------------------------------------------------------------
    # 4. INBOX & DIRECT 1-ON-1 MESSAGING
    # -------------------------------------------------------------
    @staticmethod
    def get_inbox_threads(user_id):
        """
        Fetches active conversation threads with other users.
        Shows other user's info, latest message, and unread count.
        """
        # Discover all unique peers
        sql = """
            SELECT DISTINCT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as contact_id
            FROM chat_messages
            WHERE (sender_id = %s OR receiver_id = %s)
              AND group_id IS NULL AND receiver_id IS NOT NULL
        """
        sql_sqlite = """
            SELECT DISTINCT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as contact_id
            FROM chat_messages
            WHERE (sender_id = ? OR receiver_id = ?)
              AND group_id IS NULL AND receiver_id IS NOT NULL
        """
        rows = query_all(sql, sql_sqlite, (user_id, user_id, user_id)) or []
        threads = []

        for r in rows:
            cid = r['contact_id'] if isinstance(r, dict) else r[0]
            if not cid or int(cid) == int(user_id):
                continue

            contact_user = query_one(
                "SELECT id, username, avatar_color, is_profile_private FROM users WHERE id = %s",
                "SELECT id, username, avatar_color, is_profile_private FROM users WHERE id = ?",
                (cid,)
            )
            if not contact_user:
                continue

            # Latest message
            last_msg = query_one(
                """SELECT message, created_at, sender_id
                   FROM chat_messages
                   WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s))
                     AND group_id IS NULL
                   ORDER BY created_at DESC LIMIT 1""",
                """SELECT message, created_at, sender_id
                   FROM chat_messages
                   WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
                     AND group_id IS NULL
                   ORDER BY created_at DESC LIMIT 1""",
                (user_id, cid, cid, user_id)
            )

            # Unread count from this contact
            unread = query_one(
                """SELECT COUNT(*) c FROM chat_messages
                   WHERE sender_id = %s AND receiver_id = %s AND is_read = 0 AND group_id IS NULL""",
                """SELECT COUNT(*) c FROM chat_messages
                   WHERE sender_id = ? AND receiver_id = ? AND is_read = 0 AND group_id IS NULL""",
                (cid, user_id)
            )

            threads.append({
                'contact_id': cid,
                'contact_username': contact_user['username'],
                'contact_avatar': contact_user['avatar_color'] or '#818cf8',
                'is_contact_private': bool(contact_user.get('is_profile_private')),
                'last_message': last_msg['message'] if last_msg else '',
                'last_time': last_msg['created_at'] if last_msg else '',
                'is_outgoing': bool(last_msg and last_msg['sender_id'] == user_id),
                'unread_count': int(unread['c'] if unread else 0)
            })

        # Sort threads by latest message time
        threads.sort(key=lambda x: str(x['last_time']), reverse=True)
        return threads

    @staticmethod
    def get_conversation(user_id, other_user_id, limit=60):
        """Fetches full chat history between two users and marks as read."""
        messages = query_all(
            """SELECT m.*, u.username, u.avatar_color
               FROM chat_messages m
               JOIN users u ON m.sender_id = u.id
               WHERE ((m.sender_id = %s AND m.receiver_id = %s) OR (m.sender_id = %s AND m.receiver_id = %s))
                 AND m.group_id IS NULL
               ORDER BY m.created_at ASC LIMIT %s""",
            """SELECT m.*, u.username, u.avatar_color
               FROM chat_messages m
               JOIN users u ON m.sender_id = u.id
               WHERE ((m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?))
                 AND m.group_id IS NULL
               ORDER BY m.created_at ASC LIMIT ?""",
            (user_id, other_user_id, other_user_id, user_id, limit)
        ) or []

        # Mark messages received as read
        execute_update(
            "UPDATE chat_messages SET is_read = 1 WHERE sender_id = %s AND receiver_id = %s AND group_id IS NULL",
            "UPDATE chat_messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ? AND group_id IS NULL",
            (other_user_id, user_id)
        )

        return [dict(m) for m in messages]

    @staticmethod
    def send_direct_message(sender_id, receiver_id, message_text):
        """Sends a 1-on-1 direct message and dispatches a notification."""
        clean_text = (message_text or '').strip()
        if not clean_text:
            return None

        msg_id = execute_insert(
            """INSERT INTO chat_messages (sender_id, receiver_id, message, is_read)
               VALUES (%s, %s, %s, 0)""",
            """INSERT INTO chat_messages (sender_id, receiver_id, message, is_read)
               VALUES (?, ?, ?, 0)""",
            (sender_id, receiver_id, clean_text)
        )

        # Notify receiver
        sender = query_one(
            "SELECT username FROM users WHERE id = %s",
            "SELECT username FROM users WHERE id = ?",
            (sender_id,)
        )
        sender_name = sender['username'] if sender else 'Subscriber'
        FeedModel.create_notification(
            user_id=receiver_id,
            actor_id=sender_id,
            notif_type='message',
            title=f"New Message from {sender_name}",
            content=clean_text[:60] + ('...' if len(clean_text) > 60 else ''),
            link=f"/feed?inbox={sender_id}"
        )

        return {
            'id': msg_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': clean_text,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    @staticmethod
    def get_unread_messages_count(user_id):
        """Counts total unread direct messages across all senders."""
        row = query_one(
            "SELECT COUNT(*) c FROM chat_messages WHERE receiver_id = %s AND is_read = 0 AND group_id IS NULL",
            "SELECT COUNT(*) c FROM chat_messages WHERE receiver_id = ? AND is_read = 0 AND group_id IS NULL",
            (user_id,)
        )
        return int(row['c'] if row else 0)

    # -------------------------------------------------------------
    # 5. PENDING INVITATIONS (CARD CLUB & CHESS)
    # -------------------------------------------------------------
    @staticmethod
    def get_pending_invitations_for_user(user_id):
        """
        Returns all invitations actionable by this subscriber:
        - Card Club group invitations
        - GoChess 3D battle invitations
        - Public game matches open for joining
        """
        invites = []

        # Card Club direct invites
        try:
            club_rows = query_all(
                """SELECT i.id, i.group_id, i.token, i.created_at, g.name as title,
                          g.invite_code, u.username as inviter_name
                   FROM club_invites i
                   JOIN club_groups g ON g.id = i.group_id
                   LEFT JOIN users u ON u.id = i.created_by
                   WHERE i.invitee_user_id = %s AND i.status = 'pending'
                   ORDER BY i.created_at DESC""",
                """SELECT i.id, i.group_id, i.token, i.created_at, g.name as title,
                          g.invite_code, u.username as inviter_name
                   FROM club_invites i
                   JOIN club_groups g ON g.id = i.group_id
                   LEFT JOIN users u ON u.id = i.created_by
                   WHERE i.invitee_user_id = ? AND i.status = 'pending'
                   ORDER BY i.created_at DESC""",
                (user_id,)
            ) or []
            for r in club_rows:
                inv = dict(r)
                inv['type'] = 'card_club'
                inv['badge'] = 'Card Club Room'
                inv['icon'] = 'fa-solid fa-cards'
                inv['action_url'] = f"/club/join?invite={inv.get('invite_code', '')}"
                invites.append(inv)
        except Exception:
            pass

        # Chess direct invitations
        try:
            chess_rows = query_all(
                """SELECT i.id, i.game_id, i.message, i.created_at, u.username as inviter_name
                   FROM chess_invitations i
                   JOIN users u ON u.id = i.from_user_id
                   WHERE i.to_user_id = %s AND i.status = 'pending'
                   ORDER BY i.created_at DESC""",
                """SELECT i.id, i.game_id, i.message, i.created_at, u.username as inviter_name
                   FROM chess_invitations i
                   JOIN users u ON u.id = i.from_user_id
                   WHERE i.to_user_id = ? AND i.status = 'pending'
                   ORDER BY i.created_at DESC""",
                (user_id,)
            ) or []
            for r in chess_rows:
                inv = dict(r)
                inv['type'] = 'chess'
                inv['badge'] = 'GoChess 3D Duel'
                inv['icon'] = 'fa-solid fa-chess-knight'
                inv['title'] = inv.get('message') or f"Battle vs {inv.get('inviter_name')}"
                inv['action_url'] = f"/chess"
                invites.append(inv)
        except Exception:
            pass

        return invites

    # -------------------------------------------------------------
    # 6. UNIVERSAL SEARCH (POSTS, INVITATIONS, USERS)
    # -------------------------------------------------------------
    @staticmethod
    def universal_search(query_str, viewer_id=None):
        """
        Searches Posts, Invitations, and Users.
        Strictly applies privacy rules:
        If user profile is private, only displays name and public information.
        """
        q = (query_str or '').strip()
        if not q:
            return {'posts': [], 'invitations': [], 'users': []}

        q_like = f"%{q}%"

        # 1. Search Posts
        posts_rows = query_all(
            """SELECT b.*, u.username, u.avatar_color, u.is_profile_private
               FROM blog_posts b
               JOIN users u ON b.user_id = u.id
               WHERE b.privacy = 'public'
                 AND (b.title LIKE %s OR b.content LIKE %s OR b.tags LIKE %s)
               ORDER BY b.created_at DESC LIMIT 15""",
            """SELECT b.*, u.username, u.avatar_color, u.is_profile_private
               FROM blog_posts b
               JOIN users u ON b.user_id = u.id
               WHERE b.privacy = 'public'
                 AND (b.title LIKE ? OR b.content LIKE ? OR b.tags LIKE ?)
               ORDER BY b.created_at DESC LIMIT 15""",
            (q_like, q_like, q_like)
        ) or []

        # 2. Search Invitations
        invites_rows = query_all(
            """SELECT b.*, u.username, u.avatar_color
               FROM blog_posts b
               JOIN users u ON b.user_id = u.id
               WHERE b.privacy = 'public'
                 AND b.post_type IN ('card_invite', 'chess_invite', 'invite')
                 AND (b.title LIKE %s OR b.content LIKE %s OR b.game_type LIKE %s OR b.invite_code LIKE %s)
               ORDER BY b.created_at DESC LIMIT 15""",
            """SELECT b.*, u.username, u.avatar_color
               FROM blog_posts b
               JOIN users u ON b.user_id = u.id
               WHERE b.privacy = 'public'
                 AND b.post_type IN ('card_invite', 'chess_invite', 'invite')
                 AND (b.title LIKE ? OR b.content LIKE ? OR b.game_type LIKE ? OR b.invite_code LIKE ?)
               ORDER BY b.created_at DESC LIMIT 15""",
            (q_like, q_like, q_like, q_like)
        ) or []

        # 3. Search Users (with privacy protection)
        users_rows = query_all(
            """SELECT id, username, bio, avatar_color, role, is_profile_private
               FROM users
               WHERE username LIKE %s OR bio LIKE %s
               LIMIT 20""",
            """SELECT id, username, bio, avatar_color, role, is_profile_private
               FROM users
               WHERE username LIKE ? OR bio LIKE ?
               LIMIT 20""",
            (q_like, q_like)
        ) or []

        sanitized_users = []
        for u in users_rows:
            usr = dict(u)
            uid = usr['id']
            is_priv = bool(usr.get('is_profile_private', 0))
            is_me = (viewer_id and int(viewer_id) == int(uid))

            if is_priv and not is_me:
                sanitized_users.append({
                    'id': uid,
                    'username': usr['username'],
                    'avatar_color': usr['avatar_color'] or '#818cf8',
                    'role': usr['role'],
                    'bio': '🔒 Private Profile (Public View Only)',
                    'is_profile_private': 1
                })
            else:
                sanitized_users.append({
                    'id': uid,
                    'username': usr['username'],
                    'avatar_color': usr['avatar_color'] or '#818cf8',
                    'role': usr['role'],
                    'bio': usr.get('bio') or 'Group Theory & Game Explorer',
                    'is_profile_private': 0
                })

        return {
            'posts': [dict(p) for p in posts_rows],
            'invitations': [dict(i) for i in invites_rows],
            'users': sanitized_users
        }
