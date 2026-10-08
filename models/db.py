"""
CubePermutation AI - Database Layer (MySQL Engine with Automatic SQLite Fallback)
==================================================================================
MVC Model DB Handler:
- MySQL database connection manage kore (PyMySQL driver)
- Auto-creates 'cube_permutation' database ebong tables (users, solves, profiles)
- Jodi MySQL credentials unavailable thake, seamlessly SQLite e data persist kore.

All query operations are documented with Bangla comments (Banglish).
"""

import sqlite3
import pymysql
import pymysql.cursors
from config import Config

# Track active database type ('mysql' or 'sqlite')
ACTIVE_DB_TYPE = 'sqlite'

def try_mysql_connection():
    """
    MySQL server e connect korar cheshta kore:
    1. Prothome server level e connect kore database 'cube_permutation' create kore
    2. Tarpor database er sathe connection return kore
    """
    global ACTIVE_DB_TYPE
    try:
        # Step 1: Connect without selecting specific database to ensure it exists
        server_conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3
        )
        with server_conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        server_conn.commit()
        server_conn.close()

        # Step 2: Connect to the specific database
        db_conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        ACTIVE_DB_TYPE = 'mysql'
        return db_conn
    except Exception as e:
        ACTIVE_DB_TYPE = 'sqlite'
        return None

def get_db_connection():
    """
    Active database connection return kore (MySQL primary, SQLite fallback).
    """
    mysql_conn = try_mysql_connection()
    if mysql_conn is not None:
        return mysql_conn, 'mysql'
    
    # SQLite Fallback Connection
    sqlite_conn = sqlite3.connect(Config.SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    return sqlite_conn, 'sqlite'

def init_database():
    """
    Database tables initialize kore:
    1. `users` table: id, username, email, password_hash, bio, avatar_color, created_at
    2. `solves` table: id, user_id, scramble, solution, move_count, created_at
    """
    conn, db_type = get_db_connection()
    
    if db_type == 'mysql':
        print("[Database] Connected to MySQL Server successfully!")
        with conn.cursor() as cur:
            # Users Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    email VARCHAR(120) NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    bio VARCHAR(255) DEFAULT 'Group Theory Enthusiast & Speedcuber',
                    avatar_color VARCHAR(30) DEFAULT '#818cf8',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # Solves Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS solves (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    scramble TEXT NOT NULL,
                    solution TEXT NOT NULL,
                    move_count INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        conn.close()
    else:
        print("[Database] Using SQLite Engine (Local Storage: cubedata.db)")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                bio TEXT DEFAULT 'Group Theory Enthusiast & Speedcuber',
                avatar_color TEXT DEFAULT '#818cf8',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if bio and avatar_color columns exist in case table already existed
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        if 'bio' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT 'Group Theory Enthusiast & Speedcuber'")
        if 'avatar_color' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_color TEXT DEFAULT '#818cf8'")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                scramble TEXT NOT NULL,
                solution TEXT NOT NULL,
                move_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        conn.close()

def query_one(sql_mysql, sql_sqlite, params=()):
    """Single row fetch korar helper function (Cross-DB compatible)"""
    conn, db_type = get_db_connection()
    try:
        if db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute(sql_mysql, params)
                return cur.fetchone()
        else:
            cur = conn.cursor()
            cur.execute(sql_sqlite, params)
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()

def query_all(sql_mysql, sql_sqlite, params=()):
    """Multiple rows fetch korar helper function"""
    conn, db_type = get_db_connection()
    try:
        if db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute(sql_mysql, params)
                return cur.fetchall()
        else:
            cur = conn.cursor()
            cur.execute(sql_sqlite, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()

def execute_insert(sql_mysql, sql_sqlite, params=()):
    """Insert query execute kore newly generated ID return kore"""
    conn, db_type = get_db_connection()
    try:
        if db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute(sql_mysql, params)
                return cur.lastrowid
        else:
            cur = conn.cursor()
            cur.execute(sql_sqlite, params)
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()

def execute_update(sql_mysql, sql_sqlite, params=()):
    """Update ba Delete query execute kore affected rows return kore"""
    conn, db_type = get_db_connection()
    try:
        if db_type == 'mysql':
            with conn.cursor() as cur:
                return cur.execute(sql_mysql, params)
        else:
            cur = conn.cursor()
            res = cur.execute(sql_sqlite, params)
            conn.commit()
            return res.rowcount
    finally:
        conn.close()
