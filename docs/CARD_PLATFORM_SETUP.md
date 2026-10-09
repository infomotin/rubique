# Production Card Platform & Economy Architecture Documentation

## 1. Overview
The Rubique Card Platform is an enterprise-grade, high-security gaming suite featuring:
- **12 Popular Global & Bangladeshi Card Games** with exact player counts and standard tournament rules.
- **Classic Playing Card AI Arena** (29, Contract Bridge, Spades, Hearts, Whist, Oh Hell!, Euchre).
- **18+ Private Groups & Rooms** with admin-only invitations, dynamic role voting, and automated member balance sweep.
- **Fixed-Supply (1,000,000,000 Coins) Cryptographic Ledger** with append-only hash chains, escrow, and zero-sum betting.
- **WebSockets Real-Time Integration** (Speed real-time simultaneous shedding; turn-based updates for trick & strategy games).

---

## 2. Security & Identity

### 2.1 18+ Age Gate
- **Enforcement Points:**
  - Self-declared date-of-birth (`date_of_birth` column in `users` table) validated at registration.
  - Accounts with age $< 18$ years are rejected at signup.
  - Legacy accounts without a recorded DOB hit `/club/age-gate` before accessing any Card Club room, wallet, or table.
- **Implementation:** `models/card_club/groups.py:age_on()` and `controllers/card_club_controller.py:require_adult()`.

### 2.2 Device Binding (Multi-Account Prevention)
- **Mechanism:** One registration per machine hardware key.
- **Key Composition:**
  - `strong`: `X-Device-Mac` header or client hardware fingerprint (User Agent, screen depth/resolution, platform, language). Enforced at registration and login.
  - `weak`: SHA-256 hash of IP + User-Agent (used as registration fallback to prevent NAT lockout).
- **Limitations & Production Upgrade Path:**
  - Browser sandboxes do not expose raw network adapter MAC addresses due to OS security boundaries. The system supports client-provided MAC (`device_mac`) via Electron/native wrappers or hardware attestation headers (`X-Device-Mac`).
  - For enterprise or hardware-level security, replace `compose_device_key()` with WebAuthn FIDO2 attestation or MDM client certificates.

---

## 3. Private Groups & Access Control

### 3.1 Strict Isolation
- Groups are private entities. Non-members cannot search, discover, or access group homepages, table sessions, chat, or wallets.
- All database queries filter strictly by `group_id` and verified user membership.

### 3.2 Admin Invitations
- Admission to groups is strictly by admin invitation.
- Invites are recorded in `club_invites` and must be explicitly accepted by the invitee before membership is granted.

### 3.3 Dynamic Role Set & Majority Voting
- Admins propose role modifications for members.
- Proposeable roles must be drawn from the active game's designated role set (e.g., `dealer`, `bid-master`, `trump-bidder`, `declarer`, `floor-manager`, `pit-boss`).
- Proposals are stored in `club_role_proposals`.
- Enactment requires a simple majority vote ($> 50\%$) from all active group members (`club_role_votes`).

### 3.4 Member Removal Protocol
When an admin removes a member from a group:
1. Active table seats held by the member are automatically vacated.
2. The member's remaining group wallet balance is swept into the group wallet pool (`club_wallets`).
3. Group membership is revoked.

---

## 4. Card Game Catalogue

| Game | Slug | Players | Mode | Key Rules & Scoring |
|---|---|---|---|---|
| **Call Break** | `call_break` | 4 | Turn-based | 52 cards (13 each). Spades permanent trump. Bids 1-13. Must follow suit and beat highest card if possible. |
| **Hazari** | `hazari` | 4 | Turn-based | 1000-point partition game. 13 cards partitioned into 3-3-3-4 groups. Combos: Troy > Color Run > Run > Color > Pair > High Card. |
| **Twenty-Nine (29)** | `29` | 4 (Teams) | Turn-based | 32 cards (J=3, 9=2, A=1, 10=1). Bidding 16-28. Hidden trump revealed on void. Pairs (+4/-4). |
| **Teen Patti** | `teen_patti` | 3–6 | Turn-based | 3-card Indian Brag. Hand rank: Trail/Troy > Pure Sequence > Sequence > Color > Pair > High Card. |
| **Rummy** | `rummy` | 2–6 | Turn-based | 7 cards dealt. Draw stock/discard, meld sets (3-4 rank) and runs (3+ suited sequence). Discard to end turn. |
| **Contract Bridge** | `bridge` | 4 (Teams) | Turn-based | Partnership contract bidding. Declarer & Dummy open layout. Duplicate scoring. |
| **Texas Hold'em** | `poker` | 2–9 | Turn-based | Hole cards + Flop, Turn, River community cards. Pot betting rounds & showdown ranking. |
| **Blackjack (21)** | `blackjack` | 2–7 | Turn-based | Players vs Dealer. Hit, Stand, Double Down. Dealer hits to 16 and stands on soft 17. |
| **President / Scum** | `president` | 3–16 | Turn-based | Climbing game. Lead singles/pairs/trips. Beat rank or pass. First out becomes President. |
| **Cheat / Bluff** | `cheat` | 3–13 | Turn-based | Discard face-down declaring rank in cycle A-K. Challenge previous move. Liar picks up pile. |
| **Speed** | `speed` | 2–4 | Real-time | Real-time shedding. Race cards onto ascending (+1) and descending (-1) center piles. |
| **Crazy Eights** | `crazy_eights` | 2–7 | Turn-based | Match suit or rank. 8s are wild cards. Skip, reverse, and draw-two action cards. |

---

## 5. Simulated Coin Economy & Blockchain-Style Ledger

### 5.1 Fixed Supply Invariant
The total coin economy has an unalterable supply of **1,000,000,000** Game Coins held across three balance categories:
$$\text{Reserve} + \text{Circulating} + \text{Pool Balances} = 1,000,000,000$$

- **Developer Reserve:** Starts at 1,000,000,000 coins. All grants and initial pool allocations are funded from here. Mid-play minting is strictly prohibited.
- **Circulating:** Personal wallets + in-flight escrow and betting holds (owner `w:0:0`).
- **Pool Balances:** Group prize pools pre-allocated by admins to fund tables.

### 5.2 Hash-Chained Ledger
Every balance mutation appends an immutable entry to `club_ledger`:
```
entry_hash = sha256(prev_hash + "|" + seq + "|" + owner_key + "|" + amount + "|" + balance_after + "|" + entry_type + "|" + ref_type + "|" + ref_id + "|" + note)
```
- Linked cryptographically from genesis hash (`0` $\times 64$).
- Validated via `models/card_club/economy.py:verify_ledger()` and `/club/api/ledger/verify`.

### 5.3 Transfers & Escrow
- **Peer-to-Peer Transfers:** Sender initiates transfer $\rightarrow$ recipient must accept before coins move atomically.
- **Escrow:** Coins locked in hold wallet (`w:0:0`) $\rightarrow$ completed to payee or refunded to payer upon settlement.
- **Betting:** Zero-sum bets on player's own active games. Personal bet limit capped at 500 coins. Hard-fail if pool bonus exceeds group pool funds.

---

## 6. Real-Time WebSockets Architecture

- **Backend:** `Flask-SocketIO` registered in `app.py` (`init_socketio()` in `controllers/card_club_controller.py`).
- **Rooms:** `user:{uid}` (auto-joined on connect for authenticated sessions) and `table:{tid}` (joined via `watch_table`, membership-checked).
- **Client events:**
  - `watch_table` / `unwatch_table`: Enter/leave a table's live room (server returns the current private view on watch).
  - `table_move`: Real-time or turn-based action dispatch (same service path as HTTP `POST /club/api/tables/<id>/move`).
- **Server pushes:**
  - `table_state`: Private view, emitted per seated user to their `user:{uid}` room after every move.
  - `table_spectate`: Public/spectator view, emitted to the `table:{tid}` room.
  - `table_settlement`: Final zero-sum settlement payload to players and spectators when a table finishes.
- **Automatic Fallback:** Client script `static/js/card_club.js` automatically falls back to HTTP REST endpoints (`/club/api/tables/<id>/state` and `/club/api/tables/<id>/move`, polling every 2.5s) if WebSocket connectivity is interrupted.

---

## 7. Testing & Verification

Run the automated test suites using the virtual environment:

```bash
# 1. Run the comprehensive Card Platform test suite (16 tests)
.venv/bin/python -m unittest -v tests/test_card_platform.py

# 2. Run the full regression test suite (Card Club + Cube Theory)
.venv/bin/python -m unittest -v test_app.CardClubTests
```

To run a direct ledger invariant check in Python:
```python
from models.card_club.economy import verify_ledger
print(verify_ledger())
# Output: {'ok': True, 'chain_ok': True, 'balances_ok': True, 'supply_ok': True, ...}
```
