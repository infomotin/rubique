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
        User ID diye user data fetch kore.
        """
        sql_mysql = "SELECT id, username, email, bio, avatar_color, created_at FROM users WHERE id = %s"
        sql_sqlite = "SELECT id, username, email, bio, avatar_color, created_at FROM users WHERE id = ?"
        return query_one(sql_mysql, sql_sqlite, (user_id,))

    @staticmethod
    def verify_password(stored_hash, password):
        """
        Password hash check kore authentication verify kore.
        """
        return check_password_hash(stored_hash, password)

    @staticmethod
    def update_profile(user_id, bio, avatar_color):
        """
        User er bio ebong custom avatar accent color update kore.
        """
        sql_mysql = "UPDATE users SET bio = %s, avatar_color = %s WHERE id = %s"
        sql_sqlite = "UPDATE users SET bio = ?, avatar_color = ? WHERE id = ?"
        return execute_update(sql_mysql, sql_sqlite, (bio, avatar_color, user_id))
