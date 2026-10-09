"""
CubePermutation AI - User Model (MVC Architecture)
===================================================
User Authentication, Profile Management, and Password Hashing model.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from .db import query_one, query_all, execute_insert, execute_update

class UserModel:
    """
    User Data Model:
    Registration, Login verification, and Profile updating operations.
    """
    
    @staticmethod
    def create_user(username, email, password, bio=None, avatar_color='#818cf8'):
        """
        Notun user create kore hashed password database e save kore.
        """
        password_hash = generate_password_hash(password)
        bio = bio or 'Group Theory Explorer & Speedcuber'
        
        sql_mysql = "INSERT INTO users (username, email, password_hash, bio, avatar_color) VALUES (%s, %s, %s, %s, %s)"
        sql_sqlite = "INSERT INTO users (username, email, password_hash, bio, avatar_color) VALUES (?, ?, ?, ?, ?)"
        
        user_id = execute_insert(sql_mysql, sql_sqlite, (username, email, password_hash, bio, avatar_color))
        return user_id

    @staticmethod
    def find_by_username(username):
        """
        Username diye user fetch kore (case-insensitive search).
        """
        sql_mysql = "SELECT * FROM users WHERE username = %s LIMIT 1"
        sql_sqlite = "SELECT * FROM users WHERE username = ? LIMIT 1"
        return query_one(sql_mysql, sql_sqlite, (username,))

    @staticmethod
    def find_by_id(user_id):
        """
        User ID diye user data fetch kore including all personal info.
        """
        sql_mysql = "SELECT * FROM users WHERE id = %s"
        sql_sqlite = "SELECT * FROM users WHERE id = ?"
        return query_one(sql_mysql, sql_sqlite, (user_id,))

    @staticmethod
    def verify_password(stored_hash, password):
        """
        Password hash check kore authentication verify kore.
        """
        return check_password_hash(stored_hash, password)

    @staticmethod
    def update_profile(user_id, bio, avatar_color, wca_id='', country='', main_cube='', preferred_method='', pb_single='', pb_ao5=''):
        """
        User er bio, avatar color, ebong personal speedcubing credentials update kore.
        """
        sql_mysql = """
            UPDATE users 
            SET bio = %s, avatar_color = %s, wca_id = %s, country = %s, main_cube = %s, preferred_method = %s, pb_single = %s, pb_ao5 = %s
            WHERE id = %s
        """
        sql_sqlite = """
            UPDATE users 
            SET bio = ?, avatar_color = ?, wca_id = ?, country = ?, main_cube = ?, preferred_method = ?, pb_single = ?, pb_ao5 = ?
            WHERE id = ?
        """
        return execute_update(
            sql_mysql, sql_sqlite,
            (bio, avatar_color, wca_id, country, main_cube, preferred_method, pb_single, pb_ao5, user_id)
        )

    @staticmethod
    def search_users(query, exclude_user_id=None, limit=10):
        """
        Search registered users by username for card game lobby and invites.
        """
        pattern = f"%{query.strip()}%" if query else "%"
        limit = max(1, min(int(limit or 10), 50))
        if exclude_user_id:
            sql_m = "SELECT id, username, email, role, avatar_color, created_at FROM users WHERE username LIKE %s AND id != %s ORDER BY username ASC LIMIT %s"
            sql_s = "SELECT id, username, email, role, avatar_color, created_at FROM users WHERE username LIKE ? AND id != ? ORDER BY username ASC LIMIT ?"
            return query_all(sql_m, sql_s, (pattern, int(exclude_user_id), limit)) or []
        else:
            sql_m = "SELECT id, username, email, role, avatar_color, created_at FROM users WHERE username LIKE %s ORDER BY username ASC LIMIT %s"
            sql_s = "SELECT id, username, email, role, avatar_color, created_at FROM users WHERE username LIKE ? ORDER BY username ASC LIMIT ?"
            return query_all(sql_m, sql_s, (pattern, limit)) or []

    @staticmethod
    def list_active_players(exclude_user_id=None, limit=12):
        """
        List registered users to find playing partners for games.
        """
        limit = max(1, min(int(limit or 12), 50))
        if exclude_user_id:
            sql_m = "SELECT id, username, email, role, avatar_color, created_at FROM users WHERE id != %s ORDER BY id DESC LIMIT %s"
            sql_s = "SELECT id, username, email, role, avatar_color, created_at FROM users WHERE id != ? ORDER BY id DESC LIMIT ?"
            return query_all(sql_m, sql_s, (int(exclude_user_id), limit)) or []
        else:
            sql_m = "SELECT id, username, email, role, avatar_color, created_at FROM users ORDER BY id DESC LIMIT %s"
            sql_s = "SELECT id, username, email, role, avatar_color, created_at FROM users ORDER BY id DESC LIMIT ?"
            return query_all(sql_m, sql_s, (limit,)) or []

