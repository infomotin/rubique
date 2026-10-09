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
                    date_of_birth DATE NULL,
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

            # 16. Chess Games Table (GoChess Smart Board with 1v1, Clan vs Clan & Clan vs Public)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chess_games (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    white_user_id INT NULL,
                    black_user_id INT NULL,
                    white_group_id INT NULL,
                    black_group_id INT NULL,
                    title VARCHAR(150) DEFAULT 'GoChess Smart Session',
                    game_mode VARCHAR(30) DEFAULT 'ai',
                    match_type VARCHAR(30) DEFAULT 'ai',
                    ai_level INT DEFAULT 2,
                    board_theme VARCHAR(50) DEFAULT 'obsidian',
                    fen VARCHAR(200) DEFAULT 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                    pgn TEXT,
                    moves_count INT DEFAULT 0,
                    status VARCHAR(30) DEFAULT 'active',
                    winner VARCHAR(30) NULL,
                    is_public INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Defensive migration: multiplayer columns for pre-existing chess_games tables
            for _col_sql in (
                "white_user_id INT NULL",
                "black_user_id INT NULL",
                "white_group_id INT NULL",
                "black_group_id INT NULL",
                "match_type VARCHAR(30) DEFAULT 'ai'",
                "is_public INT DEFAULT 1",
            ):
                try:
                    cur.execute(f"ALTER TABLE chess_games ADD COLUMN {_col_sql}")
                except Exception:
                    pass

            # 17. Chess Clan Challenges Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chess_clan_challenges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    game_id INT NOT NULL,
                    group_id INT NOT NULL,
                    user_id INT NOT NULL,
                    challenge_note TEXT,
                    status VARCHAR(30) DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES chess_games(id) ON DELETE CASCADE,
                    FOREIGN KEY (group_id) REFERENCES chat_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 18. Chess Problems Table (Author by Super Admin, Solved by Subscribers)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chess_problems (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    author_id INT NOT NULL,
                    title VARCHAR(150) NOT NULL,
                    difficulty VARCHAR(50) DEFAULT 'Grandmaster',
                    fen VARCHAR(200) NOT NULL,
                    solution_moves TEXT NOT NULL,
                    hint TEXT,
                    xp_reward INT DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 19. Chess Problem Submissions Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chess_problem_submissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    problem_id INT NOT NULL,
                    user_id INT NOT NULL,
                    submitted_moves TEXT NOT NULL,
                    is_solved INT DEFAULT 0,
                    xp_earned INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (problem_id) REFERENCES chess_problems(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 20. Chess Multiplayer Team Moves (Clan vs Clan & Group vs Public Multi-Player)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chess_team_moves (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    game_id INT NOT NULL,
                    user_id INT NOT NULL,
                    team VARCHAR(20) DEFAULT 'white',
                    move_uci VARCHAR(10) NOT NULL,
                    move_san VARCHAR(15),
                    comment VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES chess_games(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 21. System Settings & Game Feature Toggles
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type VARCHAR(50) DEFAULT 'boolean',
                    description VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 22. Game Security & Anti-Cheat Events
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_security_events (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    game_type VARCHAR(50) NOT NULL,
                    game_id INT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) DEFAULT 'warning',
                    client_ip VARCHAR(50),
                    user_agent VARCHAR(255),
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 23. Card Games (Memory Deck & Puzzle Match)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS card_games (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    game_type VARCHAR(50) DEFAULT 'cyber_deck_match',
                    card_pairs INT DEFAULT 8,
                    moves_count INT DEFAULT 0,
                    time_seconds INT DEFAULT 0,
                    score INT DEFAULT 0,
                    status VARCHAR(30) DEFAULT 'active',
                    deck_state TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 24. Developer Bit-Level Telemetry Stream
            cur.execute("""
                CREATE TABLE IF NOT EXISTS developer_telemetry_stream (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trace_id VARCHAR(64) NOT NULL,
                    client_ip VARCHAR(50),
                    user_id INT NULL,
                    role VARCHAR(30) DEFAULT 'guest',
                    module VARCHAR(50) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    payload_bytes INT DEFAULT 0,
                    payload_bits INT DEFAULT 0,
                    payload_hex TEXT,
                    latency_ms FLOAT DEFAULT 0.0,
                    http_status INT DEFAULT 200,
                    severity VARCHAR(20) DEFAULT 'INFO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Age gate: self-declared DOB for Card Club (18+ check at sign-up)
            try:
                cur.execute("ALTER TABLE users ADD COLUMN date_of_birth DATE NULL")
            except Exception:
                pass

            # 25. Card Club - Private closed groups (invisible to outsiders)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_groups (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    description VARCHAR(255) DEFAULT '',
                    invite_code VARCHAR(20) NOT NULL UNIQUE,
                    default_role VARCHAR(20) DEFAULT 'member',
                    created_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            try:
                cur.execute("ALTER TABLE club_groups ADD COLUMN default_role VARCHAR(20) DEFAULT 'member'")
            except Exception:
                pass
            # 26. Card Club - Group membership & roles
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_group_members (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    user_id INT NOT NULL,
                    role VARCHAR(20) DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_club_member (group_id, user_id),
                    FOREIGN KEY (group_id) REFERENCES club_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 27. Card Club - Admin-only invitations (no self-discovery)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_invites (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    invitee_user_id INT NULL,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP NULL,
                    FOREIGN KEY (group_id) REFERENCES club_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (invitee_user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 28. Card Club - Role change / default role proposals (majority approval)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_role_proposals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    proposer_id INT NOT NULL,
                    target_user_id INT NULL,
                    proposal_type VARCHAR(40) NOT NULL,
                    payload TEXT,
                    status VARCHAR(20) DEFAULT 'open',
                    votes_for INT DEFAULT 0,
                    votes_against INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP NULL,
                    FOREIGN KEY (group_id) REFERENCES club_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (proposer_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 29. Card Club - Proposal votes (one vote per member)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_role_votes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    proposal_id INT NOT NULL,
                    user_id INT NOT NULL,
                    vote VARCHAR(10) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_club_vote (proposal_id, user_id),
                    FOREIGN KEY (proposal_id) REFERENCES club_role_proposals(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 30. Card Club - Group-isolated wallets (user_id=0 is the group pool)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_wallets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    user_id INT DEFAULT 0,
                    balance BIGINT NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_club_wallet (group_id, user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 31. Card Club - Wallet ledger (every coin movement audited)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_ledger (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    user_id INT NOT NULL,
                    amount BIGINT NOT NULL,
                    balance_after BIGINT NOT NULL,
                    entry_type VARCHAR(30) NOT NULL,
                    ref_type VARCHAR(30),
                    ref_id INT,
                    note VARCHAR(255) DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 32. Card Club - Transfers requiring recipient approval
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    from_user_id INT NOT NULL,
                    to_user_id INT NOT NULL,
                    amount BIGINT NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP NULL,
                    FOREIGN KEY (group_id) REFERENCES club_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 33. Card Club - Game tables (state JSON, seat order, stake & pool bonus)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_tables (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    game_slug VARCHAR(40) NOT NULL,
                    name VARCHAR(120) DEFAULT '',
                    stake BIGINT DEFAULT 0,
                    pool_bonus BIGINT DEFAULT 0,
                    max_seats INT NOT NULL,
                    status VARCHAR(20) DEFAULT 'waiting',
                    state TEXT,
                    created_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP NULL,
                    finished_at TIMESTAMP NULL,
                    FOREIGN KEY (group_id) REFERENCES club_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 34. Card Club - Seats at a table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_seats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    table_id INT NOT NULL,
                    user_id INT NOT NULL,
                    seat_index INT NOT NULL,
                    status VARCHAR(20) DEFAULT 'seated',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_club_seat (table_id, user_id),
                    FOREIGN KEY (table_id) REFERENCES club_tables(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 35. Card Club - Escrowed bets (zero-sum settlement)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_bets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    table_id INT NOT NULL,
                    user_id INT NOT NULL,
                    amount BIGINT NOT NULL,
                    status VARCHAR(20) DEFAULT 'escrowed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (table_id) REFERENCES club_tables(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 36. Card Club - Move log (audit trail)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_moves (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    table_id INT NOT NULL,
                    seq INT NOT NULL,
                    user_id INT NULL,
                    move_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (table_id) REFERENCES club_tables(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 37. Card Club - Hash-chained ledger head (optimistic lock row)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_chain_head (
                    id INT PRIMARY KEY,
                    seq INT NOT NULL DEFAULT 0,
                    last_hash CHAR(64) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 38. Card Club - Developer reserve (fixed supply, never mints mid-play)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_reserve (
                    id INT PRIMARY KEY,
                    balance BIGINT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 39. Card Club - Player-to-player coin sale escrow
            cur.execute("""
                CREATE TABLE IF NOT EXISTS club_escrow (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    payer_id INT NOT NULL,
                    payee_id INT NOT NULL,
                    amount BIGINT NOT NULL,
                    description VARCHAR(255) DEFAULT '',
                    status VARCHAR(20) DEFAULT 'offered',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP NULL,
                    FOREIGN KEY (payer_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (payee_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # 40. Card Club - Device binding (one registration per machine)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS device_registrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_key CHAR(64) NOT NULL UNIQUE,
                    user_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            for _ledger_sql in (
                "ALTER TABLE club_ledger ADD COLUMN seq INT NOT NULL DEFAULT 0",
                "ALTER TABLE club_ledger ADD COLUMN owner_key VARCHAR(80) NOT NULL DEFAULT ''",
                "ALTER TABLE club_ledger ADD COLUMN prev_hash CHAR(64) NOT NULL DEFAULT ''",
                "ALTER TABLE club_ledger ADD COLUMN entry_hash CHAR(64) NOT NULL DEFAULT ''",
            ):
                try:
                    cur.execute(_ledger_sql)
                except Exception:
                    pass
            # club_wallets.group_id = 0 is the global namespace: drop its FK
            try:
                cur.execute("""SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                               WHERE TABLE_SCHEMA = DATABASE()
                                 AND TABLE_NAME = 'club_wallets'
                                 AND REFERENCED_TABLE_NAME = 'club_groups'""")
                for _fkr in cur.fetchall():
                    _fkname = _fkr.get("CONSTRAINT_NAME") if isinstance(_fkr, dict) else _fkr[0]
                    if _fkname:
                        try:
                            cur.execute(f"ALTER TABLE club_wallets DROP FOREIGN KEY {_fkname}")
                        except Exception:
                            pass
            except Exception:
                pass
            # club_transfers.group_id = 0 is the global namespace: drop its FK
            try:
                cur.execute("""SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                               WHERE TABLE_SCHEMA = DATABASE()
                                 AND TABLE_NAME = 'club_transfers'
                                 AND REFERENCED_TABLE_NAME = 'club_groups'""")
                for _fkr in cur.fetchall():
                    _fkname = _fkr.get("CONSTRAINT_NAME") if isinstance(_fkr, dict) else _fkr[0]
                    if _fkname:
                        try:
                            cur.execute(f"ALTER TABLE club_transfers DROP FOREIGN KEY {_fkname}")
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                cur.execute("INSERT INTO club_chain_head (id, seq, last_hash) VALUES (1, 0, %s)",
                            ("0" * 64,))
            except Exception:
                pass
            try:
                cur.execute("INSERT INTO club_reserve (id, balance) VALUES (1, %s)",
                            (1000000000,))
            except Exception:
                pass
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
                date_of_birth TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Auto-migrate role column if not present
        cur.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in cur.fetchall()]
        if 'role' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        if 'date_of_birth' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN date_of_birth TEXT")
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

        # 16. Chess Games Table (GoChess Smart Board with 1v1, Clan vs Clan & Clan vs Public)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chess_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                white_user_id INTEGER,
                black_user_id INTEGER,
                white_group_id INTEGER,
                black_group_id INTEGER,
                title TEXT DEFAULT 'GoChess Smart Session',
                game_mode TEXT DEFAULT 'ai',
                match_type TEXT DEFAULT 'ai',
                ai_level INTEGER DEFAULT 2,
                board_theme TEXT DEFAULT 'obsidian',
                fen TEXT DEFAULT 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                pgn TEXT,
                moves_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                winner TEXT,
                is_public INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Defensive migration: multiplayer columns for pre-existing chess_games tables
        cur.execute("PRAGMA table_info(chess_games)")
        _cg_cols = {row[1] for row in cur.fetchall()}
        for _col_name, _col_sql in (
            ("white_user_id", "INTEGER"),
            ("black_user_id", "INTEGER"),
            ("white_group_id", "INTEGER"),
            ("black_group_id", "INTEGER"),
            ("match_type", "TEXT DEFAULT 'ai'"),
            ("is_public", "INTEGER DEFAULT 1"),
        ):
            if _col_name not in _cg_cols:
                try:
                    cur.execute(f"ALTER TABLE chess_games ADD COLUMN {_col_name} {_col_sql}")
                except Exception:
                    pass

        # 17. Chess Clan Challenges Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chess_clan_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                challenge_note TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES chess_games(id),
                FOREIGN KEY (group_id) REFERENCES chat_groups(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 18. Chess Problems Table (Author by Super Admin, Solved by Subscribers)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chess_problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                difficulty TEXT DEFAULT 'Grandmaster',
                fen TEXT NOT NULL,
                solution_moves TEXT NOT NULL,
                hint TEXT,
                xp_reward INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users(id)
            )
        """)

        # 19. Chess Problem Submissions Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chess_problem_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                submitted_moves TEXT NOT NULL,
                is_solved INTEGER DEFAULT 0,
                xp_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES chess_problems(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 20. Chess Multiplayer Team Moves (Clan vs Clan & Group vs Public Multi-Player)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chess_team_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                team TEXT DEFAULT 'white',
                move_uci TEXT NOT NULL,
                move_san TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES chess_games(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 21. System Settings & Game Feature Toggles
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type TEXT DEFAULT 'boolean',
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 22. Game Security & Anti-Cheat Events
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_type TEXT NOT NULL,
                game_id INTEGER,
                event_type TEXT NOT NULL,
                severity TEXT DEFAULT 'warning',
                client_ip TEXT,
                user_agent TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 23. Card Games (Memory Deck & Puzzle Match)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS card_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_type TEXT DEFAULT 'cyber_deck_match',
                card_pairs INTEGER DEFAULT 8,
                moves_count INTEGER DEFAULT 0,
                time_seconds INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                deck_state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 24. Developer Bit-Level Telemetry Stream
        cur.execute("""
            CREATE TABLE IF NOT EXISTS developer_telemetry_stream (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                client_ip TEXT,
                user_id INTEGER,
                role TEXT DEFAULT 'guest',
                module TEXT NOT NULL,
                action TEXT NOT NULL,
                payload_bytes INTEGER DEFAULT 0,
                payload_bits INTEGER DEFAULT 0,
                payload_hex TEXT,
                latency_ms REAL DEFAULT 0.0,
                http_status INTEGER DEFAULT 200,
                severity TEXT DEFAULT 'INFO',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 25. Card Club - Private closed groups (invisible to outsiders)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                invite_code TEXT NOT NULL UNIQUE,
                default_role TEXT DEFAULT 'member',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        cur.execute("PRAGMA table_info(club_groups)")
        _gg_cols = {row[1] for row in cur.fetchall()}
        if "default_role" not in _gg_cols:
            try:
                cur.execute("ALTER TABLE club_groups ADD COLUMN default_role TEXT DEFAULT 'member'")
            except Exception:
                pass
        # 26. Card Club - Group membership & roles
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES club_groups(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # 27. Card Club - Admin-only invitations (no self-discovery)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                invitee_user_id INTEGER,
                token TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'pending',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES club_groups(id),
                FOREIGN KEY (invitee_user_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        # 28. Card Club - Role change / default role proposals (majority approval)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_role_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                proposer_id INTEGER NOT NULL,
                target_user_id INTEGER,
                proposal_type TEXT NOT NULL,
                payload TEXT,
                status TEXT DEFAULT 'open',
                votes_for INTEGER DEFAULT 0,
                votes_against INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES club_groups(id),
                FOREIGN KEY (proposer_id) REFERENCES users(id)
            )
        """)
        # 29. Card Club - Proposal votes (one vote per member)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_role_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (proposal_id, user_id),
                FOREIGN KEY (proposal_id) REFERENCES club_role_proposals(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # 30. Card Club - Group-isolated wallets (user_id=0 is the group pool)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER DEFAULT 0,
                balance INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (group_id, user_id)
            )
        """)
        # 31. Card Club - Wallet ledger (every coin movement audited)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                entry_type TEXT NOT NULL,
                ref_type TEXT,
                ref_id INTEGER,
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 32. Card Club - Transfers requiring recipient approval
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES club_groups(id),
                FOREIGN KEY (from_user_id) REFERENCES users(id),
                FOREIGN KEY (to_user_id) REFERENCES users(id)
            )
        """)
        # 33. Card Club - Game tables (state JSON, seat order, stake & pool bonus)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                game_slug TEXT NOT NULL,
                name TEXT DEFAULT '',
                stake INTEGER DEFAULT 0,
                pool_bonus INTEGER DEFAULT 0,
                max_seats INTEGER NOT NULL,
                status TEXT DEFAULT 'waiting',
                state TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES club_groups(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        # 34. Card Club - Seats at a table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                seat_index INTEGER NOT NULL,
                status TEXT DEFAULT 'seated',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (table_id, user_id),
                FOREIGN KEY (table_id) REFERENCES club_tables(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # 35. Card Club - Escrowed bets (zero-sum settlement)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'escrowed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES club_tables(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # 36. Card Club - Move log (audit trail)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                seq INTEGER NOT NULL,
                user_id INTEGER,
                move_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES club_tables(id)
            )
        """)

        # 37. Card Club - Hash-chained ledger head
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_chain_head (
                id INTEGER PRIMARY KEY,
                seq INTEGER NOT NULL DEFAULT 0,
                last_hash TEXT NOT NULL
            )
        """)
        # 38. Card Club - Developer reserve (fixed supply)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_reserve (
                id INTEGER PRIMARY KEY,
                balance INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 39. Card Club - Player-to-player coin sale escrow
        cur.execute("""
            CREATE TABLE IF NOT EXISTS club_escrow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payer_id INTEGER NOT NULL,
                payee_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'offered',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (payer_id) REFERENCES users(id),
                FOREIGN KEY (payee_id) REFERENCES users(id)
            )
        """)
        # 40. Card Club - Device binding (one registration per machine)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS device_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_key TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cur.execute("PRAGMA table_info(club_ledger)")
        _led_cols = {row[1] for row in cur.fetchall()}
        for _col_name, _col_sql in (
            ("seq", "INTEGER NOT NULL DEFAULT 0"),
            ("owner_key", "TEXT NOT NULL DEFAULT ''"),
            ("prev_hash", "TEXT NOT NULL DEFAULT ''"),
            ("entry_hash", "TEXT NOT NULL DEFAULT ''"),
        ):
            if _col_name not in _led_cols:
                try:
                    cur.execute(f"ALTER TABLE club_ledger ADD COLUMN {_col_name} {_col_sql}")
                except Exception:
                    pass
        cur.execute("SELECT id FROM club_chain_head WHERE id = 1")
        if not cur.fetchone():
            cur.execute("INSERT INTO club_chain_head (id, seq, last_hash) VALUES (1, 0, ?)",
                        ("0" * 64,))
        cur.execute("SELECT id FROM club_reserve WHERE id = 1")
        if not cur.fetchone():
            cur.execute("INSERT INTO club_reserve (id, balance) VALUES (1, ?)", (1000000000,))

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

    # 0. Seed Default System Settings & Game Feature Toggles
    default_settings = [
        ('chess_game_enabled', '1', 'boolean', 'Enable or disable GoChess 3D Smart Board for players'),
        ('card_game_enabled', '1', 'boolean', 'Enable or disable CyberDeck Card Game for players'),
        ('speedcube_game_enabled', '1', 'boolean', 'Enable or disable 3D Rubik Speedcube for players'),
        ('game_anti_cheat_enabled', '1', 'boolean', 'Anti-Cheat engine: detects rapid-move bots & anomalies'),
        ('security_audit_logging', '1', 'boolean', 'Bit-level security and technical telemetry logging'),
        ('bit_telemetry_enabled', '1', 'boolean', 'Developer panel real-time bit stream monitoring')
    ]
    for skey, sval, stype, sdesc in default_settings:
        stg = query_one(
            "SELECT id FROM system_settings WHERE setting_key = %s",
            "SELECT id FROM system_settings WHERE setting_key = ?",
            (skey,)
        )
        if not stg:
            execute_insert(
                "INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES (%s, %s, %s, %s)",
                "INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES (?, ?, ?, ?)",
                (skey, sval, stype, sdesc)
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

    # 18. Seed Very Hard Grandmaster Chess Problems (Posted by Super Admin)
    prob = query_one("SELECT id FROM chess_problems LIMIT 1", "SELECT id FROM chess_problems LIMIT 1")
    if not prob:
        admin_user = query_one("SELECT id FROM users WHERE role = 'super_admin'", "SELECT id FROM users WHERE role = 'super_admin'")
        admin_id = admin_user['id'] if admin_user else 1

        execute_insert(
            """INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                admin_id,
                "The Greek Gift Sacrifice (Bxh7+ Breakthrough)",
                "Grandmaster (2400 ELO)",
                "r1bq1rk1/ppp2ppp/2n5/3pP3/1b1P4/2NB1N2/PP3PPP/R1BQK2R w KQ - 0 10",
                "d3h7,g8h7,f3g5,h7g8,d1h5",
                "Sacrifice the bishop on h7 with check to rip open the opponent's king safety, then follow up with Ng5 and Qh5.",
                250
            )
        )

        execute_insert(
            """INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                admin_id,
                "Morphy's Parisian Queen Deflection",
                "Very Hard (2200 ELO)",
                "rn3rk1/pbpp1ppp/1p6/8/2B1q3/5N2/PPP2PPP/R2QR1K1 w - - 0 13",
                "c4f7,f8f7,e1e4,b7e4",
                "Deflect the defending Black rook from the back rank by sacrificing on f7, completely exposing the unprotected black Queen on e4.",
                200
            )
        )

        execute_insert(
            """INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                admin_id,
                "Kasparov's Immortal Queen Deflection to Mate",
                "Extreme Tactical (2600 ELO)",
                "r1b2rk1/pp3ppp/2n1p3/2qp4/8/2B1PN2/PPP2PPP/R2QKB1R w KQ - 0 1",
                "c3g7,g8g7,d1d4",
                "Sacrifice the dark-squared bishop to destroy the pawn shield and setup a devastating double-attack fork.",
                350
            )
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
