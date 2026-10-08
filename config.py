"""
CubePermutation AI - Configuration Module
==========================================
Database credentials, session secrets, and application environment settings.
"""

import os

class Config:
    # Flask Secret Key for secure sessions
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cube_permutation_group_theory_mvc_super_key_2026')
    
    # MySQL Database Settings (Default for Laragon / XAMPP / Localhost)
    # Laragon e default user holo 'root', password empty ba configurable
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'cube_permutation')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    
    # SQLite Fallback DB Path
    SQLITE_DB = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cubedata.db')
    
    # Upload folder
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
