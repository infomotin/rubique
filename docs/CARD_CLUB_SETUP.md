# Card Club — Setup & Operations Guide

Run, demo, and operate the **Card Club** subscriber section: 15+ card games, private 18+ groups, live WebSocket tables, and the fixed-supply coin ledger.

> Architecture, security model, and economy design are documented separately in [`CARD_PLATFORM_SETUP.md`](CARD_PLATFORM_SETUP.md). This file is the practical run-book.

---

## 1. Requirements & Install

- Python 3.14 (repo venv: `.venv/`), MySQL (SQLite auto-fallback for local runs)
- Node is **not** required; the Socket.IO browser client is vendored at `static/js/socket.io.min.js` (v4.7.5)

```bash
cd /Users/motin/Herd/rubique
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` includes `flask-socketio` / `python-socketio` — without them the server dies at `import flask_socketio` (see §8).

## 2. Run

```bash
.venv/bin/python app.py
# → http://127.0.0.1:5050  (debug reloader on, Socket.IO threading driver)
```

- Tables are created automatically by `init_database()` on first boot (`club_*` tables, #25–40 in `models/db.py`).
- Demo logins: `admin/admin123` (super_admin), `developer/dev123`, `speedcuber/user123`.
- Only one process may bind port 5050 — if `lsof -iTCP:5050` shows another instance (e.g. a second dev session), kill it first or pick another port; a stale reloader parent keeps serving old code.

## 3. Demo Walkthrough (two browsers / one normal + one incognito)

1. **Register** an adult account at `/register` with a valid date of birth (≥ 18). On success the wallet is granted **100 coins** from the fixed reserve (`GET /club/api/wallet` → `balances.personal = 100`).
   - Under-18 DOB → registration rejected, no user row created.
   - Existing account without DOB → redirected to `/club/age-gate` on first `/club` visit.
   - Second registration from the same device fingerprint (same browser) → blocked ("device already registered").
2. Open **`/club/`** (sidebar → *Card Club*). Create a group → you are its admin and the group pool is seeded (`GROUP_POOL_ALLOCATION = 5,000` coins held in the pool wallet `(g,0)`).
3. **Invite** the second account by username (admin-only), then accept from that account's `/club/` page.
4. **Fund** group balances for staking: `POST /club/api/wallet/fund {"group_id": …, "amount": 40}` moves coins from your personal wallet into your group balance `(g,u)` — bets are placed from the **group balance**, not personal.
5. **Create a table** (`blitz`, stake 10, pool bonus 5), **join** with the second account, **start**. Play in the browser (legal-move buttons render automatically; custom JSON actions for trick games).
6. When the engine finishes, the pot settles **zero-sum** (`payouts == pot + pool_bonus`); the settlement is pushed over WebSocket and shown in the table's settlement banner.
7. **Verify the ledger**: developer account → `GET /club/api/ledger/verify` (or the Verify button on `/club/ledger`). Expect `ok: true` with reserve + circulating + pools = 1,000,000,000.

## 4. Routes (blueprint `card_club_bp`, prefix `/club`)

| Page (session + age gate) | Method | Path |
|---|---|---|
| Section home | GET | `/club/` |
| Age gate | GET/POST | `/club/age-gate` |
| Group detail | GET | `/club/groups/<gid>` |
| Table (game board) | GET | `/club/tables/<tid>` |
| Ledger explorer | GET | `/club/ledger` |

| JSON API (`X-Card-Club: 1` accepted; JSON errors 401/403/404/400) | Method | Path |
|---|---|---|
| Create / list my groups | POST/GET | `/club/api/groups` |
| Invite / accept invite | POST | `/club/api/groups/<gid>/invites`, `/club/api/invites/<iid>/accept` |
| Propose role change / vote | POST | `/club/api/groups/<gid>/proposals`, `/club/api/proposals/<pid>/vote` |
| Remove member (sweeps balance) | POST | `/club/api/groups/<gid>/members/<uid>/remove` |
| Wallet: balances, fund, transfer, resolve, escrow, act | GET/POST | `/club/api/wallet…` |
| Table: create, join, leave, start, abandon, move, state | POST/GET | `/club/api/tables/<tid>…` |
| Ledger verify (**developer role only**) | GET | `/club/api/ledger/verify` |

Socket.IO events (rooms `user:{uid}`, `table:{tid}`): client `watch_table`, `unwatch_table`, `table_move`; server `table_state` (private per seat), `table_spectate`, `table_settlement`.

## 5. Economy Configuration (`models/card_club/economy.py`)

| Constant | Value | Meaning |
|---|---|---|
| `SUPPLY` | 1,000,000,000 | Immutable total; reserve + circulating + pools always equal it |
| `STARTING_GRANT` | 100 | One-time, idempotent grant to every adult account |
| `GROUP_POOL_ALLOCATION` | 5,000 | Seeded into pool wallet `(g,0)` at group creation |
| `MAX_BET_LIMIT` | 500 | Hard per-seat stake cap (API rejects above it) |
| `MAX_OUTSTANDING_EXPOSURE` | 2,000 | Running exposure guard per group |

Wallet coordinates: `(0,u)` personal · `(g,0)` group pool · `(g,u)` member group balance · `(0,0)` in-flight hold (escrow/transfers). Transfers are **recipient-approved**; the sender cannot self-resolve. Every mutation is a paired ledger entry; `verify_ledger()` re-checks the hash chain, per-wallet deltas, and the supply invariant.

## 6. WebSockets vs. Polling

- The server speaks Engine.IO v4 / Socket.IO v4 (`async_mode="threading"`, `cors_allowed_origins="*"`), authenticated by the normal Flask **session cookie** — no token handshake needed.
- `static/js/card_club.js` connects on table pages, watches the table, and re-renders on `table_state` / `table_spectate`; if the socket cannot connect (proxy, older browser) it **falls back to HTTP polling every 2.5s** of `GET /club/api/tables/<id>/state`, so tables stay playable without WS.
- HTTP and WS moves share one code path (`_do_move`), so rules, settlement, and ledger behavior are identical either way.

## 7. Testing

```bash
# Unit + integration suite (existing RBAC/Cube/Chess tests + 4 Card Club tests)
.venv/bin/python -m unittest test_app -v            # expect: Ran 11 tests … OK

# Card Club only (age gate & device binding, group privacy/invites/majority vote,
# wallet/escrow/bet limits/zero-sum settlement, engine smoke over the whole catalogue)
.venv/bin/python -m unittest test_app.CardClubTests -v
```

Scripts (per-run unique users; run from anywhere):

- `…/T/opencode/club_e2e.py` — 52-step HTTP end-to-end (age gates, invites, votes, transfers, escrow, blitz settlement, `verify_ledger ok`, member removal).
- `…/T/opencode/club_ws_test.py` — live Socket.IO check: two players + spectator receive `table_state` / `table_spectate` pushes after an HTTP move (6/6).

Direct invariant check:

```python
from models.card_club.economy import verify_ledger
print(verify_ledger())   # {'ok': True, 'reserve': …, 'circulating': …, 'pools': …, 'violations': []}
```

## 8. Known Limitations & Troubleshooting

- **Settle failure leaves bets escrowed**: if `settle_zero_sum` ever raises after a finished game, bets stay in the hold wallet `(0,0)`. Recovery: admin **Abandon** the table — `_refund_one`/`refund_bets_for_table` returns stakes (and any pool bonus) before flipping bet status. The ledger stays verifiable either way; repair with a refund rather than manual SQL.
- **Device binding is best-effort**: browser fingerprints (UA + screen + language + TZ) are spoofable and shared on NATs/corporate proxies — they stop casual multi-accounting, not an adversary. Production path: WebAuthn/FIDO2 attestation or native-client keys (see §2.2 of `CARD_PLATFORM_SETUP.md`). Weak keys (IP+UA) are deliberately *not* enforced at login to avoid NAT lockouts.
- **Age gate only checks self-declared DOB** — no document verification.
- **Stale server code**: the Flask debug reloader can crash-loop if a watched file is saved with a syntax error mid-edit (check `* Restarting with stat` / `SyntaxError` in the server console). Fix the file and the reloader recovers on the next save; verify with `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5050/`.
- **Port conflicts**: two dev sessions both starting `app.py` → the second fails to bind; the first may be running older code. `lsof -iTCP:5050` to check.
- **Test data grows the circulating supply**: unit tests and demos grant real coins (supply is conserved; the reserve shrinks, the invariant still holds). To re-derive a pristine reserve after deleting test wallets/ledger rows, set `club_reserve.balance = 1,000,000,000 − (circulating + pools)` from the current wallet totals, then confirm `verify_ledger()` returns `ok: true` — never patch the ledger entries themselves.
