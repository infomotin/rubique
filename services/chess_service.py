"""
CubePermutation AI - Chess Domain Service
==========================================
Encapsulates 3D GoChess board rules, autonomous AI opponent decision engine,
Minimax move tree evaluation, coach hints, and stage lifecycle management.

Easy Description:
- Manages the rules of chess: legal moves, checks, checkmates, stalemates.
- Computes AI moves based on difficulty level (Novice 800 to Grandmaster 2600 ELO).
- Calculates LED coach hints and advantage evaluation scores.
- Handles saving, pausing, and resuming chess stages.
"""

from typing import Dict, Any, Optional, Tuple
import chess
from models.chess_model import ChessModel
from models.security_model import SecurityModel


class ChessService:
    """
    GoChess 3D Smart Board Domain Service
    """

    @staticmethod
    def start_game(
        user_id: int,
        title: str = 'GoChess Smart Studio',
        game_mode: str = 'ai',
        ai_level: int = 2,
        board_theme: str = 'obsidian'
    ) -> Dict[str, Any]:
        """
        Creates a new chess game session and initializes starting board state.

        Easy Description:
        Sets up a fresh chess game on the board with full initial coach hints.
        """
        game_id = ChessModel.create_game(
            user_id=user_id,
            title=title,
            game_mode=game_mode,
            ai_level=ai_level,
            board_theme=board_theme
        )
        board = chess.Board()
        hints = ChessModel.get_coach_hints(board)

        return {
            "status": "success",
            "game_id": game_id,
            "fen": board.fen(),
            "hints": hints
        }

    @staticmethod
    def process_player_move(
        fen: str,
        from_sq: str,
        to_sq: str,
        promotion: str = 'q',
        game_id: Optional[int] = None,
        ai_level: int = 2,
        game_mode: str = 'ai',
        user_id: Optional[int] = None,
        client_ip: str = '127.0.0.1'
    ) -> Tuple[bool, Dict[str, Any], int]:
        """
        Validates and executes a player's move, followed by AI counter-move if playing in AI mode.

        Easy Description:
        Validates the player's move, updates the board, and if playing the AI, triggers the AI's response move.
        """
        try:
            board = chess.Board(fen)
        except Exception:
            return False, {"status": "error", "message": "Invalid FEN board state"}, 400

        if not from_sq or not to_sq:
            return False, {"status": "error", "message": "Missing move squares"}, 400

        move_uci = f"{from_sq}{to_sq}"
        move_candidate = chess.Move.from_uci(move_uci)

        if move_candidate not in board.legal_moves:
            # Check promotion candidate
            move_candidate = chess.Move.from_uci(f"{move_uci}{promotion.lower()}")
            if move_candidate not in board.legal_moves:
                SecurityModel.log_security_event(
                    game_type='chess',
                    game_id=game_id,
                    event_type='ILLEGAL_MOVE_ATTEMPT',
                    severity='warning',
                    details=f"Illegal move {move_uci} attempted on FEN {fen[:35]}",
                    user_id=user_id,
                    client_ip=client_ip
                )
                return False, {
                    "status": "illegal_move",
                    "message": f"Move {move_uci} is illegal in current position."
                }, 400

        # Execute player move
        player_san = board.san(move_candidate)
        player_captured = board.is_capture(move_candidate)
        board.push(move_candidate)

        SecurityModel.log_telemetry_bit(
            module='CHESS_XR',
            action='PLAYER_MOVE',
            payload_data=f"game_id={game_id}&move={player_san}&fen={board.fen()[:30]}",
            latency_ms=2.5,
            http_status=200,
            severity='INFO',
            user_id=user_id,
            role='subscriber',
            client_ip=client_ip
        )

        result_payload = {
            "status": "success",
            "player_move": {
                "from": from_sq,
                "to": to_sq,
                "san": player_san,
                "uci": move_candidate.uci(),
                "captured": player_captured
            },
            "fen": board.fen(),
            "is_check": board.is_check(),
            "is_game_over": board.is_game_over(),
            "result_message": None,
            "ai_move": None
        }

        # Check for game termination after player move
        if board.is_checkmate():
            result_payload["result_message"] = "Checkmate! You win!"
            if game_id:
                ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'player')
            return True, result_payload, 200

        if board.is_stalemate() or board.is_insufficient_material() or board.is_fivefold_repetition():
            result_payload["result_message"] = "Game Draw!"
            if game_id:
                ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'draw')
            return True, result_payload, 200

        # AI Opponent Counter Turn
        if game_mode == 'ai' and not board.is_game_over():
            ai_move, ai_score = ChessModel.get_ai_move(board, level=ai_level)
            if ai_move:
                ai_san = board.san(ai_move)
                ai_from = chess.square_name(ai_move.from_square)
                ai_to = chess.square_name(ai_move.to_square)
                ai_captured = board.is_capture(ai_move)

                board.push(ai_move)

                result_payload["ai_move"] = {
                    "from": ai_from,
                    "to": ai_to,
                    "san": ai_san,
                    "uci": ai_move.uci(),
                    "captured": ai_captured,
                    "score": ai_score
                }
                result_payload["fen"] = board.fen()
                result_payload["is_check"] = board.is_check()
                result_payload["is_game_over"] = board.is_game_over()

                if board.is_checkmate():
                    result_payload["result_message"] = "Checkmate! AI wins!"
                    if game_id:
                        ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'ai')
                elif board.is_stalemate() or board.is_insufficient_material():
                    result_payload["result_message"] = "Game Draw!"
                    if game_id:
                        ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'draw')

        # Persist updated board state to database
        if game_id:
            ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'active')

        # Calculate updated coach LED telemetry
        result_payload["hints"] = ChessModel.get_coach_hints(board)

        return True, result_payload, 200

    @staticmethod
    def trigger_ai_turn(
        fen: str,
        ai_level: int = 2,
        game_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any], int]:
        """
        Explicitly triggers the AI opponent to compute and execute the best move for current FEN.

        Easy Description:
        Forces the AI opponent to calculate its move immediately, supporting play-as-Black or manual triggers.
        """
        try:
            board = chess.Board(fen)
        except Exception:
            return False, {"status": "error", "message": "Invalid FEN board state"}, 400

        if board.is_game_over():
            return False, {"status": "error", "message": "Game is already over."}, 400

        ai_move, ai_score = ChessModel.get_ai_move(board, level=ai_level)
        if not ai_move:
            return False, {"status": "error", "message": "No legal moves available for AI."}, 400

        ai_san = board.san(ai_move)
        ai_from = chess.square_name(ai_move.from_square)
        ai_to = chess.square_name(ai_move.to_square)
        ai_captured = board.is_capture(ai_move)

        board.push(ai_move)

        result_payload = {
            "status": "success",
            "ai_move": {
                "from": ai_from,
                "to": ai_to,
                "san": ai_san,
                "uci": ai_move.uci(),
                "captured": ai_captured,
                "score": ai_score
            },
            "fen": board.fen(),
            "is_check": board.is_check(),
            "is_game_over": board.is_game_over(),
            "result_message": None
        }

        if board.is_checkmate():
            result_payload["result_message"] = "Checkmate!"
            if game_id:
                ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'ai')
        elif board.is_stalemate() or board.is_insufficient_material():
            result_payload["result_message"] = "Game Draw!"
            if game_id:
                ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'draw')
        elif game_id:
            ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'active')

        result_payload["hints"] = ChessModel.get_coach_hints(board)
        return True, result_payload, 200
