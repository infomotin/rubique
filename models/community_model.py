"""
CubePermutation AI - Community & Social Model (MVC Pattern)
===========================================================
Handles Video Uploads, Speedcuber Live Chat, Groups, Friends, and Blog Posts.
"""

from .db import query_one, query_all, execute_insert, execute_update

class CommunityModel:
    
    # -------------------------------------------------------------
    # 1. VIDEOS MANAGEMENT
    # -------------------------------------------------------------
    @staticmethod
    def upload_video(user_id, title, video_url, solve_time=0.0, method='CFOP', description=''):
        """Saves a speedcubing solve video"""
        return execute_insert(
            """INSERT INTO videos (user_id, title, video_url, solve_time, method, description, likes)
               VALUES (%s, %s, %s, %s, %s, %s, 0)""",
            """INSERT INTO videos (user_id, title, video_url, solve_time, method, description, likes)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (user_id, title, video_url, float(solve_time), method, description)
        )

    @staticmethod
    def get_all_videos(limit=20):
        """Fetches all speedcubing solve videos with author details"""
        return query_all(
            """SELECT v.*, u.username, u.avatar_color
               FROM videos v
               JOIN users u ON v.user_id = u.id
               ORDER BY v.created_at DESC LIMIT %s""",
            """SELECT v.*, u.username, u.avatar_color
               FROM videos v
               JOIN users u ON v.user_id = u.id
               ORDER BY v.created_at DESC LIMIT ?""",
            (limit,)
        )

    @staticmethod
    def like_video(video_id):
        """Increments like counter on a video"""
        return execute_update(
            "UPDATE videos SET likes = likes + 1 WHERE id = %s",
            "UPDATE videos SET likes = likes + 1 WHERE id = ?",
            (video_id,)
        )

    # -------------------------------------------------------------
    # 2. CHAT GROUPS & MESSAGES
    # -------------------------------------------------------------
    @staticmethod
    def create_group(name, description, is_private=0, passcode=None, created_by=1):
        """Creates a public or private chat group"""
        return execute_insert(
            """INSERT INTO chat_groups (name, description, is_private, passcode, created_by)
               VALUES (%s, %s, %s, %s, %s)""",
            """INSERT INTO chat_groups (name, description, is_private, passcode, created_by)
               VALUES (?, ?, ?, ?, ?)""",
            (name, description, 1 if is_private else 0, passcode, created_by)
        )

    @staticmethod
    def get_all_groups():
        """Fetches all public and private chat groups"""
        return query_all(
            """SELECT g.*, u.username as creator_name,
               (SELECT COUNT(*) FROM chat_messages m WHERE m.group_id = g.id) as message_count
               FROM chat_groups g
               JOIN users u ON g.created_by = u.id
               ORDER BY g.created_at DESC""",
            """SELECT g.*, u.username as creator_name,
               (SELECT COUNT(*) FROM chat_messages m WHERE m.group_id = g.id) as message_count
               FROM chat_groups g
               JOIN users u ON g.created_by = u.id
               ORDER BY g.created_at DESC"""
        )

    @staticmethod
    def send_message(sender_id, message, group_id=None, receiver_id=None):
        """Sends a message in a group or direct 1-on-1"""
        return execute_insert(
            """INSERT INTO chat_messages (sender_id, receiver_id, group_id, message)
               VALUES (%s, %s, %s, %s)""",
            """INSERT INTO chat_messages (sender_id, receiver_id, group_id, message)
               VALUES (?, ?, ?, ?)""",
            (sender_id, receiver_id, group_id, message)
        )

    @staticmethod
    def get_group_messages(group_id, limit=50):
        """Fetches latest messages from a group"""
        return query_all(
            """SELECT m.*, u.username, u.avatar_color
               FROM chat_messages m
               JOIN users u ON m.sender_id = u.id
               WHERE m.group_id = %s
               ORDER BY m.created_at ASC LIMIT %s""",
            """SELECT m.*, u.username, u.avatar_color
               FROM chat_messages m
               JOIN users u ON m.sender_id = u.id
               WHERE m.group_id = ?
               ORDER BY m.created_at ASC LIMIT ?""",
            (group_id, limit)
        )

    # -------------------------------------------------------------
    # 3. FRIENDS SYSTEM
    # -------------------------------------------------------------
    @staticmethod
    def add_friend(user_id, friend_id):
        """Adds or accepts a friend connection"""
        existing = query_one(
            "SELECT id FROM friends WHERE user_id = %s AND friend_id = %s",
            "SELECT id FROM friends WHERE user_id = ? AND friend_id = ?",
            (user_id, friend_id)
        )
        if not existing:
            return execute_insert(
                "INSERT INTO friends (user_id, friend_id, status) VALUES (%s, %s, 'accepted')",
                "INSERT INTO friends (user_id, friend_id, status) VALUES (?, ?, 'accepted')",
                (user_id, friend_id)
            )
        return existing['id']

    @staticmethod
    def get_user_friends(user_id):
        """Fetches all speedcubing friends for a user"""
        return query_all(
            """SELECT u.id, u.username, u.bio, u.avatar_color, f.created_at as friendship_date
               FROM friends f
               JOIN users u ON f.friend_id = u.id
               WHERE f.user_id = %s""",
            """SELECT u.id, u.username, u.bio, u.avatar_color, f.created_at as friendship_date
               FROM friends f
               JOIN users u ON f.friend_id = u.id
               WHERE f.user_id = ?""",
            (user_id,)
        )

    # -------------------------------------------------------------
    # 4. BLOG POSTS & COMMUNITY FEED
    # -------------------------------------------------------------
    @staticmethod
    def create_post(user_id, title, content, tags='CFOP,Tips'):
        """Creates a community blog post"""
        return execute_insert(
            """INSERT INTO blog_posts (user_id, title, content, tags, likes)
               VALUES (%s, %s, %s, %s, 0)""",
            """INSERT INTO blog_posts (user_id, title, content, tags, likes)
               VALUES (?, ?, ?, ?, 0)""",
            (user_id, title, content, tags)
        )

    @staticmethod
    def get_all_posts(limit=20):
        """Fetches all blog posts with comments count"""
        return query_all(
            """SELECT b.*, u.username, u.avatar_color,
               (SELECT COUNT(*) FROM blog_comments c WHERE c.post_id = b.id) as comment_count
               FROM blog_posts b
               JOIN users u ON b.user_id = u.id
               ORDER BY b.created_at DESC LIMIT %s""",
            """SELECT b.*, u.username, u.avatar_color,
               (SELECT COUNT(*) FROM blog_comments c WHERE c.post_id = b.id) as comment_count
               FROM blog_posts b
               JOIN users u ON b.user_id = u.id
               ORDER BY b.created_at DESC LIMIT ?""",
            (limit,)
        )

    @staticmethod
    def add_comment(post_id, user_id, comment):
        """Adds a comment to a blog post"""
        return execute_insert(
            "INSERT INTO blog_comments (post_id, user_id, comment) VALUES (%s, %s, %s)",
            "INSERT INTO blog_comments (post_id, user_id, comment) VALUES (?, ?, ?)",
            (post_id, user_id, comment)
        )

    @staticmethod
    def get_post_comments(post_id):
        """Fetches comments for a specific post"""
        return query_all(
            """SELECT c.*, u.username, u.avatar_color
               FROM blog_comments c
               JOIN users u ON c.user_id = u.id
               WHERE c.post_id = %s
               ORDER BY c.created_at ASC""",
            """SELECT c.*, u.username, u.avatar_color
               FROM blog_comments c
               JOIN users u ON c.user_id = u.id
               WHERE c.post_id = ?
               ORDER BY c.created_at ASC""",
            (post_id,)
        )
