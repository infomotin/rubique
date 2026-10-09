"""
CubePermutation AI - Card Game Controller (MVC Architecture)
============================================================
CyberDeck Memory & Algorithm Matching Protocol:
Guarded by Super Admin Feature Flag and Anti-Cheat Security Engine.
"""

import time
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from models.user_model import UserModel
from models.card_model import CardModel, CARD_SYMBOLS
from models.security_model import SecurityModel

card_bp = Blueprint('card', __name__, url_prefix='/cards')

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

    return render_template(
        'card/game.html',
        user=user,
        active_page='card_game',
        symbols=CARD_SYMBOLS,
        saved_games=saved_games,
        is_override=admin_override
    )

@card_bp.route('/new-game', methods=['POST'])
def new_game():
    """Initializes a new randomized CyberDeck matching session"""
    user_id = session.get('user_id') or 1
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
def pause_game(game_id):
    user_id = session.get('user_id')
    CardModel.pause_game(game_id, user_id)
    return jsonify({"status": "success", "message": "Card play stage paused!"})

@card_bp.route('/game/<int:game_id>/resume', methods=['POST'])
def resume_game(game_id):
    user_id = session.get('user_id')
    game = CardModel.resume_game(game_id, user_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404
    return jsonify({"status": "success", "game": game})

@card_bp.route('/game/<int:game_id>/destroy', methods=['POST', 'DELETE'])
def destroy_game(game_id):
    user_id = session.get('user_id')
    CardModel.destroy_game(game_id, user_id)
    return jsonify({"status": "success", "message": "Card stage destroyed."})
