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
                    wca_id VARCHAR(50) DEFAULT '',
                    country VARCHAR(100) DEFAULT '',
                    main_cube VARCHAR(100) DEFAULT 'GAN 12 MagLev 3x3',
                    preferred_method VARCHAR(50) DEFAULT 'CFOP',
                    pb_single VARCHAR(30) DEFAULT '',
                    pb_ao5 VARCHAR(30) DEFAULT '',
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
            # 8. Videos Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    video_url TEXT NOT NULL,
                    solve_time FLOAT DEFAULT 0.0,
                    method VARCHAR(50) DEFAULT 'CFOP',
                    description TEXT,
                    likes INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 9. Chat Groups Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_groups (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    description TEXT,
                    is_private INT DEFAULT 0,
                    passcode VARCHAR(50) NULL,
                    created_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 10. Chat Messages Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT NOT NULL,
                    receiver_id INT NULL,
                    group_id INT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 11. Friends Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS friends (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    friend_id INT NOT NULL,
                    status VARCHAR(30) DEFAULT 'accepted',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 12. Blog Posts Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    tags VARCHAR(120) DEFAULT 'CFOP,Tutorial',
                    likes INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 13. Blog Comments Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS blog_comments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    post_id INT NOT NULL,
                    user_id INT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 14. Custom Cubes Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS custom_cubes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(150) NOT NULL,
                    shape_type VARCHAR(50) DEFAULT 'classic_3x3',
                    description TEXT,
                    color_scheme TEXT,
                    cube_state TEXT,
                    scramble TEXT,
                    status VARCHAR(30) DEFAULT 'unsolved',
                    is_public INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 15. Cube Group Challenges Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cube_group_challenges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cube_id INT NOT NULL,
                    group_id INT NOT NULL,
                    user_id INT NOT NULL,
                    challenge_note TEXT,
                    status VARCHAR(30) DEFAULT 'open',
                    solution TEXT,
                    solver_id INT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cube_id) REFERENCES custom_cubes(id) ON DELETE CASCADE,
                    FOREIGN KEY (group_id) REFERENCES chat_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
        if 'wca_id' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN wca_id TEXT DEFAULT ''")
        if 'country' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN country TEXT DEFAULT ''")
        if 'main_cube' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN main_cube TEXT DEFAULT 'GAN 12 MagLev 3x3'")
        if 'preferred_method' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN preferred_method TEXT DEFAULT 'CFOP'")
        if 'pb_single' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN pb_single TEXT DEFAULT ''")
        if 'pb_ao5' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN pb_ao5 TEXT DEFAULT ''")

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

        # 8. Videos Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                video_url TEXT NOT NULL,
                solve_time REAL DEFAULT 0.0,
                method TEXT DEFAULT 'CFOP',
                description TEXT,
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 9. Chat Groups Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                is_private INTEGER DEFAULT 0,
                passcode TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 10. Chat Messages Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER,
                group_id INTEGER,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id)
            )
        """)

        # 11. Friends Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                status TEXT DEFAULT 'accepted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 12. Blog Posts Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT 'CFOP,Tutorial',
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 13. Blog Comments Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES blog_posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 14. Custom Cubes Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS custom_cubes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                shape_type TEXT DEFAULT 'classic_3x3',
                description TEXT,
                color_scheme TEXT,
                cube_state TEXT,
                scramble TEXT,
                status TEXT DEFAULT 'unsolved',
                is_public INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 15. Cube Group Challenges Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cube_group_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cube_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                challenge_note TEXT,
                status TEXT DEFAULT 'open',
                solution TEXT,
                solver_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cube_id) REFERENCES custom_cubes(id),
                FOREIGN KEY (group_id) REFERENCES chat_groups(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
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

    # Seed Initial Videos
    v = query_one("SELECT id FROM videos LIMIT 1", "SELECT id FROM videos LIMIT 1")
    if not v:
        user_cuber = query_one("SELECT id FROM users WHERE username = 'speedcuber'", "SELECT id FROM users WHERE username = 'speedcuber'")
        uid = user_cuber['id'] if user_cuber else 1
        execute_insert(
            "INSERT INTO videos (user_id, title, video_url, solve_time, method, description, likes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            "INSERT INTO videos (user_id, title, video_url, solve_time, method, description, likes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, "9.42s Single CFOP Solve Breakdown", "https://www.w3schools.com/html/mov_bbb.mp4", 9.42, "CFOP", "Full solve walkthrough with easy F2L pair inserts and Sune OLL finish!", 14)
        )
        execute_insert(
            "INSERT INTO videos (user_id, title, video_url, solve_time, method, description, likes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            "INSERT INTO videos (user_id, title, video_url, solve_time, method, description, likes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, "Two-Phase Kociemba 14-Move FMC Solution", "https://www.w3schools.com/html/movie.mp4", 6.85, "Kociemba Two-Phase", "Demonstrating God's number sub-20 reduction live in 3D.", 28)
        )

    # Seed Initial Groups & Messages
    grp = query_one("SELECT id FROM chat_groups LIMIT 1", "SELECT id FROM chat_groups LIMIT 1")
    if not grp:
        user_cuber = query_one("SELECT id FROM users WHERE username = 'speedcuber'", "SELECT id FROM users WHERE username = 'speedcuber'")
        uid = user_cuber['id'] if user_cuber else 1
        gid1 = execute_insert(
            "INSERT INTO chat_groups (name, description, is_private, created_by) VALUES (%s, %s, %s, %s)",
            "INSERT INTO chat_groups (name, description, is_private, created_by) VALUES (?, ?, ?, ?)",
            ("Global Speedcubers Clan", "Public hangout for cube lovers, speedcubers, and algorithm explorers worldwide!", 0, uid)
        )
        gid2 = execute_insert(
            "INSERT INTO chat_groups (name, description, is_private, passcode, created_by) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO chat_groups (name, description, is_private, passcode, created_by) VALUES (?, ?, ?, ?, ?)",
            ("Sub-10 Master Study Group", "Private master group for advanced lookahead and commutators.", 1, "CUBE10", uid)
        )
        execute_insert(
            "INSERT INTO chat_messages (sender_id, group_id, message) VALUES (%s, %s, %s)",
            "INSERT INTO chat_messages (sender_id, group_id, message) VALUES (?, ?, ?)",
            (uid, gid1, "Welcome to the Speedcuber Clan! Drop your personal best times here! 🎲")
        )

    # Seed Initial Blog Posts
    b = query_one("SELECT id FROM blog_posts LIMIT 1", "SELECT id FROM blog_posts LIMIT 1")
    if not b:
        user_cuber = query_one("SELECT id FROM users WHERE username = 'speedcuber'", "SELECT id FROM users WHERE username = 'speedcuber'")
        uid = user_cuber['id'] if user_cuber else 1
        pid1 = execute_insert(
            "INSERT INTO blog_posts (user_id, title, content, tags, likes) VALUES (%s, %s, %s, %s, %s)",
            "INSERT INTO blog_posts (user_id, title, content, tags, likes) VALUES (?, ?, ?, ?, ?)",
            (uid, "How I Dropped My Average from 30s to Sub-15 with 2-Look OLL", "The key to fast cubing as a kid is mastering standard finger tricks! Instead of regripping, use index flicks for U moves and thumb pulls for R'. Learn Sune and T-perm first.", "CFOP,Tips,Kids", 19)
        )
        execute_insert(
            "INSERT INTO blog_comments (post_id, user_id, comment) VALUES (%s, %s, %s)",
            "INSERT INTO blog_comments (post_id, user_id, comment) VALUES (?, ?, ?)",
            (pid1, uid, "Awesome tutorial! Sune is definitely my favorite algorithm.")
        )

    # Seed Initial Custom Cubes & Clan Challenge
    cc = query_one("SELECT id FROM custom_cubes LIMIT 1", "SELECT id FROM custom_cubes LIMIT 1")
    if not cc:
        user_cuber = query_one("SELECT id FROM users WHERE username = 'speedcuber'", "SELECT id FROM users WHERE username = 'speedcuber'")
        uid = user_cuber['id'] if user_cuber else 1
        cube1_id = execute_insert(
            """INSERT INTO custom_cubes (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO custom_cubes (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid, "Cyber Neon GoCube 3x3", "gocube_3x3", "High-frequency cyber illuminated Bluetooth smart cube with custom neon color scheme.", "#38bdf8,#e0e7ff,#10b981,#6366f1,#f59e0b,#f43f5e", "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB", "R U R' U' R' F R2 U' R' U' R U R' F'", "unsolved", 1)
        )
        cube2_id = execute_insert(
            """INSERT INTO custom_cubes (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO custom_cubes (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid, "Titanium Mirror Bump Cube", "mirror_cube", "Monochrome metallic brushed silver blocks with shape-shifting geometry.", "#e2e8f0,#cbd5e1,#94a3b8,#64748b,#475569,#334155", "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB", "F R U' R' U F'", "solved", 1)
        )
        cube3_id = execute_insert(
            """INSERT INTO custom_cubes (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO custom_cubes (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid, "Grand Dodecahedron Megaminx", "megaminx", "12-faced cosmic pentagonal star puzzle challenge with 12 distinct vivid colors.", "#ffffff,#facc15,#22c55e,#3b82f6,#ef4444,#a855f7,#f97316,#06b6d4,#ec4899,#84cc16,#64748b,#b45309", "", "R++ D-- R-- D++ U'", "unsolved", 1)
        )
        # Seed a Clan Challenge mentioning the speedcubers clan
        grp = query_one("SELECT id FROM chat_groups LIMIT 1", "SELECT id FROM chat_groups LIMIT 1")
        if grp and cube1_id:
            execute_insert(
                """INSERT INTO cube_group_challenges (cube_id, group_id, user_id, challenge_note, status)
                   VALUES (%s, %s, %s, %s, 'open')""",
                """INSERT INTO cube_group_challenges (cube_id, group_id, user_id, challenge_note, status)
                   VALUES (?, ?, ?, ?, 'open')""",
                (cube1_id, grp['id'], uid, "Clan Challenge: Can anyone find a solution algorithm under 22 moves for this Cyber Neon cube?")
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
