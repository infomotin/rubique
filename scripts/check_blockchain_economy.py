import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.user_model import UserModel
from models.card_club.economy import balances_view, verify_ledger, SUPPLY
from models.db import query_one, query_all

print("=== BLOCKCHAIN COIN ECONOMY & LEDGER STATUS (MYSQL) ===")
rep = verify_ledger()
print(f"Cryptographic Chain Integrity : {'VERIFIED (OK)' if rep['chain_ok'] else 'CORRUPT'}")
print(f"Double-Entry Balances Invariant: {'VERIFIED (OK)' if rep['balances_ok'] else 'MISMATCH'}")
print(f"Fixed Total Supply Invariant  : {'VERIFIED (1,000,000,000 COINS)' if rep['supply_ok'] else 'SUPPLY BREACH'}")
print(f"  - Developer Reserve: {rep['reserve']:,} coins")
print(f"  - Circulating Supply: {rep['circulating']:,} coins")
print(f"  - Group Prize Pools: {rep['pools']:,} coins")
print(f"  - Total Supply Sum  : {rep['reserve'] + rep['circulating'] + rep['pools']:,} / {SUPPLY:,} coins")

# Check ledger blocks count
block_count = query_one("SELECT COUNT(*) as cnt FROM club_ledger", "SELECT COUNT(*) as cnt FROM club_ledger")
chain_head = query_one("SELECT * FROM club_chain_head WHERE id = 1", "SELECT * FROM club_chain_head WHERE id = 1")
print(f"\nTotal Hash-Chained Blocks : {block_count['cnt']}")
print(f"Latest Chain Head Hash     : {chain_head['last_hash']}")
print(f"Latest Sequence Number     : #{chain_head['seq']}")

print("\n--- SUBSCRIBER COIN BALANCES ---")
for username in ['admin', 'developer', 'speedcuber']:
    u = UserModel.find_by_username(username)
    if u:
        b = balances_view(u['id'])
        print(f"[{u['role'].upper()}] {username:<12} (User #{u['id']}): {b['personal']:,} Personal Coins")

# Top 5 wealthiest subscribers
top_wallets = query_all(
    "SELECT w.group_id, w.user_id, w.balance, u.username, u.role FROM club_wallets w LEFT JOIN users u ON w.user_id = u.id WHERE w.user_id > 0 ORDER BY w.balance DESC LIMIT 5",
    "SELECT w.group_id, w.user_id, w.balance, u.username, u.role FROM club_wallets w LEFT JOIN users u ON w.user_id = u.id WHERE w.user_id > 0 ORDER BY w.balance DESC LIMIT 5"
)
print("\n--- TOP CIRCULATING WALLETS ---")
for tw in top_wallets:
    uname = tw.get('username') or f"User #{tw['user_id']}"
    print(f"Group #{tw['group_id']} | {uname:<15} (User #{tw['user_id']}): {tw['balance']:,} Coins")
