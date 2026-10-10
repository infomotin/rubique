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
from functools import wraps
import chess
import time
from models.chess_model import ChessModel, FAMOUS_GAMES
from models.user_model import UserModel
from models.community_model import CommunityModel
from models.security_model import SecurityModel
from controllers.auth_controller import login_required

chess_bp = Blueprint('chess', __name__, url_prefix='/chess')

ALLOWED_MATCH_TYPES = ('pvp', 'open', 'public', 'group_vs_group', 'group_vs_public')
GROUP_MATCH_TYPES = ('group_vs_group', 'group_vs_public')


def api_login_required(f):
    """JSON endpoints answer 401 instead of redirecting guests to the login page."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "Please log in to use the chess arena."}), 401
        return f(*args, **kwargs)
    return wrapper

@chess_bp.route('/')
def index():
    """3D Smart Chess Studio View"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id) if user_id else None
    role = user.get('role') if user else session.get('role', 'guest')
    client_ip = request.remote_addr or '127.0.0.1'

    # Super Admin Feature Flag Gate
    is_enabled = SecurityModel.is_game_enabled('chess')
    admin_override = request.args.get('admin_override') == '1' and role in ['super_admin', 'developer']

    if not is_enabled and not admin_override:
        SecurityModel.log_security_event(
            game_type='chess',
            event_type='MAINTENANCE_BLOCKED',
            severity='info',
            details=f"User #{user_id or 'guest'} attempted to access disabled Chess Game.",
            user_id=user_id,
            client_ip=client_ip
        )
        return render_template(
            'maintenance_game.html',
            user=user,
            game_title="3D Smart Chess Board",
            game_icon="fa-solid fa-chess-knight",
            override_url=url_for('chess.index', admin_override=1)
        ), 503

    # Bit-Level Developer Telemetry Log
    t0 = time.perf_counter()

    # User's recent games
    recent_games = ChessModel.get_user_games(user_id, limit=5) if user_id else []
    
    # User's clans / groups for challenges
    groups = CommunityModel.get_all_groups() if user_id else []

    # Super Admin Hard Problems
    problems = ChessModel.get_problems(limit=30)

    # Active Multiplayer Matches (1v1, Clan vs Clan, Clan vs Public)
    multiplayer_matches = ChessModel.get_multiplayer_matches(limit=20)

    # Invitations: direct subscriber invites + clan (group) invites
    received_invitations = ChessModel.get_received_invitations(user_id, limit=15) if user_id else []
    sent_invitations = ChessModel.get_sent_invitations(user_id, limit=15) if user_id else []

    # Clans this subscriber leads or rostered in (Group vs Group seats)
    my_groups = []
    if user_id:
        my_groups = [g for g in groups if ChessModel.is_clan_member(g.get('id'), user_id)]

    # User's Saved Play Stages across all styles (AI, 1v1, Clan vs Clan, Clan vs Public)
    effective_user_id = user_id or 1
    saved_stages = ChessModel.get_user_saved_stages(effective_user_id, limit=50)

    latency_ms = (time.perf_counter() - t0) * 1000
    SecurityModel.log_telemetry_bit(
        module='CHESS_XR',
        action='STUDIO_LOAD',
        payload_data=f"user={user_id}&stages={len(saved_stages)}&matches={len(multiplayer_matches)}",
        latency_ms=latency_ms,
        http_status=200,
        severity='INFO',
        user_id=user_id,
        role=role,
        client_ip=client_ip
    )
    
    return render_template(
        'chess/board.html',
        user=user,
        active_page='chess',
        recent_games=recent_games,
        famous_games=list(FAMOUS_GAMES.values()),
        problems=problems,
        multiplayer_matches=multiplayer_matches,
        received_invitations=received_invitations,
        sent_invitations=sent_invitations,
        my_groups=my_groups,
        saved_stages=saved_stages,
        groups=groups,
        is_override=admin_override
    )

from services.chess_service import ChessService
from utils.decorators import login_required, api_login_required

@chess_bp.route('/new-game', methods=['POST'])
def new_game():
    data = request.get_json() or {}
    title = data.get('title', 'GoChess Smart Studio')
    game_mode = data.get('game_mode', 'ai')
    ai_level = int(data.get('ai_level', 2))
    board_theme = data.get('board_theme', 'obsidian')
    user_id = session.get('user_id', 1)

    result = ChessService.start_game(
        user_id=user_id,
        title=title,
        game_mode=game_mode,
        ai_level=ai_level,
        board_theme=board_theme
    )
    return jsonify(result)

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
    user_id = session.get('user_id')
    client_ip = request.remote_addr or '127.0.0.1'

    ok, result, code = ChessService.process_player_move(
        fen=fen,
        from_sq=from_sq,
        to_sq=to_sq,
        promotion=promotion,
        game_id=game_id,
        ai_level=level,
        game_mode=game_mode,
        user_id=user_id,
        client_ip=client_ip
    )
    return jsonify(result), code

@chess_bp.route('/ai-move', methods=['POST'])
def trigger_ai_move():
    """Forces or triggers an autonomous AI move for the active position."""
    data = request.get_json() or {}
    fen = data.get('fen', chess.STARTING_FEN)
    level = int(data.get('ai_level', 2))
    game_id = data.get('game_id')
    ok, result, code = ChessService.trigger_ai_turn(
        fen=fen,
        ai_level=level,
        game_id=game_id
    )
    return jsonify(result), code

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
    """Create Open / Public / 1v1 / Group vs Group / Group vs Public match"""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    match_type = data.get('match_type', 'pvp')  # 'pvp', 'open', 'public', 'group_vs_group', 'group_vs_public'
    title = data.get('title', 'Cyber Arena Match') or 'Cyber Arena Match'
    white_group_id = data.get('white_group_id')
    black_group_id = data.get('black_group_id')
    is_public = int(data.get('is_public', 1))

    if match_type not in ALLOWED_MATCH_TYPES:
        return jsonify({
            "status": "error",
            "message": f"Unknown match type '{match_type}'. Choose one of: {', '.join(ALLOWED_MATCH_TYPES)}."
        }), 400

    # Open lobby & Public arena are discoverable by every subscriber
    if match_type in ('open', 'public'):
        is_public = 1

    if match_type in GROUP_MATCH_TYPES:
        if not white_group_id:
            return jsonify({"status": "error", "message": "Pick your clan first (White team)."}), 400
        if not ChessModel.is_clan_member(white_group_id, user_id):
            return jsonify({"status": "error", "message": "You can only field a clan you lead or are rostered in."}), 403
        if match_type == 'group_vs_group':
            try:
                black_group_id = int(black_group_id)
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Pick the rival clan you want to challenge."}), 400
            group_exists = any(g.get('id') == black_group_id for g in CommunityModel.get_all_groups())
            if not group_exists:
                return jsonify({"status": "error", "message": "Rival clan not found."}), 404

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
        "seat": "white",
        "is_public": is_public,
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
def make_multiplayer_move(game_id):
    """Make move in multiplayer / clan vs clan / group vs public battle"""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    from_sq = data.get('from')
    to_sq = data.get('to')
    promotion = data.get('promotion', 'q')
    team = data.get('team', 'white')
    comment = data.get('comment', '')

    if team not in ('white', 'black'):
        return jsonify({"status": "error", "message": "Team must be 'white' or 'black'"}), 400

    game = ChessModel.get_game(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Match not found"}), 404

    if game.get('status') not in ('active', 'paused'):
        return jsonify({"status": "error", "message": "This match is already closed."}), 409

    # Seat enforcement: only the seated subscriber may move their own colour
    has_seats = bool(game.get('white_user_id') or game.get('black_user_id'))
    if has_seats:
        seat = 'white' if game.get('white_user_id') == user_id else (
            'black' if game.get('black_user_id') == user_id else None)
        if seat is None:
            return jsonify({"status": "error", "message": "You are not seated in this match."}), 403
        if seat != team:
            return jsonify({
                "status": "error",
                "message": f"You are seated as {seat.capitalize()} — play for the {seat} team."
            }), 403

    board = chess.Board(game['fen'])

    # Turn enforcement: the side on move must match the claimed team
    if board.turn != (chess.WHITE if team == 'white' else chess.BLACK):
        return jsonify({"status": "error", "message": f"Not {team}'s turn."}), 409

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
# INVITATIONS: DIRECT SUBSCRIBER INVITES & CLAN (GROUP) INVITES
# =============================================================================
@chess_bp.route('/invitations/search')
@api_login_required
def search_subscribers():
    """Type-ahead search for the invitation modal"""
    q = request.args.get('q', '').strip()
    user_id = session.get('user_id')
    users = UserModel.search_users(q, exclude_user_id=user_id, limit=8) if q else []
    return jsonify({
        "status": "success",
        "users": [{"id": u['id'], "username": u['username']} for u in users]
    })

@chess_bp.route('/invitations')
@api_login_required
def list_invitations():
    """Pending invitations this subscriber received + the ones they sent"""
    user_id = session.get('user_id')
    return jsonify({
        "status": "success",
        "received": ChessModel.get_received_invitations(user_id, limit=20),
        "sent": ChessModel.get_sent_invitations(user_id, limit=20)
    })

@chess_bp.route('/invitations/send', methods=['POST'])
@api_login_required
def send_invitation():
    """Invite a subscriber (1v1) or a rival clan (Group vs Group / Group vs Public)"""
    user_id = session.get('user_id')
    data = request.get_json() or {}

    to_user_id = data.get('to_user_id')
    to_username = (data.get('to_username') or '').strip()
    to_group_id = data.get('to_group_id')
    my_group_id = data.get('my_group_id')
    title = (data.get('title') or '').strip() or 'Invitation Battle'
    message = (data.get('message') or '').strip()[:250]

    if to_username and not to_user_id:
        target = UserModel.find_by_username(to_username)
        if not target:
            return jsonify({"status": "error", "message": f'No subscriber named "{to_username}".'}), 404
        to_user_id = target['id']

    if to_user_id:
        try:
            to_user_id = int(to_user_id)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid subscriber target."}), 400
    if to_group_id:
        try:
            to_group_id = int(to_group_id)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid clan target."}), 400
    if my_group_id:
        try:
            my_group_id = int(my_group_id)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid clan for your side."}), 400

    if bool(to_user_id) == bool(to_group_id):
        return jsonify({"status": "error", "message": "Pick exactly one target: a subscriber or a clan."}), 400

    if to_user_id and to_user_id == user_id:
        return jsonify({"status": "error", "message": "You cannot invite yourself."}), 400

    if to_group_id:
        all_groups = CommunityModel.get_all_groups()
        target_group = next((g for g in all_groups if g.get('id') == to_group_id), None)
        if not target_group:
            return jsonify({"status": "error", "message": "Target clan not found."}), 404

        match_type = 'group_vs_group'
        white_group_id = None
        if my_group_id:
            if not ChessModel.is_clan_member(my_group_id, user_id):
                return jsonify({"status": "error", "message": "You can only field a clan you lead or are rostered in."}), 403
            white_group_id = my_group_id
        else:
            match_type = 'group_vs_public'

        game_id = ChessModel.create_multiplayer_match(
            user_id=user_id,
            match_type=match_type,
            title=title,
            white_group_id=white_group_id,
            black_group_id=to_group_id,
            is_public=0
        )
        invitation_id = ChessModel.create_invitation(
            game_id=game_id,
            from_user_id=user_id,
            to_group_id=to_group_id,
            message=message
        )
        return jsonify({
            "status": "success",
            "invitation_id": invitation_id,
            "game_id": game_id,
            "match_type": match_type,
            "message": f'Invite sent to clan "{target_group["name"]}"!'
        })

    # Direct subscriber invite → private 1v1, host holds White
    game_id = ChessModel.create_multiplayer_match(
        user_id=user_id,
        match_type='pvp',
        title=title,
        is_public=0
    )
    invitation_id = ChessModel.create_invitation(
        game_id=game_id,
        from_user_id=user_id,
        to_user_id=int(to_user_id),
        message=message
    )
    return jsonify({
        "status": "success",
        "invitation_id": invitation_id,
        "game_id": game_id,
        "match_type": 'pvp',
        "message": "Invitation dispatched!"
    })

@chess_bp.route('/invitations/<int:invitation_id>/accept', methods=['POST'])
@api_login_required
def accept_invitation(invitation_id):
    """Accept an invite and take the open seat"""
    user_id = session.get('user_id')
    invitation = ChessModel.get_invitation(invitation_id)
    if not invitation:
        return jsonify({"status": "error", "message": "Invitation not found."}), 404

    if invitation.get('status') != 'pending':
        return jsonify({"status": "error", "message": f"Invitation already {invitation.get('status')}."}), 409

    is_direct_target = invitation.get('to_user_id') == user_id
    is_clan_target = bool(invitation.get('to_group_id')) and ChessModel.is_clan_member(
        invitation.get('to_group_id'), user_id)
    if not (is_direct_target or is_clan_target):
        return jsonify({"status": "error", "message": "This invitation is not addressed to you."}), 403

    seat_result = ChessModel.join_multiplayer_match(invitation.get('game_id'), user_id)
    if seat_result.get('status') == 'error':
        return jsonify(seat_result), seat_result.get('code', 400)

    ChessModel.set_invitation_status(invitation_id, 'accepted')
    return jsonify({
        "status": "success",
        "seat": seat_result.get('seat'),
        "game_id": invitation.get('game_id'),
        "message": seat_result.get('message', 'Invitation accepted!')
    })

@chess_bp.route('/invitations/<int:invitation_id>/decline', methods=['POST'])
@api_login_required
def decline_invitation(invitation_id):
    """Decline an invite"""
    user_id = session.get('user_id')
    invitation = ChessModel.get_invitation(invitation_id)
    if not invitation:
        return jsonify({"status": "error", "message": "Invitation not found."}), 404

    if invitation.get('status') != 'pending':
        return jsonify({"status": "error", "message": f"Invitation already {invitation.get('status')}."}), 409

    is_direct_target = invitation.get('to_user_id') == user_id
    is_clan_target = bool(invitation.get('to_group_id')) and ChessModel.is_clan_member(
        invitation.get('to_group_id'), user_id)
    if not (is_direct_target or is_clan_target):
        return jsonify({"status": "error", "message": "This invitation is not addressed to you."}), 403

    ChessModel.set_invitation_status(invitation_id, 'declined')
    return jsonify({"status": "success", "message": "Invitation declined."})

# =============================================================================
# JOIN & QUICK PAIR: OPEN TO ALL SUBSCRIBERS / PUBLIC VS PUBLIC
# =============================================================================
@chess_bp.route('/multiplayer/<int:game_id>/join', methods=['POST'])
@api_login_required
def join_multiplayer(game_id):
    """Take the free seat in an Open / Public / Clan battle"""
    user_id = session.get('user_id')
    result = ChessModel.join_multiplayer_match(game_id, user_id)
    if result.get('status') == 'error':
        return jsonify(result), result.get('code', 400)
    return jsonify(result)

@chess_bp.route('/multiplayer/quick-pair', methods=['POST'])
@api_login_required
def quick_pair():
    """Jump into a waiting Public vs Public table, otherwise host one"""
    user_id = session.get('user_id')
    waiting = ChessModel.find_joinable_public_match(user_id)
    if waiting:
        result = ChessModel.join_multiplayer_match(waiting['id'], user_id)
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "joined": True,
                "game_id": waiting['id'],
                "seat": result.get('seat'),
                "message": f'Paired into "{waiting.get("title")}" as {result.get("seat", "").capitalize()}!'
            })

    game_id = ChessModel.create_multiplayer_match(
        user_id=user_id,
        match_type='public',
        title=f"Public Arena — {session.get('username', 'open seat')}",
        is_public=1
    )
    return jsonify({
        "status": "success",
        "joined": False,
        "game_id": game_id,
        "seat": "white",
        "message": "No open table found — you are hosting a Public vs Public battle."
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

