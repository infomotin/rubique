"""
CubePermutation AI - Super Admin Model (MVC Architecture)
=========================================================
Handles system-wide analytics, user management, tournament declaration,
trophy awards, course curation, and promo coupon distribution.
"""

from .db import query_one, query_all, execute_insert, execute_update

class AdminModel:
    """Super Admin operations for user management and competition declaring"""

    @staticmethod
    def get_system_stats():
        """Aggregates system-wide analytics for the Super Admin Command Center"""
        users_count = query_one("SELECT COUNT(*) as c FROM users", "SELECT COUNT(*) as c FROM users")
        solves_count = query_one("SELECT COUNT(*) as c FROM solves", "SELECT COUNT(*) as c FROM solves")
        comps_count = query_one("SELECT COUNT(*) as c FROM competitions", "SELECT COUNT(*) as c FROM competitions")
        courses_count = query_one("SELECT COUNT(*) as c FROM courses", "SELECT COUNT(*) as c FROM courses")
        coupons_count = query_one("SELECT COUNT(*) as c FROM coupons", "SELECT COUNT(*) as c FROM coupons")
        
        # Role Breakdown
        role_stats = query_all(
            "SELECT role, COUNT(*) as count FROM users GROUP BY role",
            "SELECT role, COUNT(*) as count FROM users GROUP BY role"
        )
        
        return {
            'total_users': users_count['c'] if users_count else 0,
            'total_solves': solves_count['c'] if solves_count else 0,
            'total_competitions': comps_count['c'] if comps_count else 0,
            'total_courses': courses_count['c'] if courses_count else 0,
            'total_coupons': coupons_count['c'] if coupons_count else 0,
            'role_breakdown': role_stats
        }

    @staticmethod
    def get_all_users():
        """Fetches all registered users along with their individual solve counts"""
        sql_mysql = """
            SELECT u.id, u.username, u.email, u.role, u.bio, u.avatar_color, u.created_at,
                   COUNT(s.id) as solve_count
            FROM users u
            LEFT JOIN solves s ON u.id = s.user_id
            GROUP BY u.id
            ORDER BY u.id DESC
        """
        sql_sqlite = """
            SELECT u.id, u.username, u.email, u.role, u.bio, u.avatar_color, u.created_at,
                   COUNT(s.id) as solve_count
            FROM users u
            LEFT JOIN solves s ON u.id = s.user_id
            GROUP BY u.id
            ORDER BY u.id DESC
        """
        return query_all(sql_mysql, sql_sqlite)

    @staticmethod
    def update_user_role(user_id, new_role):
        """Promotes or demotes user role (super_admin, developer, user)"""
        return execute_update(
            "UPDATE users SET role = %s WHERE id = %s",
            "UPDATE users SET role = ? WHERE id = ?",
            (new_role, user_id)
        )

    @staticmethod
    def delete_user(user_id):
        """Deletes user account and associated solve logs"""
        return execute_update(
            "DELETE FROM users WHERE id = %s",
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )

    # --- Competition & Tournament Management ---
    @staticmethod
    def create_competition(title, description, scramble, prize_trophy, created_by=1):
        """Super Admin declares a new official Speedcubing Competition"""
        return execute_insert(
            "INSERT INTO competitions (title, description, scramble, prize_trophy, created_by) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO competitions (title, description, scramble, prize_trophy, created_by) VALUES (?, ?, ?, ?, ?)",
            (title, description, scramble, prize_trophy, created_by)
        )

    @staticmethod
    def get_all_competitions():
        """Lists all competitions with entry counts"""
        sql = """
            SELECT c.*, COUNT(e.id) as entry_count
            FROM competitions c
            LEFT JOIN competition_entries e ON c.id = e.competition_id
            GROUP BY c.id
            ORDER BY c.id DESC
        """
        return query_all(sql, sql)

    @staticmethod
    def delete_competition(comp_id):
        return execute_update("DELETE FROM competitions WHERE id = %s", "DELETE FROM competitions WHERE id = ?", (comp_id,))

    # --- Courses & Tutorials Management ---
    @staticmethod
    def create_course(title, description, difficulty, modules_count, author='Super Admin'):
        return execute_insert(
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (?, ?, ?, ?, ?)",
            (title, description, difficulty, modules_count, author)
        )

    @staticmethod
    def get_all_courses():
        return query_all("SELECT * FROM courses ORDER BY id DESC", "SELECT * FROM courses ORDER BY id DESC")

    @staticmethod
    def delete_course(course_id):
        return execute_update("DELETE FROM courses WHERE id = %s", "DELETE FROM courses WHERE id = ?", (course_id,))

    # --- Coupons & Rewards Management ---
    @staticmethod
    def create_coupon(code, reward_text, discount_percent=100):
        return execute_insert(
            "INSERT INTO coupons (code, reward_text, discount_percent) VALUES (%s, %s, %s)",
            "INSERT INTO coupons (code, reward_text, discount_percent) VALUES (?, ?, ?)",
            (code.upper(), reward_text, discount_percent)
        )

    @staticmethod
    def get_all_coupons():
        return query_all("SELECT * FROM coupons ORDER BY id DESC", "SELECT * FROM coupons ORDER BY id DESC")

    @staticmethod
    def delete_coupon(coupon_id):
        return execute_update("DELETE FROM coupons WHERE id = %s", "DELETE FROM coupons WHERE id = ?", (coupon_id,))
