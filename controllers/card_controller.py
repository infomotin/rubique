"""
CubePermutation AI - Card Game Controller (MVC Architecture)
============================================================
CyberDeck Memory & Algorithm Matching Protocol:
Guarded by Super Admin Feature Flag and Anti-Cheat Security Engine.
"""

import time
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from controllers.auth_controller import login_required
from utils.decorators import api_login_required
from models.user_model import UserModel
from models.card_model import CardModel, CARD_SYMBOLS
from models.security_model import SecurityModel
from models import classic_arena as arena_store
from models.card_club.errors import CardClubError, NotFoundError, PermissionDenied
from models.card_club.engines.classic_tricks import (
    CLASSIC_CATALOG, GAME_ENGINES
)

card_bp = Blueprint('card', __name__, url_prefix='/cards')


def _owns_card_game(game):
    """True when the signed-in caller is the owner of this CyberDeck game."""
    if not game:
        return False
    owner = game.get('user_id')
    caller = session.get('user_id')
    if owner is None or not caller:
        return False
    try:
        return int(owner) == int(caller)
    except (TypeError, ValueError):
        return False

@card_bp.route('/')
def index():
    """CyberDeck Memory Card Protocol Arena View"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id) if user_id else None
    role = user.get('role') if user else session.get('role', 'guest')
    client_ip = request.remote_addr or '127.0.0.1'

    # Super Admin Feature Flag Gate
    is_enabled = SecurityModel.is_game_enabled('card')
    admin_override = request.args.get('admin_override') == '1' and role in ['super_admin', 'developer']

    if not is_enabled and not admin_override:
        # Log maintenance block event
        SecurityModel.log_security_event(
            game_type='card',
            event_type='MAINTENANCE_BLOCKED',
            severity='info',
            details=f"User #{user_id or 'guest'} attempted to access disabled Card Game.",
            user_id=user_id,
            client_ip=client_ip
        )
        return render_template(
            'maintenance_game.html',
            user=user,
            game_title="CyberDeck Memory Card Protocol",
            game_icon="fa-solid fa-clone",
            override_url=url_for('card.index', admin_override=1)
        ), 503

    # Bit-Level Developer Telemetry Log
    t0 = time.perf_counter()
    saved_games = CardModel.get_user_games(user_id, limit=20) if user_id else []
    latency_ms = (time.perf_counter() - t0) * 1000

    SecurityModel.log_telemetry_bit(
        module='CARD_ENGINE',
        action='ARENA_VIEW_LOAD',
        payload_data=f"user={user_id}&games={len(saved_games)}",
        latency_ms=latency_ms,
        http_status=200,
        severity='INFO',
        user_id=user_id,
        role=role,
        client_ip=client_ip
    )

    username = user.get('username') if user else session.get('username', '')
    is_speedcuber = (username == 'speedcuber') or (request.args.get('test_user') == 'speedcuber') or (request.args.get('account') == 'speedcuber')

    return render_template(
        'card/game.html',
        user=user,
        active_page='cards',
        symbols=CARD_SYMBOLS,
        saved_games=saved_games,
        is_override=admin_override,
        is_speedcuber=is_speedcuber
    )

@card_bp.route('/new-game', methods=['POST'])
@api_login_required
def new_game():
    """Initializes a new randomized CyberDeck matching session"""
    user_id = session.get('user_id')
    role = session.get('role', 'guest')
    client_ip = request.remote_addr or '127.0.0.1'

    if not SecurityModel.is_game_enabled('card') and role not in ['super_admin', 'developer']:
        return jsonify({"status": "error", "message": "Card game is currently disabled by Super Admin."}), 403

    t0 = time.perf_counter()
    data = request.get_json() or {}
    card_pairs = int(data.get('card_pairs', 8))
    card_pairs = max(4, min(card_pairs, 8))

    game_id, deck = CardModel.create_game(user_id=user_id, card_pairs=card_pairs)
    latency_ms = (time.perf_counter() - t0) * 1000

    SecurityModel.log_telemetry_bit(
        module='CARD_ENGINE',
        action='GAME_INITIALIZED',
        payload_data=f"game_id={game_id}&pairs={card_pairs}",
        latency_ms=latency_ms,
        http_status=200,
        severity='INFO',
        user_id=user_id,
        role=role,
        client_ip=client_ip
    )

    return jsonify({
        "status": "success",
        "game_id": game_id,
        "deck": deck,
        "total_cards": len(deck),
        "card_pairs": card_pairs
    })

@card_bp.route('/update-progress', methods=['POST'])
@api_login_required
def update_progress():
    """Updates move count, time elapsed, and matches for score calculation"""
    data = request.get_json() or {}
    game_id = data.get('game_id')
    moves = int(data.get('moves', 0))
    time_sec = int(data.get('time_seconds', 0))
    score = int(data.get('score', 0))
    status = data.get('status', 'active')
    deck_state = data.get('deck_state')
    user_id = session.get('user_id')
    role = session.get('role', 'guest')
    client_ip = request.remote_addr or '127.0.0.1'

    if not game_id:
        return jsonify({"status": "error", "message": "Game ID required"}), 400

    game = CardModel.get_game(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404
    if not _owns_card_game(game):
        return jsonify({"status": "error", "message": "Not your game."}), 403

    # Anti-Cheat check: Rapid move anomaly
    anti_cheat_on = SecurityModel.is_game_enabled('game_anti_cheat')
    if anti_cheat_on and moves > 10 and time_sec < 2:
        SecurityModel.log_security_event(
            game_type='card',
            game_id=game_id,
            event_type='RAPID_MOVE_ANOMALY',
            severity='warning',
            details=f"Suspicious card flip rate: {moves} flips in {time_sec}s.",
            user_id=user_id,
            client_ip=client_ip
        )

    CardModel.update_game(game_id, moves, time_sec, score, status, deck_state)

    SecurityModel.log_telemetry_bit(
        module='CARD_ENGINE',
        action='PROGRESS_RECORDED',
        payload_data=f"game_id={game_id}&moves={moves}&score={score}&status={status}",
        latency_ms=1.2,
        http_status=200,
        severity='INFO',
        user_id=user_id,
        role=role,
        client_ip=client_ip
    )

    return jsonify({"status": "success", "message": "Card game stage updated!"})

@card_bp.route('/game/<int:game_id>/pause', methods=['POST'])
@api_login_required
def pause_game(game_id):
    user_id = session.get('user_id')
    game = CardModel.get_game(game_id)
    if not game or not _owns_card_game(game):
        return jsonify({"status": "error", "message": "Game not found"}), 404
    CardModel.pause_game(game_id, user_id)
    return jsonify({"status": "success", "message": "Card play stage paused!"})

@card_bp.route('/game/<int:game_id>/resume', methods=['POST'])
@api_login_required
def resume_game(game_id):
    user_id = session.get('user_id')
    existing = CardModel.get_game(game_id)
    if not existing or not _owns_card_game(existing):
        return jsonify({"status": "error", "message": "Game not found"}), 404
    game = CardModel.resume_game(game_id, user_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404
    return jsonify({"status": "success", "game": game})

@card_bp.route('/game/<int:game_id>/destroy', methods=['POST', 'DELETE'])
@api_login_required
def destroy_game(game_id):
    user_id = session.get('user_id')
    game = CardModel.get_game(game_id)
    if not game or not _owns_card_game(game):
        return jsonify({"status": "error", "message": "Game not found"}), 404
    CardModel.destroy_game(game_id, user_id)
    return jsonify({"status": "success", "message": "Card stage destroyed."})


# =====================================================================
# CLASSIC PLAYING CARD SUITE (29, Bridge, Spades, Hearts, Whist, Oh Hell, Euchre)
# =====================================================================

def _user():
    """Classic Suite games are money games - they always need a seat owner."""
    uid = session.get('user_id')
    if not uid:
        return None
    return int(uid)


def _deny(err, status=400):
    code = status
    if isinstance(err, PermissionDenied):
        code = 403
    elif isinstance(err, NotFoundError):
        code = 404
    return jsonify({"ok": False, "error": str(err)}), code


def _body():
    data = request.get_json(silent=True) or request.form or {}
    return dict(data) if hasattr(data, 'items') else {}


@card_bp.route('/classic')
@login_required
def classic_arena():
    """Classic 4-Player Partnership & Trick-Taking Card Arena View"""
    user_id = _user()
    user = UserModel.find_by_id(user_id) if user_id else None
    active = arena_store.active_game_for(user_id) if user_id else None
    return render_template(
        'card/classic_arena.html',
        user=user,
        user_id=user_id,
        active_page='cards',
        catalog=CLASSIC_CATALOG,
        logged_in=bool(user_id),
        active_game_id=int(active['id']) if active else None,
        default_group_id=int(session.get('group_id') or 0)
    )


@card_bp.route('/classic/new-game', methods=['POST'])
@api_login_required
def classic_new_game():
    """Create a classic table: solo-vs-bots, or a lobby table for the group."""
    uid = _user()
    data = _body()
    try:
        game = arena_store.create_game(
            uid,
            data.get('slug', '29'),
            mode=data.get('mode', 'ai'),
            group_id=int(data.get('group_id') or 0),
            stake=int(data.get('stake') or 0),
        )
        return jsonify({"ok": True, "game_id": int(game["id"]),
                        "state": arena_store.view_for(game["id"], uid)})
    except CardClubError as e:
        return _deny(e)


@card_bp.route('/classic/join', methods=['POST'])
@api_login_required
def classic_join():
    uid = _user()
    data = _body()
    try:
        game_id = int(data.get('game_id') or 0)
        arena_store.join_game(uid, game_id)
        return jsonify({"ok": True, "game_id": game_id,
                        "state": arena_store.view_for(game_id, uid)})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("game_id required"))


@card_bp.route('/classic/start', methods=['POST'])
@api_login_required
def classic_start():
    uid = _user()
    data = _body()
    try:
        game_id = int(data.get('game_id') or 0)
        arena_store.start_game(uid, game_id)
        return jsonify({"ok": True, "game_id": game_id,
                        "state": arena_store.view_for(game_id, uid)})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("game_id required"))


@card_bp.route('/classic/leave', methods=['POST'])
@api_login_required
def classic_leave():
    uid = _user()
    data = _body()
    try:
        game_id = int(data.get('game_id') or 0)
        arena_store.leave_game(uid, game_id)
        return jsonify({"ok": True})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("game_id required"))


@card_bp.route('/classic/cancel', methods=['POST'])
@api_login_required
def classic_cancel():
    uid = _user()
    data = _body()
    try:
        game_id = int(data.get('game_id') or 0)
        arena_store.cancel_game(uid, game_id)
        return jsonify({"ok": True})
    except (CardClubError, ValueError, TypeError) as e:
        return _deny(e if isinstance(e, CardClubError)
                     else CardClubError("game_id required"))


@card_bp.route('/classic/tables', methods=['GET'])
@api_login_required
def classic_tables():
    uid = _user()
    group_id = request.args.get('group_id', type=int, default=0)
    if not group_id:
        return jsonify({"ok": True, "tables": [], "group_id": 0})
    try:
        from models.card_club import groups
        groups.require_member(group_id, uid)
    except CardClubError as e:
        return _deny(e)
    return jsonify({"ok": True, "group_id": group_id,
                    "tables": arena_store.list_group_games(group_id)})


@card_bp.route('/classic/action', methods=['POST'])
@api_login_required
def classic_action():
    """Server-validated move: illegal actions never reach the engine."""
    uid = _user()
    data = _body()
    game_id = data.pop('game_id', None)
    try:
        game_id = int(game_id) if game_id else None
    except (ValueError, TypeError):
        game_id = None

    game = (arena_store.get_game(game_id) if game_id
            else arena_store.active_game_for(uid))
    if not game:
        return _deny(NotFoundError("No classic table in play"))
    if arena_store.seat_index_of(game["id"], uid) is None:
        return _deny(PermissionDenied("You are not seated at this table"))

    try:
        view, settlement = arena_store.apply_action(game["id"], uid, data)
        return jsonify({"ok": True, "state": view, "settlement": settlement})
    except CardClubError as e:
        return _deny(e)
    except Exception as e:                       # engine-level rejection
        return jsonify({"ok": False, "error": str(e)}), 400


@card_bp.route('/classic/state', methods=['GET'])
@api_login_required
def classic_state():
    uid = _user()
    game_id = request.args.get('game_id', type=int)
    game = arena_store.active_game_for(uid, game_id)
    if not game:
        return jsonify({"ok": False, "error": "No classic table in play"}), 404
    return jsonify({"ok": True, "game_id": int(game["id"]),
                    "state": arena_store.view_for(game["id"], uid)})

