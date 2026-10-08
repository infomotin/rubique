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
from controllers import home_bp, auth_bp, visualizer_bp, profile_bp, api_bp

def create_app():
    """
    Flask Application Factory (Modular MVC Setup):
    1. Configuration load kore
    2. MySQL / SQLite database schema initialize kore
    3. Blueprints (Controllers) register kore
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Database Tables (Users, Solves)
    with app.app_context():
        init_database()

    # Register MVC Blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(visualizer_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(api_bp)

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"CubePermutation AI MVC Server shuru hocche port {port} e...")
    print(f"Browser e open korun: http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
