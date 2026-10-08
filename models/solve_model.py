"""
CubePermutation AI - Solve Model (MVC Architecture)
===================================================
Cube Solves History, Performance Metrics, and Analytics data model.
"""

from .db import query_one, query_all, execute_insert, execute_update

class SolveModel:
    """
    Solve Data Model:
    Tracks solved scrambles, solution lengths, step counts, and user profile statistics.
    """

    @staticmethod
    def record_solve(user_id, scramble, solution, move_count):
        """
        User er solve kora sequence database e save kore.
        """
        sql_mysql = "INSERT INTO solves (user_id, scramble, solution, move_count) VALUES (%s, %s, %s, %s)"
        sql_sqlite = "INSERT INTO solves (user_id, scramble, solution, move_count) VALUES (?, ?, ?, ?)"
        
        solve_id = execute_insert(sql_mysql, sql_sqlite, (user_id, scramble, solution, move_count))
        return solve_id

    @staticmethod
    def get_user_history(user_id, limit=20):
        """
        User er recent solves chronological order e fetch kore.
        """
        sql_mysql = "SELECT id, scramble, solution, move_count, created_at FROM solves WHERE user_id = %s ORDER BY id DESC LIMIT %s"
        sql_sqlite = "SELECT id, scramble, solution, move_count, created_at FROM solves WHERE user_id = ? ORDER BY id DESC LIMIT ?"
        return query_all(sql_mysql, sql_sqlite, (user_id, limit))

    @staticmethod
    def get_user_stats(user_id):
        """
        User er profile statistics calculate kore:
        - Total solves count
        - Optimal / minimum move count
        - Average move count
        """
        sql_mysql = """
            SELECT 
                COUNT(*) as total_solves,
                COALESCE(MIN(move_count), 0) as min_moves,
                COALESCE(AVG(move_count), 0) as avg_moves
            FROM solves 
            WHERE user_id = %s
        """
        sql_sqlite = """
            SELECT 
                COUNT(*) as total_solves,
                COALESCE(MIN(move_count), 0) as min_moves,
                COALESCE(AVG(move_count), 0) as avg_moves
            FROM solves 
            WHERE user_id = ?
        """
        stats = query_one(sql_mysql, sql_sqlite, (user_id,))
        if stats:
            stats['avg_moves'] = round(float(stats['avg_moves']), 1)
        return stats or {'total_solves': 0, 'min_moves': 0, 'avg_moves': 0.0}

    @staticmethod
    def delete_solve(solve_id, user_id):
        """Single solve history item delete kore"""
        sql_mysql = "DELETE FROM solves WHERE id = %s AND user_id = %s"
        sql_sqlite = "DELETE FROM solves WHERE id = ? AND user_id = ?"
        return execute_update(sql_mysql, sql_sqlite, (solve_id, user_id))

    @staticmethod
    def clear_all(user_id):
        """User er shob solve history clear kore"""
        sql_mysql = "DELETE FROM solves WHERE user_id = %s"
        sql_sqlite = "DELETE FROM solves WHERE user_id = ?"
        return execute_update(sql_mysql, sql_sqlite, (user_id,))
