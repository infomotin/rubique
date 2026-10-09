"""
CubePermutation AI - Game Security & Telemetry Model (MVC Architecture)
========================================================================
Handles:
1. Super Admin Game Module Toggles (Chess, Card, Speedcube)
2. Game Activities Real-Time Observability (Chess, Cards, Solves)
3. Security & Anti-Cheat Anomaly Engine (Rapid-move bot checks, unauthorized probes)
4. Developer Panel Bit-Level Telemetry Monitoring (Bit & byte telemetry stream)
"""

import time
import uuid
from .db import query_one, query_all, execute_insert, execute_update

class SecurityModel:
    """Super Admin Game Observability & Developer Bit Telemetry Model"""

    # =========================================================================
    # 1. SUPER ADMIN GAME FEATURE TOGGLES & SYSTEM SETTINGS
    # =========================================================================
    @staticmethod
    def get_setting(key, default='0'):
        """Fetches setting value by key"""
        res = query_one(
            "SELECT setting_value FROM system_settings WHERE setting_key = %s",
            "SELECT setting_value FROM system_settings WHERE setting_key = ?",
            (key,)
        )
        if res and res.get('setting_value') is not None:
            return res['setting_value']
        return default

    @staticmethod
    def set_setting(key, value, description=""):
        """Updates or inserts a system setting"""
        existing = query_one(
            "SELECT id FROM system_settings WHERE setting_key = %s",
            "SELECT id FROM system_settings WHERE setting_key = ?",
            (key,)
        )
        val_str = str(value)
        if existing:
            sql_mysql = "UPDATE system_settings SET setting_value = %s WHERE setting_key = %s"
            sql_sqlite = "UPDATE system_settings SET setting_value = ? WHERE setting_key = ?"
            return execute_update(sql_mysql, sql_sqlite, (val_str, key))
        else:
            sql_mysql = "INSERT INTO system_settings (setting_key, setting_value, description) VALUES (%s, %s, %s)"
            sql_sqlite = "INSERT INTO system_settings (setting_key, setting_value, description) VALUES (?, ?, ?)"
            return execute_insert(sql_mysql, sql_sqlite, (key, val_str, description))

    @staticmethod
    def get_all_game_settings():
        """Returns standard game toggles and security flags dictionary"""
        defaults = {
            'chess_game_enabled': '1',
            'card_game_enabled': '1',
            'speedcube_game_enabled': '1',
            'game_anti_cheat_enabled': '1',
            'security_audit_logging': '1',
            'bit_telemetry_enabled': '1'
        }
        rows = query_all("SELECT * FROM system_settings", "SELECT * FROM system_settings")
        settings_dict = dict(defaults)
        for r in rows:
            settings_dict[r['setting_key']] = r['setting_value']
        return settings_dict

    @staticmethod
    def is_game_enabled(game_name):
        """Checks if a game module is active for players"""
        key = f"{game_name}_game_enabled" if not game_name.endswith('_enabled') else game_name
        val = SecurityModel.get_setting(key, default='1')
        return val in ['1', 'true', 'True', True]

    # =========================================================================
    # 2. GAME ACTIVITIES OBSERVATION & SUPER ADMIN OVERSIGHT
    # =========================================================================
    @staticmethod
    def get_all_game_activities(limit=50):
        """
        Retrieves real-time observation log across all games:
        Chess matches, Card matches, and Speedcube solves
        """
        activities = []
        
        # 1. Chess Games
        chess_rows = query_all("""
            SELECT cg.id, cg.user_id, cg.title, cg.match_type, cg.moves_count, cg.status, cg.created_at,
                   cg.fen, u.username as player_name, u.role as player_role,
                   'chess' as game_category
            FROM chess_games cg
            LEFT JOIN users u ON cg.user_id = u.id
            ORDER BY cg.created_at DESC LIMIT %s
        """, """
            SELECT cg.id, cg.user_id, cg.title, cg.match_type, cg.moves_count, cg.status, cg.created_at,
                   cg.fen, u.username as player_name, u.role as player_role,
                   'chess' as game_category
            FROM chess_games cg
            LEFT JOIN users u ON cg.user_id = u.id
            ORDER BY cg.created_at DESC LIMIT ?
        """, (limit,))
        activities.extend(chess_rows)

        # 2. Card Games
        card_rows = query_all("""
            SELECT cg.id, cg.user_id, cg.game_type as title, cg.game_type as match_type, 
                   cg.moves_count, cg.status, cg.created_at,
                   cg.deck_state as fen, u.username as player_name, u.role as player_role,
                   'card' as game_category
            FROM card_games cg
            LEFT JOIN users u ON cg.user_id = u.id
            ORDER BY cg.created_at DESC LIMIT %s
        """, """
            SELECT cg.id, cg.user_id, cg.game_type as title, cg.game_type as match_type, 
                   cg.moves_count, cg.status, cg.created_at,
                   cg.deck_state as fen, u.username as player_name, u.role as player_role,
                   'card' as game_category
            FROM card_games cg
            LEFT JOIN users u ON cg.user_id = u.id
            ORDER BY cg.created_at DESC LIMIT ?
        """, (limit,))
        activities.extend(card_rows)

        # Sort combined activities by created_at DESC
        activities.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)
        return activities[:limit]

    @staticmethod
    def freeze_game(game_type, game_id):
        """Super Admin action: Freeze / Pause an active game session"""
        if game_type == 'chess':
            execute_update(
                "UPDATE chess_games SET status = 'paused' WHERE id = %s",
                "UPDATE chess_games SET status = 'paused' WHERE id = ?",
                (game_id,)
            )
        elif game_type == 'card':
            execute_update(
                "UPDATE card_games SET status = 'paused' WHERE id = %s",
                "UPDATE card_games SET status = 'paused' WHERE id = ?",
                (game_id,)
            )
        return True

    @staticmethod
    def terminate_game(game_type, game_id):
        """Super Admin action: Terminate an active game session"""
        if game_type == 'chess':
            execute_update(
                "UPDATE chess_games SET status = 'completed', winner = 'admin_terminated' WHERE id = %s",
                "UPDATE chess_games SET status = 'completed', winner = 'admin_terminated' WHERE id = ?",
                (game_id,)
            )
        elif game_type == 'card':
            execute_update(
                "UPDATE card_games SET status = 'completed' WHERE id = %s",
                "UPDATE card_games SET status = 'completed' WHERE id = ?",
                (game_id,)
            )
        return True

    @staticmethod
    def get_game_activity_stats():
        """Aggregates overview counts of active and total game sessions"""
        c_chess = query_one("SELECT COUNT(*) as c FROM chess_games", "SELECT COUNT(*) as c FROM chess_games")
        c_chess_active = query_one("SELECT COUNT(*) as c FROM chess_games WHERE status = 'active'", "SELECT COUNT(*) as c FROM chess_games WHERE status = 'active'")
        c_cards = query_one("SELECT COUNT(*) as c FROM card_games", "SELECT COUNT(*) as c FROM card_games")
        c_cards_active = query_one("SELECT COUNT(*) as c FROM card_games WHERE status = 'active'", "SELECT COUNT(*) as c FROM card_games WHERE status = 'active'")
        c_sec = query_one("SELECT COUNT(*) as c FROM game_security_events", "SELECT COUNT(*) as c FROM game_security_events")
        
        return {
            'total_chess_games': c_chess['c'] if c_chess else 0,
            'active_chess_games': c_chess_active['c'] if c_chess_active else 0,
            'total_card_games': c_cards['c'] if c_cards else 0,
            'active_card_games': c_cards_active['c'] if c_cards_active else 0,
            'security_events_count': c_sec['c'] if c_sec else 0
        }

    # =========================================================================
    # 3. SECURITY & ANTI-CHEAT ANOMALY AUDIT TRAIL
    # =========================================================================
    @staticmethod
    def log_security_event(game_type, event_type, severity='warning', details='', user_id=None, game_id=None, client_ip=None, user_agent=None):
        """Records an intrusion, anti-cheat flag, or access denial security event"""
        sql_mysql = """
            INSERT INTO game_security_events (user_id, game_type, game_id, event_type, severity, client_ip, user_agent, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        sql_sqlite = """
            INSERT INTO game_security_events (user_id, game_type, game_id, event_type, severity, client_ip, user_agent, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (user_id, game_type, game_id, event_type, severity, client_ip or '127.0.0.1', user_agent or 'Antigravity-Agent/1.0', details)
        return execute_insert(sql_mysql, sql_sqlite, params)

    @staticmethod
    def get_recent_security_events(limit=50):
        """Fetches security incidents for Super Admin inspection"""
        sql_mysql = """
            SELECT gse.*, u.username, u.role
            FROM game_security_events gse
            LEFT JOIN users u ON gse.user_id = u.id
            ORDER BY gse.created_at DESC LIMIT %s
        """
        sql_sqlite = """
            SELECT gse.*, u.username, u.role
            FROM game_security_events gse
            LEFT JOIN users u ON gse.user_id = u.id
            ORDER BY gse.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, (limit,))

    @staticmethod
    def dismiss_security_event(event_id):
        """Dismisses / clears a security alert"""
        execute_update(
            "DELETE FROM game_security_events WHERE id = %s",
            "DELETE FROM game_security_events WHERE id = ?",
            (event_id,)
        )
        return True

    # =========================================================================
    # 4. DEVELOPER BIT-LEVEL TELEMETRY STREAM MONITORING
    # =========================================================================
    @staticmethod
    def log_telemetry_bit(module, action, payload_data="", latency_ms=0.0, http_status=200, severity="INFO", user_id=None, role=None, client_ip=None):
        """
        Logs fine-grained bit-level and byte-level telemetry stream for developer monitoring
        """
        # Calculate raw payload byte and bit count
        raw_bytes = str(payload_data).encode('utf-8')
        payload_bytes = len(raw_bytes)
        payload_bits = payload_bytes * 8
        payload_hex = raw_bytes.hex()[:48]  # First 24 bytes in hex
        trace_id = uuid.uuid4().hex[:12]

        sql_mysql = """
            INSERT INTO developer_telemetry_stream 
            (trace_id, client_ip, user_id, role, module, action, payload_bytes, payload_bits, payload_hex, latency_ms, http_status, severity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        sql_sqlite = """
            INSERT INTO developer_telemetry_stream 
            (trace_id, client_ip, user_id, role, module, action, payload_bytes, payload_bits, payload_hex, latency_ms, http_status, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            trace_id, client_ip or '127.0.0.1', user_id, role or 'guest',
            module, action, payload_bytes, payload_bits, payload_hex,
            round(latency_ms, 2), http_status, severity
        )
        return execute_insert(sql_mysql, sql_sqlite, params)

    @staticmethod
    def get_telemetry_stream(limit=100, module=None, severity=None):
        """Fetches developer live activity bit stream"""
        where_mysql = []
        where_sqlite = []
        params = []

        if module:
            where_mysql.append("module = %s")
            where_sqlite.append("module = ?")
            params.append(module)

        if severity:
            where_mysql.append("severity = %s")
            where_sqlite.append("severity = ?")
            params.append(severity)

        where_clause_mysql = f"WHERE {' AND '.join(where_mysql)}" if where_mysql else ""
        where_clause_sqlite = f"WHERE {' AND '.join(where_sqlite)}" if where_sqlite else ""

        params.append(limit)

        sql_mysql = f"""
            SELECT dts.*, u.username
            FROM developer_telemetry_stream dts
            LEFT JOIN users u ON dts.user_id = u.id
            {where_clause_mysql}
            ORDER BY dts.id DESC LIMIT %s
        """
        sql_sqlite = f"""
            SELECT dts.*, u.username
            FROM developer_telemetry_stream dts
            LEFT JOIN users u ON dts.user_id = u.id
            {where_clause_sqlite}
            ORDER BY dts.id DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, tuple(params))

    @staticmethod
    def clear_telemetry_stream():
        """Clears telemetry bit stream"""
        execute_update("DELETE FROM developer_telemetry_stream", "DELETE FROM developer_telemetry_stream")
        return True
