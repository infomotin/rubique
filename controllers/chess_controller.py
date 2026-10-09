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

    # Super Admin Hard Problems
    problems = ChessModel.get_problems(limit=30)

    # Active Multiplayer Matches (1v1, Clan vs Clan, Clan vs Public)
    multiplayer_matches = ChessModel.get_multiplayer_matches(limit=20)

    # User's Saved Play Stages across all styles (AI, 1v1, Clan vs Clan, Clan vs Public)
    effective_user_id = user_id or 1
    saved_stages = ChessModel.get_user_saved_stages(effective_user_id, limit=50)
    
    return render_template(
        'chess/board.html',
        user=user,
        active_page='chess',
        recent_games=recent_games,
        famous_games=list(FAMOUS_GAMES.values()),
        problems=problems,
        multiplayer_matches=multiplayer_matches,
        saved_stages=saved_stages,
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
    player_captured = board.is_capture(move_candidate)
    board.push(move_candidate)
    
    player_result = {
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

# =============================================================================
# SUPER ADMIN HARD CHESS PROBLEMS & SUBSCRIBER SUBMISSIONS
# =============================================================================
@chess_bp.route('/problems')
def list_problems():
    """List of all Super Admin Grandmaster Chess Problems"""
    problems = ChessModel.get_problems(limit=50)
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id) if user_id else None
    return jsonify({
        "status": "success",
        "problems": problems,
        "is_admin": (user and user.get('role') == 'super_admin')
    })

@chess_bp.route('/problems/<int:problem_id>')
def get_problem_details(problem_id):
    """Get single problem details for loading into GoChess 3D board"""
    problem = ChessModel.get_problem(problem_id)
    if not problem:
        return jsonify({"status": "error", "message": "Problem not found"}), 404
    submissions = ChessModel.get_problem_submissions(problem_id)
    return jsonify({
        "status": "success",
        "problem": problem,
        "submissions": submissions
    })

@chess_bp.route('/problems/create', methods=['POST'])
@login_required
def create_problem():
    """Super Admin posts a new Very Hard Chess Problem"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    if not user or user.get('role') != 'super_admin':
        return jsonify({"status": "error", "message": "Only Super Admin can author official Master Problems"}), 403

    data = request.get_json() or {}
    title = data.get('title', 'Grandmaster Tactical Challenge')
    difficulty = data.get('difficulty', 'Grandmaster (2400 ELO)')
    fen = data.get('fen', '').strip()
    solution_moves = data.get('solution_moves', '').strip()
    hint = data.get('hint', '')
    xp_reward = int(data.get('xp_reward', 150))

    if not fen or not solution_moves:
        return jsonify({"status": "error", "message": "FEN and Solution moves are required"}), 400

    # Validate FEN
    try:
        _vboard = chess.Board(fen)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid FEN board position"}), 400

    # Validate the official solution line is legal from the FEN (prevents unsolvable problems)
    sol_tokens = [m.strip() for m in solution_moves.replace(';', ',').split(',') if m.strip()]
    if not sol_tokens:
        return jsonify({"status": "error", "message": "FEN and Solution moves are required"}), 400
    for tok in sol_tokens:
        _mv = ChessModel._parse_move_token(_vboard, tok)
        if _mv is None:
            return jsonify({
                "status": "error",
                "message": f"Solution move '{tok}' is not legal from the FEN (use UCI like d3h7 or SAN like Bxh7+)"
            }), 400
        _vboard.push(_mv)

    problem_id = ChessModel.create_problem(
        author_id=user_id,
        title=title,
        difficulty=difficulty,
        fen=fen,
        solution_moves=solution_moves,
        hint=hint,
        xp_reward=xp_reward
    )

    return jsonify({
        "status": "success",
        "problem_id": problem_id,
        "message": "Grandmaster Problem published successfully for subscribers!"
    })

@chess_bp.route('/problems/<int:problem_id>/submit', methods=['POST'])
@login_required
def submit_solution(problem_id):
    """Subscriber tries their own moves and submits their solution"""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    submitted_moves = data.get('moves', '').strip()

    if not submitted_moves:
        return jsonify({"status": "error", "message": "No moves provided for submission"}), 400

    result = ChessModel.verify_and_submit_solution(problem_id, user_id, submitted_moves)
    return jsonify(result)

# =============================================================================
# MULTIPLAYER MATCHMAKING: 1v1, GROUP VS GROUP, GROUP VS PUBLIC
# =============================================================================
@chess_bp.route('/multiplayer')
def multiplayer_arena():
    """List all active multiplayer battles"""
    match_type = request.args.get('type')
    matches = ChessModel.get_multiplayer_matches(match_type=match_type, limit=30)
    return jsonify({
        "status": "success",
        "matches": matches
    })

@chess_bp.route('/multiplayer/create', methods=['POST'])
@login_required
def create_multiplayer_game():
    """Create 1v1, Group vs Group, or Group vs Public match"""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    match_type = data.get('match_type', 'pvp')  # 'pvp', 'group_vs_group', 'group_vs_public'
    title = data.get('title', 'Cyber Arena Match')
    white_group_id = data.get('white_group_id')
    black_group_id = data.get('black_group_id')
    is_public = int(data.get('is_public', 1))

    game_id = ChessModel.create_multiplayer_match(
        user_id=user_id,
        match_type=match_type,
        title=title,
        white_group_id=white_group_id,
        black_group_id=black_group_id,
        is_public=is_public
    )

    return jsonify({
        "status": "success",
        "game_id": game_id,
        "match_type": match_type,
        "message": f"Multiplayer match '{title}' initiated!"
    })

@chess_bp.route('/multiplayer/<int:game_id>/state')
def get_multiplayer_state(game_id):
    """Get live state and team moves for a multiplayer match"""
    game = ChessModel.get_game(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Match not found"}), 404
    team_moves = ChessModel.get_game_team_moves(game_id)
    return jsonify({
        "status": "success",
        "game": game,
        "team_moves": team_moves
    })

@chess_bp.route('/multiplayer/<int:game_id>/move', methods=['POST'])
@login_required
def make_multiplayer_move():
    """Make move in multiplayer / clan vs clan / group vs public battle"""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    game_id = data.get('game_id', game_id)
    from_sq = data.get('from')
    to_sq = data.get('to')
    promotion = data.get('promotion', 'q')
    team = data.get('team', 'white')
    comment = data.get('comment', '')

    game = ChessModel.get_game(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Match not found"}), 404

    board = chess.Board(game['fen'])
    move_uci = f"{from_sq}{to_sq}"
    move_candidate = chess.Move.from_uci(move_uci)
    if move_candidate not in board.legal_moves:
        move_candidate = chess.Move.from_uci(f"{move_uci}{promotion.lower()}")
        if move_candidate not in board.legal_moves:
            return jsonify({"status": "error", "message": f"Illegal move {move_uci}"}), 400

    move_san = board.san(move_candidate)
    board.push(move_candidate)

    # Record team move
    ChessModel.record_team_move(game_id, user_id, team, move_candidate.uci(), move_san, comment)

    # Update game FEN & moves count
    winner = None
    status = 'active'
    if board.is_checkmate():
        status = 'completed'
        winner = team
    elif board.is_stalemate() or board.is_insufficient_material():
        status = 'completed'
        winner = 'draw'

    ChessModel.update_game_state(game_id, board.fen(), "", board.fullmove_number, status, winner)

    return jsonify({
        "status": "success",
        "move": {"from": from_sq, "to": to_sq, "san": move_san, "uci": move_candidate.uci()},
        "fen": board.fen(),
        "is_check": board.is_check(),
        "is_game_over": board.is_game_over(),
        "winner": winner
    })

# =============================================================================
# PLAY STAGE LIFECYCLE: STORE, PAUSE / STOP, RESUME, DESTROY, STYLE FILTERING
# =============================================================================
@chess_bp.route('/saved-stages')
def get_saved_stages():
    """Retrieve all play stages stored for the player across each style"""
    user_id = session.get('user_id') or 1
    style = request.args.get('style') or request.args.get('match_type')
    stages = ChessModel.get_user_saved_stages(user_id, match_type=style, limit=50)
    return jsonify({"status": "success", "stages": stages})

@chess_bp.route('/game/<int:game_id>/pause', methods=['POST'])
def pause_game_stage(game_id):
    """Stop / Pause play stage: preserves exact board state and frozen clock"""
    user_id = session.get('user_id') or 1
    data = request.get_json() or {}
    fen = data.get('fen')
    moves_count = data.get('moves_count')
    ChessModel.pause_game(game_id, user_id, fen=fen, moves_count=moves_count)
    return jsonify({"status": "success", "message": "Play stage paused and safely stored!"})

@chess_bp.route('/game/<int:game_id>/resume', methods=['POST'])
def resume_game_stage(game_id):
    """Resume stored play stage from exact position and move count"""
    user_id = session.get('user_id') or 1
    game = ChessModel.resume_game(game_id, user_id)
    if not game:
        return jsonify({"status": "error", "message": "Game stage not found"}), 404
    board = chess.Board(game['fen'])
    hints = ChessModel.get_coach_hints(board)
    return jsonify({
        "status": "success",
        "game": game,
        "fen": game['fen'],
        "moves_count": game['moves_count'],
        "hints": hints,
        "message": f"Resumed stage: {game['title']}"
    })

@chess_bp.route('/game/<int:game_id>/destroy', methods=['POST', 'DELETE'])
def destroy_game_stage(game_id):
    """Permanently destroy / discard saved play stage"""
    user_id = session.get('user_id') or 1
    ChessModel.destroy_game(game_id, user_id)
    return jsonify({"status": "success", "message": "Play stage permanently destroyed."})

@chess_bp.route('/game/<int:game_id>/save-title', methods=['POST'])
def save_stage_title(game_id):
    """Update title / custom label for a stored play stage"""
    user_id = session.get('user_id') or 1
    data = request.get_json() or {}
    title = data.get('title')
    if not title:
        return jsonify({"status": "error", "message": "Title required"}), 400
    game = ChessModel.save_stage_snapshot(game_id, user_id, title=title)
    return jsonify({"status": "success", "game": game, "message": "Stage title updated!"})

