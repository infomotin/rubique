"""
CubePermutation AI - Card Game Model (MVC Architecture)
=======================================================
Implements the CyberDeck Memory & Algorithmic Card Matching Game:
Features 8 distinct pairs of twisty puzzle & chess grandmaster motifs.
"""

import json
import random
from .db import query_one, query_all, execute_insert, execute_update

CARD_SYMBOLS = [
    {"id": "king", "name": "Grandmaster King", "icon": "fa-chess-king", "color": "#f59e0b", "category": "Chess"},
    {"id": "queen", "name": "Tactical Queen", "icon": "fa-chess-queen", "color": "#ec4899", "category": "Chess"},
    {"id": "knight", "name": "Hyper Knight", "icon": "fa-chess-knight", "color": "#8b5cf6", "category": "Chess"},
    {"id": "gods_num", "name": "God's Number 20", "icon": "fa-cube", "color": "#06b6d4", "category": "Cube"},
    {"id": "megaminx", "name": "12-Axis Megaminx", "icon": "fa-gem", "color": "#10b981", "category": "Geometry"},
    {"id": "pyraminx", "name": "Pyraminx Tetrahedron", "icon": "fa-shapes", "color": "#f97316", "category": "Geometry"},
    {"id": "kociemba", "name": "Kociemba Subgroup", "icon": "fa-code-branch", "color": "#6366f1", "category": "Algorithm"},
    {"id": "quantum", "name": "XR Quantum Core", "icon": "fa-atom", "color": "#e11d48", "category": "Quantum"}
]

class CardModel:
    """CyberDeck Memory Card Engine"""

    @staticmethod
    def create_game(user_id, card_pairs=8):
        """Generates a new randomized cyber deck match session"""
        symbols_pool = CARD_SYMBOLS[:card_pairs]
        # Duplicate to create matching pairs
        deck = []
        card_id = 1
        for sym in symbols_pool:
            deck.append({
                "card_id": card_id,
                "pair_key": sym["id"],
                "name": sym["name"],
                "icon": sym["icon"],
                "color": sym["color"],
                "category": sym["category"],
                "matched": False
            })
            card_id += 1
            deck.append({
                "card_id": card_id,
                "pair_key": sym["id"],
                "name": sym["name"],
                "icon": sym["icon"],
                "color": sym["color"],
                "category": sym["category"],
                "matched": False
            })
            card_id += 1

        random.shuffle(deck)
        deck_json = json.dumps(deck)

        sql_mysql = """
            INSERT INTO card_games (user_id, game_type, card_pairs, moves_count, time_seconds, score, status, deck_state)
            VALUES (%s, 'cyber_deck_match', %s, 0, 0, 0, 'active', %s)
        """
        sql_sqlite = """
            INSERT INTO card_games (user_id, game_type, card_pairs, moves_count, time_seconds, score, status, deck_state)
            VALUES (?, 'cyber_deck_match', ?, 0, 0, 0, 'active', ?)
        """
        game_id = execute_insert(sql_mysql, sql_sqlite, (user_id, card_pairs, deck_json))
        return game_id, deck

    @staticmethod
    def get_game(game_id):
        return query_one(
            "SELECT * FROM card_games WHERE id = %s",
            "SELECT * FROM card_games WHERE id = ?",
            (game_id,)
        )

    @staticmethod
    def update_game(game_id, moves_count, time_seconds, score, status='active', deck_state=None):
        if deck_state is not None:
            deck_str = json.dumps(deck_state) if isinstance(deck_state, (list, dict)) else str(deck_state)
            sql_mysql = "UPDATE card_games SET moves_count = %s, time_seconds = %s, score = %s, status = %s, deck_state = %s WHERE id = %s"
            sql_sqlite = "UPDATE card_games SET moves_count = ?, time_seconds = ?, score = ?, status = ?, deck_state = ? WHERE id = ?"
            return execute_update(sql_mysql, sql_sqlite, (moves_count, time_seconds, score, status, deck_str, game_id))
        else:
            sql_mysql = "UPDATE card_games SET moves_count = %s, time_seconds = %s, score = %s, status = %s WHERE id = %s"
            sql_sqlite = "UPDATE card_games SET moves_count = ?, time_seconds = ?, score = ?, status = ?, WHERE id = ?"
            return execute_update(sql_mysql, sql_sqlite, (moves_count, time_seconds, score, status, game_id))

    @staticmethod
    def pause_game(game_id, user_id=None):
        where_m = "id = %s" if not user_id else "id = %s AND user_id = %s"
        where_s = "id = ?" if not user_id else "id = ? AND user_id = ?"
        params = (game_id,) if not user_id else (game_id, user_id)
        return execute_update(
            f"UPDATE card_games SET status = 'paused' WHERE {where_m}",
            f"UPDATE card_games SET status = 'paused' WHERE {where_s}",
            params
        )

    @staticmethod
    def resume_game(game_id, user_id=None):
        where_m = "id = %s" if not user_id else "id = %s AND user_id = %s"
        where_s = "id = ?" if not user_id else "id = ? AND user_id = ?"
        params = (game_id,) if not user_id else (game_id, user_id)
        execute_update(
            f"UPDATE card_games SET status = 'active' WHERE {where_m}",
            f"UPDATE card_games SET status = 'active' WHERE {where_s}",
            params
        )
        return CardModel.get_game(game_id)

    @staticmethod
    def destroy_game(game_id, user_id=None):
        where_m = "id = %s" if not user_id else "id = %s AND user_id = %s"
        where_s = "id = ?" if not user_id else "id = ? AND user_id = ?"
        params = (game_id,) if not user_id else (game_id, user_id)
        return execute_update(
            f"DELETE FROM card_games WHERE {where_m}",
            f"DELETE FROM card_games WHERE {where_s}",
            params
        )

    @staticmethod
    def get_user_games(user_id, limit=20):
        return query_all(
            "SELECT * FROM card_games WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            "SELECT * FROM card_games WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
