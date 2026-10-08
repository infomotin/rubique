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
        # Sub-query form keeps the statement valid on MySQL ONLY_FULL_GROUP_BY mode
        sql = """
            SELECT u.id, u.username, u.email, u.role, u.bio, u.avatar_color, u.created_at,
                   (SELECT COUNT(*) FROM solves s WHERE s.user_id = u.id) as solve_count
            FROM users u
            ORDER BY u.id DESC
        """
        return query_all(sql, sql)

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
        """Deletes a user account together with every dependent relation row"""
        # Child tables first (SQLite has no enforced cascade on legacy tables)
        for sql_mysql, sql_sqlite, params in [
            ("DELETE FROM solves WHERE user_id = %s", "DELETE FROM solves WHERE user_id = ?", (user_id,)),
            ("DELETE FROM blog_comments WHERE user_id = %s", "DELETE FROM blog_comments WHERE user_id = ?", (user_id,)),
            ("DELETE FROM blog_comments WHERE post_id IN (SELECT id FROM blog_posts WHERE user_id = %s)",
             "DELETE FROM blog_comments WHERE post_id IN (SELECT id FROM blog_posts WHERE user_id = ?)", (user_id,)),
            ("DELETE FROM blog_posts WHERE user_id = %s", "DELETE FROM blog_posts WHERE user_id = ?", (user_id,)),
            ("DELETE FROM videos WHERE user_id = %s", "DELETE FROM videos WHERE user_id = ?", (user_id,)),
            ("DELETE FROM competition_entries WHERE user_id = %s", "DELETE FROM competition_entries WHERE user_id = ?", (user_id,)),
            ("DELETE FROM friends WHERE user_id = %s OR friend_id = %s", "DELETE FROM friends WHERE user_id = ? OR friend_id = ?", (user_id, user_id)),
            ("DELETE FROM chat_messages WHERE sender_id = %s OR receiver_id = %s",
             "DELETE FROM chat_messages WHERE sender_id = ? OR receiver_id = ?", (user_id, user_id)),
            ("DELETE FROM chat_messages WHERE group_id IN (SELECT id FROM chat_groups WHERE created_by = %s)",
             "DELETE FROM chat_messages WHERE group_id IN (SELECT id FROM chat_groups WHERE created_by = ?)", (user_id,)),
            ("DELETE FROM chat_groups WHERE created_by = %s", "DELETE FROM chat_groups WHERE created_by = ?", (user_id,)),
        ]:
            execute_update(sql_mysql, sql_sqlite, params)

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
        """Lists all competitions with entry counts (ONLY_FULL_GROUP_BY safe)"""
        sql = """
            SELECT c.*,
                   (SELECT COUNT(*) FROM competition_entries e WHERE e.competition_id = c.id) as entry_count
            FROM competitions c
            ORDER BY c.id DESC
        """
        return query_all(sql, sql)

    @staticmethod
    def delete_competition(comp_id):
        """Removes a competition together with all of its submitted entries"""
        execute_update(
            "DELETE FROM competition_entries WHERE competition_id = %s",
            "DELETE FROM competition_entries WHERE competition_id = ?",
            (comp_id,)
        )
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
    def find_coupon(code):
        """Fetches a coupon row by its unique promo code"""
        return query_one(
            "SELECT * FROM coupons WHERE code = %s LIMIT 1",
            "SELECT * FROM coupons WHERE code = ? LIMIT 1",
            (code,)
        )

    @staticmethod
    def delete_coupon(coupon_id):
        return execute_update("DELETE FROM coupons WHERE id = %s", "DELETE FROM coupons WHERE id = ?", (coupon_id,))
