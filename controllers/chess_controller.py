"""
GoChess Smart Board Studio Controller (MVC Architecture)
=======================================================
Dedicated Controller for:
- 3D Smart Robotic Chess Board (Particula GoChess pattern)
- Real-time Multi-Zone RGB LED Coaching & Telemetry
- Autonomous Robotic Self-Movement Simulation (XR patent glide)
- Multi-tier Minimax AI Engine (800 to 2600 ELO)
- Masterpiece Replay / Robotic Auto-Demonstrations
- Clan Chess Puzzles & Position Challenges
"""

from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
import chess
from models.chess_model import ChessModel, FAMOUS_GAMES
from models.user_model import UserModel
from models.community_model import CommunityModel
from controllers.auth_controller import login_required

chess_bp = Blueprint('chess', __name__, url_prefix='/chess')

@chess_bp.route('/')
def index():
    """3D Smart Chess Studio View"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id) if user_id else None
    
    # User's recent games
    recent_games = ChessModel.get_user_games(user_id, limit=5) if user_id else []
    
    # User's clans / groups for challenges
    groups = CommunityModel.get_all_groups() if user_id else []
    
    return render_template(
        'chess/board.html',
        user=user,
        recent_games=recent_games,
        famous_games=list(FAMOUS_GAMES.values()),
        groups=groups
    )

@chess_bp.route('/new-game', methods=['POST'])
def new_game():
    data = request.get_json() or {}
    title = data.get('title', 'GoChess Smart Studio')
    game_mode = data.get('game_mode', 'ai')
    ai_level = int(data.get('ai_level', 2))
    board_theme = data.get('board_theme', 'obsidian')
    
    user_id = session.get('user_id', 1)  # Default fallback if guest
    
    game_id = ChessModel.create_game(
        user_id=user_id,
        title=title,
        game_mode=game_mode,
        ai_level=ai_level,
        board_theme=board_theme
    )
    
    board = chess.Board()
    hints = ChessModel.get_coach_hints(board)
    
    return jsonify({
        "status": "success",
        "game_id": game_id,
        "fen": board.fen(),
        "hints": hints
    })

@chess_bp.route('/move', methods=['POST'])
def make_move():
    data = request.get_json() or {}
    fen = data.get('fen', chess.STARTING_FEN)
    from_sq = data.get('from')
    to_sq = data.get('to')
    promotion = data.get('promotion', 'q')
    game_id = data.get('game_id')
    level = int(data.get('ai_level', 2))
    game_mode = data.get('game_mode', 'ai')
    
    try:
        board = chess.Board(fen)
    except Exception as e:
        return jsonify({"status": "error", "message": "Invalid FEN board state"}), 400

    if not from_sq or not to_sq:
        return jsonify({"status": "error", "message": "Missing move squares"}), 400

    # Build UCI move string
    move_uci = f"{from_sq}{to_sq}"
    
    # Check if this requires promotion
    move_candidate = chess.Move.from_uci(move_uci)
    if move_candidate not in board.legal_moves:
        # Try with promotion
        move_candidate = chess.Move.from_uci(f"{move_uci}{promotion.lower()}")
        if move_candidate not in board.legal_moves:
            return jsonify({
                "status": "illegal_move",
                "message": f"Move {move_uci} is illegal in current position."
            }), 400

    # Execute player move
    player_san = board.san(move_candidate)
    board.push(move_candidate)
    
    player_result = {
        "status": "success",
        "player_move": {
            "from": from_sq,
            "to": to_sq,
            "san": player_san,
            "uci": move_candidate.uci(),
            "captured": board.is_capture(move_candidate)
        },
        "fen": board.fen(),
        "is_check": board.is_check(),
        "is_game_over": board.is_game_over(),
        "result_message": None,
        "ai_move": None
    }

    if board.is_checkmate():
        player_result["result_message"] = "Checkmate! You win!"
        if game_id:
            ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'player')
        return jsonify(player_result)

    if board.is_stalemate() or board.is_insufficient_material() or board.is_fivefold_repetition():
        player_result["result_message"] = "Game Draw!"
        if game_id:
            ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'draw')
        return jsonify(player_result)

    # AI Turn
    if game_mode == 'ai' and not board.is_game_over():
        ai_move, ai_score = ChessModel.get_ai_move(board, level=level)
        if ai_move:
            ai_san = board.san(ai_move)
            ai_from = chess.square_name(ai_move.from_square)
            ai_to = chess.square_name(ai_move.to_square)
            ai_captured = board.is_capture(ai_move)
            
            board.push(ai_move)
            
            player_result["ai_move"] = {
                "from": ai_from,
                "to": ai_to,
                "san": ai_san,
                "uci": ai_move.uci(),
                "captured": ai_captured,
                "score": ai_score
            }
            player_result["fen"] = board.fen()
            player_result["is_check"] = board.is_check()
            player_result["is_game_over"] = board.is_game_over()
            
            if board.is_checkmate():
                player_result["result_message"] = "Checkmate! AI wins!"
                if game_id:
                    ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'ai')
            elif board.is_stalemate() or board.is_insufficient_material():
                player_result["result_message"] = "Game Draw!"
                if game_id:
                    ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'completed', 'draw')

    # Update state in DB
    if game_id:
        ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, 'active')

    # Compute new LED coach hints
    player_result["hints"] = ChessModel.get_coach_hints(board)

    return jsonify(player_result)

@chess_bp.route('/hint', methods=['POST'])
def get_hint():
    data = request.get_json() or {}
    fen = data.get('fen', chess.STARTING_FEN)
    try:
        board = chess.Board(fen)
        hints = ChessModel.get_coach_hints(board)
        return jsonify({"status": "success", "hints": hints})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@chess_bp.route('/famous/<game_id>')
def famous_game(game_id):
    playback = ChessModel.get_famous_game_playback(game_id)
    if not playback:
        return jsonify({"status": "error", "message": "Game not found"}), 404
    return jsonify({"status": "success", "playback": playback})

@chess_bp.route('/challenge-clan', methods=['POST'])
@login_required
def challenge_clan():
    data = request.get_json() or {}
    game_id = data.get('game_id')
    group_id = data.get('group_id')
    note = data.get('note', 'Can you solve this GoChess smart position?')
    user_id = session.get('user_id')
    
    if not game_id or not group_id:
        return jsonify({"status": "error", "message": "Missing game or clan target"}), 400
        
    chal_id = ChessModel.create_clan_challenge(game_id, group_id, user_id, note)
    return jsonify({"status": "success", "challenge_id": chal_id, "message": "Clan challenge dispatched to group!"})
