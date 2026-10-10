"""
CubePermutation AI - MVC Application Entrypoint
================================================
Production-Grade Flask Server with Modular MVC Pattern, MySQL Database Engine,
OpenCV Image Preprocessing, and Kociemba Two-Phase Algorithm Solver.
"""

import os
from flask import Flask
from config import Config
from models import init_database
from controllers import (
    home_bp, auth_bp, super_admin_bp, developer_bp,
    user_bp, visualizer_bp, profile_bp, api_bp, custom_cube_bp, chess_bp,
    card_bp, card_club_bp, feed_bp
)

import json
from flask import session, request, redirect, jsonify
from translations import TRANSLATIONS, get_text


def create_app():
    """
    Flask Application Factory (Modular MVC Setup with Multi-Role RBAC & i18n):
    1. Configuration load kore
    2. MySQL / SQLite database schema initialize kore
    3. Multi-Role Blueprints (Controllers) register kore
    4. Multi-Language (i18n) Engine context processor register kore
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Database Tables (Users, Solves, Competitions, Courses, Coupons, Logs)
    with app.app_context():
        init_database()

    # Register MVC Blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(developer_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(visualizer_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(custom_cube_bp)
    app.register_blueprint(chess_bp)
    app.register_blueprint(card_bp)
    app.register_blueprint(card_club_bp)
    app.register_blueprint(feed_bp)

    # Card Club live tables (Socket.IO - websocket push + HTTP polling fallback)
    from controllers.card_club_controller import init_socketio
    socketio = init_socketio(app)

    # Multi-Language (i18n) Context Processor
    @app.context_processor
    def inject_i18n():
        lang = session.get('lang', 'en')
        def t(key, default=''):
            return get_text(key, lang, default)
        return {
            'current_lang': lang,
            't': t,
            'translations_json': json.dumps(TRANSLATIONS)
        }

    # Language Switcher Route
    @app.route('/set-language/<lang>', methods=['GET', 'POST'])
    def set_language(lang):
        if lang in TRANSLATIONS:
            session['lang'] = lang
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'lang': session.get('lang', 'en')})
        referrer = request.referrer or '/'
        return redirect(referrer)

    return app

app = create_app()
socketio = app.extensions.get('socketio') or None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"CubePermutation AI MVC Server shuru hocche port {port} e...")
    print(f"Browser e open korun: http://127.0.0.1:{port}")
    from engineio.async_drivers import threading  # noqa: F401 (threading driver)
    socketio.run(app, host='127.0.0.1', port=port, debug=True,
                 allow_unsafe_werkzeug=True)
