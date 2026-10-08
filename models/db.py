"""
CubePermutation AI - Database Layer (MySQL & SQLite Multi-Role Architecture)
=============================================================================
MVC Model DB Handler with Multi-Role RBAC:
- Super Admin, Developer, and Registered User support.
- Auto-creates tables: users, solves, competitions, competition_entries, courses, coupons, system_logs.
- Seeds default demo accounts for instant testing.
"""

import sqlite3
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash
from config import Config

ACTIVE_DB_TYPE = 'sqlite'

def try_mysql_connection():
    """MySQL server connect kore database create kore connection return kore"""
    global ACTIVE_DB_TYPE
    try:
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
    except Exception:
        ACTIVE_DB_TYPE = 'sqlite'
        return None

def get_db_connection():
    """Active DB connection return kore (MySQL or SQLite)"""
    mysql_conn = try_mysql_connection()
    if mysql_conn is not None:
        return mysql_conn, 'mysql'
    
    sqlite_conn = sqlite3.connect(Config.SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    return sqlite_conn, 'sqlite'

def init_database():
    """
    Database schema initialize kore ebong Multi-Role RBAC tables toiri kore:
    1. users (role: 'super_admin', 'developer', 'user')
    2. solves (cube history)
    3. competitions (declared by super admin)
    4. competition_entries (user participation)
    5. courses (group theory tutorials)
    6. coupons (rewards & discount codes)
    7. system_logs (dev telemetry & bug logs)
    """
    conn, db_type = get_db_connection()
    
    if db_type == 'mysql':
        print("[Database] Initializing MySQL Multi-Role RBAC Tables...")
        with conn.cursor() as cur:
            # 1. Users Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    email VARCHAR(120) NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(30) DEFAULT 'user',
                    bio VARCHAR(255) DEFAULT 'Group Theory Explorer & Speedcuber',
                    avatar_color VARCHAR(30) DEFAULT '#818cf8',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 2. Solves Table
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
            # 3. Competitions Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS competitions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    scramble VARCHAR(255) NOT NULL,
                    prize_trophy VARCHAR(100) DEFAULT 'Golden Polyhedron',
                    status VARCHAR(30) DEFAULT 'active',
                    created_by INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 4. Competition Entries Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS competition_entries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    competition_id INT NOT NULL,
                    user_id INT NOT NULL,
                    move_count INT NOT NULL,
                    time_seconds FLOAT DEFAULT 0.0,
                    solution TEXT,
                    status VARCHAR(30) DEFAULT 'verified',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (competition_id) REFERENCES competitions(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 5. Courses Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    difficulty VARCHAR(30) DEFAULT 'Intermediate',
                    modules_count INT DEFAULT 5,
                    author VARCHAR(80) DEFAULT 'Super Admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 6. Coupons Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS coupons (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(50) NOT NULL UNIQUE,
                    reward_text VARCHAR(150) NOT NULL,
                    discount_percent INT DEFAULT 100,
                    status VARCHAR(30) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 7. System Logs Table (for Developer HUD)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    level VARCHAR(20) DEFAULT 'INFO',
                    module VARCHAR(50) DEFAULT 'SolverEngine',
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        conn.close()
    else:
        print("[Database] Initializing SQLite Multi-Role RBAC Tables...")
        cur = conn.cursor()
        
        # 1. Users Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                bio TEXT DEFAULT 'Group Theory Explorer & Speedcuber',
                avatar_color TEXT DEFAULT '#818cf8',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Auto-migrate role column if not present
        cur.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in cur.fetchall()]
        if 'role' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        if 'bio' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT 'Group Theory Explorer & Speedcuber'")
        if 'avatar_color' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN avatar_color TEXT DEFAULT '#818cf8'")

        # 2. Solves Table
        cur.execute("""
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

        # 3. Competitions Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS competitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                scramble TEXT NOT NULL,
                prize_trophy TEXT DEFAULT 'Golden Polyhedron',
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Competition Entries Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS competition_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                move_count INTEGER NOT NULL,
                time_seconds REAL DEFAULT 0.0,
                solution TEXT,
                status TEXT DEFAULT 'verified',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (competition_id) REFERENCES competitions(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 5. Courses Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                difficulty TEXT DEFAULT 'Intermediate',
                modules_count INTEGER DEFAULT 5,
                author TEXT DEFAULT 'Super Admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Coupons Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                reward_text TEXT NOT NULL,
                discount_percent INTEGER DEFAULT 100,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. System Logs Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT DEFAULT 'INFO',
                module TEXT DEFAULT 'SolverEngine',
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # Seed Default Demo Accounts & Initial Data
    seed_demo_data()

def seed_demo_data():
    """
    Three User Types Default Demo Accounts:
    1. Super Admin: username 'admin', password 'admin123', role 'super_admin'
    2. Developer: username 'developer', password 'dev123', role 'developer'
    3. Registered User: username 'speedcuber', password 'user123', role 'user'
    """
    demo_accounts = [
        ('admin', 'admin@cubeverse.io', 'admin123', 'super_admin', 'Supreme Administrator & Competition Judge', '#f59e0b'),
        ('developer', 'dev@cubeverse.io', 'dev123', 'developer', 'Lead Full-Stack AI & Computer Vision Architect', '#06b6d4'),
        ('speedcuber', 'cuber@cubeverse.io', 'user123', 'user', 'WCA Speedcubing Contender & Group Theorist', '#818cf8')
    ]
    
    for uname, email, pw, role, bio, color in demo_accounts:
        user = query_one(
            "SELECT id FROM users WHERE username = %s",
            "SELECT id FROM users WHERE username = ?",
            (uname,)
        )
        if not user:
            pw_hash = generate_password_hash(pw)
            execute_insert(
                "INSERT INTO users (username, email, password_hash, role, bio, avatar_color) VALUES (%s, %s, %s, %s, %s, %s)",
                "INSERT INTO users (username, email, password_hash, role, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?)",
                (uname, email, pw_hash, role, bio, color)
            )

    # Seed Initial Competitions if none exist
    comp = query_one("SELECT id FROM competitions LIMIT 1", "SELECT id FROM competitions LIMIT 1")
    if not comp:
        execute_insert(
            "INSERT INTO competitions (title, description, scramble, prize_trophy, status) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO competitions (title, description, scramble, prize_trophy, status) VALUES (?, ?, ?, ?, ?)",
            (
                "Rubik's Grand Group Championship 2026",
                "Solve this standard WCA 18-move scramble in minimum moves using Two-Phase reductions.",
                "R U R' U' F' U2 F U R U' R' F' R U R' U' R' F R2 U'",
                "Platinum Polyhedron Trophy + 500 Credits",
                "active"
            )
        )
        execute_insert(
            "INSERT INTO competitions (title, description, scramble, prize_trophy, status) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO competitions (title, description, scramble, prize_trophy, status) VALUES (?, ?, ?, ?, ?)",
            (
                "Speedcubing FMC (Fewest Moves Challenge)",
                "Find the shortest generator sequence g in S54 reaching identity in under 18 moves.",
                "B' U2 R' D B2 R2 L D B' F' U' L' D' F2 R L2 B2 F' D R'",
                "Gold FMC Speed Medal",
                "active"
            )
        )

    # Seed Initial Courses
    course = query_one("SELECT id FROM courses LIMIT 1", "SELECT id FROM courses LIMIT 1")
    if not course:
        execute_insert(
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (?, ?, ?, ?, ?)",
            ("Mastering Permutation Group Theory", "Learn conjugacy classes, cycle notation, and parity in S54.", "Advanced", 6, "Super Admin")
        )
        execute_insert(
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (?, ?, ?, ?, ?)",
            ("Kociemba Two-Phase Algorithm Decoded", "Step-by-step subgroup reduction from G0 to G1 to G2.", "Intermediate", 4, "Developer")
        )
        execute_insert(
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO courses (title, description, difficulty, modules_count, author) VALUES (?, ?, ?, ?, ?)",
            ("OpenCV Computer Vision for Twisty Puzzles", "HSV segmentation, sticker edge detection, and centroid extraction.", "Practical", 5, "Developer")
        )

    # Seed Initial Coupons
    coupon = query_one("SELECT id FROM coupons LIMIT 1", "SELECT id FROM coupons LIMIT 1")
    if not coupon:
        execute_insert(
            "INSERT INTO coupons (code, reward_text, discount_percent, status) VALUES (%s, %s, %s, %s)",
            "INSERT INTO coupons (code, reward_text, discount_percent, status) VALUES (?, ?, ?, ?)",
            ("GROUPTHEORY2026", "100% Free Access to All Speedcubing Tournaments & Visualizer Pro", 100, "active")
        )
        execute_insert(
            "INSERT INTO coupons (code, reward_text, discount_percent, status) VALUES (%s, %s, %s, %s)",
            "INSERT INTO coupons (code, reward_text, discount_percent, status) VALUES (?, ?, ?, ?)",
            ("KOCIEMBA_VIP", "VIP God's Number Certificate & Badge", 100, "active")
        )

    # Seed Initial System Logs for Dev Dashboard
    log = query_one("SELECT id FROM system_logs LIMIT 1", "SELECT id FROM system_logs LIMIT 1")
    if not log:
        logs_to_add = [
            ('INFO', 'SystemInit', 'MVC Server initialized with PyMySQL and dual SQLite fallback.'),
            ('INFO', 'KociembaEngine', 'Two-Phase Algorithm G0 -> G1 -> G2 solver pre-warmed in 0.04ms.'),
            ('INFO', 'OpenCVPipeline', 'HSV Color Space classifier calibrated for 6 standard Rubik stickers.'),
            ('DEBUG', 'RBAC_Router', 'Multi-role authentication permission matrix verified.')
        ]
        for lvl, mod, msg in logs_to_add:
            execute_insert(
                "INSERT INTO system_logs (level, module, message) VALUES (%s, %s, %s)",
                "INSERT INTO system_logs (level, module, message) VALUES (?, ?, ?)",
                (lvl, mod, msg)
            )

def query_one(sql_mysql, sql_sqlite, params=()):
    """Single row fetch helper"""
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
    """Multiple rows fetch helper"""
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
    """Insert query helper returning inserted ID"""
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
    """Update / Delete query helper returning affected row count"""
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
