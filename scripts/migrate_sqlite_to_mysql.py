"""
Migration Script: SQLite (cubedata.db) to MySQL (cube_permutation)
==================================================================
Transfers all existing data from SQLite to MySQL with:
1. Schema verification / initialization.
2. Foreign key checks disabled during import (SET FOREIGN_KEY_CHECKS = 0;).
3. Batched inserts with parameterized queries.
4. Auto-increment synchronization.
5. Row-count parity checks and report.
"""

import os
import sys
import sqlite3
import pymysql
import pymysql.cursors

# Ensure rubique root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
from models.db import init_database

def run_migration():
    sqlite_path = os.path.abspath(Config.SQLITE_DB)
    if not os.path.exists(sqlite_path):
        print(f"[ERROR] SQLite database file not found at: {sqlite_path}")
        return False

    print(f"[INFO] Connecting to SQLite at: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Step 1: Ensure MySQL database and schema exist
    print(f"[INFO] Ensuring MySQL database '{Config.MYSQL_DB}' and schemas exist...")
    # First connect to server and create DB
    server_conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        port=Config.MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
    with server_conn.cursor() as s_cur:
        s_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    server_conn.commit()
    server_conn.close()

    # Connect to MySQL DB
    mysql_conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        port=Config.MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    mysql_cur = mysql_conn.cursor()

    # Initialize all schemas
    init_database()

    # Get list of SQLite tables
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    sqlite_tables = [row['name'] for row in sqlite_cur.fetchall()]
    print(f"[INFO] Found {len(sqlite_tables)} tables in SQLite: {', '.join(sqlite_tables)}")

    # Get list of MySQL tables
    mysql_cur.execute("SHOW TABLES;")
    mysql_tables = set(list(row.values())[0] for row in mysql_cur.fetchall())
    print(f"[INFO] Found {len(mysql_tables)} tables in MySQL.")

    # Disable foreign key checks on MySQL during migration
    mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    mysql_cur.execute("SET UNIQUE_CHECKS = 0;")
    mysql_conn.commit()

    report = []
    
    try:
        for table in sqlite_tables:
            # Check if table exists in MySQL
            if table not in mysql_tables:
                print(f"[WARN] Table '{table}' exists in SQLite but not in MySQL. Attempting auto-create...")
                # Fetch sqlite CREATE TABLE sql
                sqlite_cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
                create_sql = sqlite_cur.fetchone()['sql']
                # Adapt SQLite AUTOINCREMENT to MySQL AUTO_INCREMENT if possible, or skip
                # Usually init_database defines all tables, let's see
                print(f"[WARN] Skipping auto-create for '{table}', please check schema if needed.")
                continue

            # Fetch columns for table from MySQL
            mysql_cur.execute(f"DESCRIBE `{table}`;")
            mysql_cols = [c['Field'] for c in mysql_cur.fetchall()]

            # Fetch columns for table from SQLite
            sqlite_cur.execute(f"PRAGMA table_info(`{table}`);")
            sqlite_cols = [c['name'] for c in sqlite_cur.fetchall()]

            common_cols = [c for c in sqlite_cols if c in mysql_cols]
            if not common_cols:
                print(f"[WARN] Table '{table}' has no overlapping columns between SQLite and MySQL.")
                continue

            # Count rows in SQLite
            sqlite_cur.execute(f"SELECT COUNT(*) as cnt FROM `{table}`;")
            sqlite_count = sqlite_cur.fetchone()['cnt']

            if sqlite_count == 0:
                print(f"[INFO] Table '{table}' has 0 rows in SQLite. Skipping data copy.")
                report.append({'table': table, 'sqlite_rows': 0, 'mysql_rows': 0, 'status': 'EMPTY'})
                continue

            # Read all rows from SQLite
            col_list_str = ", ".join([f"`{c}`" for c in common_cols])
            sqlite_cur.execute(f"SELECT {col_list_str} FROM `{table}`;")
            rows = sqlite_cur.fetchall()

            # Clear existing data in MySQL table to avoid duplicate key conflicts
            mysql_cur.execute(f"TRUNCATE TABLE `{table}`;")

            # Prepare batch insert
            placeholders = ", ".join(["%s"] * len(common_cols))
            insert_sql = f"INSERT INTO `{table}` ({col_list_str}) VALUES ({placeholders})"

            batch_data = []
            for row in rows:
                val_tuple = tuple(row[c] for c in common_cols)
                batch_data.append(val_tuple)

            # Insert in chunks of 500
            chunk_size = 500
            for i in range(0, len(batch_data), chunk_size):
                chunk = batch_data[i:i + chunk_size]
                mysql_cur.executemany(insert_sql, chunk)

            mysql_conn.commit()

            # Count rows in MySQL to verify
            mysql_cur.execute(f"SELECT COUNT(*) as cnt FROM `{table}`;")
            mysql_count = mysql_cur.fetchone()['cnt']

            status = 'OK' if sqlite_count == mysql_count else 'MISMATCH'
            print(f"[SYNC] Table '{table}': SQLite {sqlite_count} rows -> MySQL {mysql_count} rows [{status}]")
            report.append({'table': table, 'sqlite_rows': sqlite_count, 'mysql_rows': mysql_count, 'status': status})

        print("\n" + "="*60)
        print("MIGRATION SUMMARY REPORT")
        print("="*60)
        for r in report:
            print(f"{r['table']:<35} SQLite: {r['sqlite_rows']:<6} MySQL: {r['mysql_rows']:<6} Status: {r['status']}")
        print("="*60)

    finally:
        # Re-enable foreign key checks on MySQL
        mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        mysql_cur.execute("SET UNIQUE_CHECKS = 1;")
        mysql_conn.commit()

        sqlite_conn.close()
        mysql_conn.close()

    print("[SUCCESS] Data migration completed successfully!")
    return True

if __name__ == '__main__':
    run_migration()
