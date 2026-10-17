"""Computer opponents: bot identities, table seating and move selection.

A bot is an ordinary `users` row carrying ``role = 'bot'`` and sitting in a
seat flagged ``club_seats.is_bot = 1``, so bots reuse the exact same
membership, escrow, settlement and broadcast paths as human players - a bot
payout goes through ``economy.settle_zero_sum`` exactly like a human's.

Two entry points matter:

* ``seat_bots(group_id, table_id, count)`` - fills a ``vs_com``/``solo``
  table with opponents before it starts.
* ``step(engine, bot_seats)`` - plays every bot seat until control returns to
  a human (or the game ends), returning the applied moves for the audit log.
"""

import hashlib
import itertools
import random
import secrets

from models.db import query_one, execute_insert, execute_update
from models.card_club import economy, groups
from models.card_club.engines.base import RANK_VALUE
from models.card_club.engines.poker_hands import evaluate_best

BOT_ROLE = "bot"

# (display name, avatar colour) - index-stable so a bot keeps its identity
# across every table it sits at.
ROSTER = [
    ("Nova", "#f472b6"), ("Orion", "#38bdf8"), ("Zephyr", "#c084fc"),
    ("Atlas", "#34d399"), ("Pixel", "#fbbf24"), ("Sable", "#f87171"),
    ("Quartz", "#22d3ee"), ("Ember", "#fb923c"), ("Onyx", "#94a3b8"),
    ("Iris", "#a3e635"),
]

TRICK_SLUGS = {"call_break", "29", "knockout_whist", "rantergoround"}
WILD_SLUGS = {"blitz", "crazy_eights"}

_STRENGTH_29 = {"7": 1, "8": 2, "Q": 3, "K": 4, "T": 5, "A": 6, "9": 7, "J": 8}


# --------------------------------------------------------------- identities
def _rank(card):
    return RANK_VALUE[card[1]]


def _card_strength(slug, card):
    if slug == "29":
        return _STRENGTH_29.get(card[1], 0)
    return _rank(card)


def bot_username(slot):
    name, _ = ROSTER[slot % len(ROSTER)]
    suffix = "" if slot < len(ROSTER) else f"{slot // len(ROSTER) + 1}"
    return f"bot_{name.lower()}{suffix}"


def bot_display_name(slot):
    name, _ = ROSTER[slot % len(ROSTER)]
    suffix = "" if slot < len(ROSTER) else f" {slot // len(ROSTER) + 1}"
    return f"{name}{suffix}"


def ensure_bot(slot):
    """Return ``(user_id, display_name)``, creating the bot user on demand."""
    username = bot_username(slot)
    name = bot_display_name(slot)
    _, color = ROSTER[slot % len(ROSTER)]
    row = query_one("SELECT id FROM users WHERE username = %s",
                    "SELECT id FROM users WHERE username = ?", (username,))
    if row:
        uid = int(row["id"] if isinstance(row, dict) else row[0])
        execute_update("UPDATE users SET role = %s, avatar_color = %s WHERE id = %s",
                       "UPDATE users SET role = ?, avatar_color = ? WHERE id = ?",
                       (BOT_ROLE, color, uid))
        return uid, name
    try:
        uid = execute_insert(
            "INSERT INTO users (username, email, password_hash, role, avatar_color) "
            "VALUES (%s,%s,%s,%s,%s)",
            "INSERT INTO users (username, email, password_hash, role, avatar_color) "
            "VALUES (?,?,?,?,?)",
            (username, f"{username}@rubique.local", secrets.token_hex(32),
             BOT_ROLE, color))
    except Exception:
        row = query_one("SELECT id FROM users WHERE username = %s",
                        "SELECT id FROM users WHERE username = ?", (username,))
        if not row:
            raise
        uid = int(row["id"] if isinstance(row, dict) else row[0])
    return uid, name


def is_bot_uid(user_id):
    row = query_one("SELECT role FROM users WHERE id = %s",
                    "SELECT role FROM users WHERE id = ?", (user_id,))
    if not row:
        return False
    role = row["role"] if isinstance(row, dict) else row[0]
    return role == BOT_ROLE


# ------------------------------------------------------------------ seating
def _join_group(group_id, user_id, display_name=""):
    """Bots hold a regular membership row (role ``bot``) so every seat, escrow
    and settlement path stays identical to a human player."""
    if groups.is_member(group_id, user_id):
        return
    try:
        execute_insert(
            "INSERT INTO club_group_members (group_id, user_id, role, fake_name) "
            "VALUES (%s,%s,%s,%s)",
            "INSERT INTO club_group_members (group_id, user_id, role, fake_name) "
            "VALUES (?,?,?,?)",
            (group_id, user_id, BOT_ROLE, (display_name or "").strip() or None))
    except Exception:
        pass


def _ensure_funds(user_id, need):
    """A bot must be able to escrow the same stake a human posts."""
    if need <= 0:
        return
    bal = economy.balances_view(user_id)["personal"]
    if bal >= need:
        return
    shortfall = min(need - bal, economy.MAX_BET_LIMIT)
    economy.replenish_wallet(user_id, shortfall)


def seat_bots(group_id, table_id, count, stake=0):
    """Seat ``count`` bots at a waiting table. Returns the seated user ids."""
    from models.card_club import gameplay
    if count <= 0:
        return []
    taken = {int(s["user_id"]) for s in gameplay.seats(table_id)}
    seated = []
    slot = 0
    while len(seated) < count and slot < len(ROSTER) * 3:
        uid, name = ensure_bot(slot)
        slot += 1
        if uid in taken:
            continue
        _join_group(group_id, uid, name)
        _ensure_funds(uid, int(stake or 0))
        gameplay.join_table(group_id, uid, table_id, fake_name=name)
        execute_update(
            "UPDATE club_seats SET is_bot = 1, rules_read = 1 "
            "WHERE table_id = %s AND user_id = %s",
            "UPDATE club_seats SET is_bot = 1, rules_read = 1 "
            "WHERE table_id = ? AND user_id = ?",
            (table_id, uid))
        taken.add(uid)
        seated.append(uid)
    return seated


def bot_seats_of(table_id, seat_rows=None):
    from models.card_club import gameplay
    rows = seat_rows if seat_rows is not None else gameplay.seats(table_id)
    return sorted(int(s["seat_index"]) for s in rows if s.get("is_bot"))


def bots_needed(t, info, seated):
    """How many computer opponents a ``vs_com``/``solo`` table still needs."""
    mode = (t.get("mode") or "multiplayer") if isinstance(t, dict) else "multiplayer"
    if mode not in ("vs_com", "solo"):
        return 0
    humans = [s for s in seated if not s.get("is_bot")]
    bots = [s for s in seated if s.get("is_bot")]
    if not humans:
        return 0
    if mode == "solo":
        target = max(info["min"], 1)
    else:
        target = max(info["min"], min(int(t.get("max_seats") or info["max"]),
                                       info["max"]))
    want = target - len(humans) - len(bots)
    room = min(int(t.get("max_seats") or info["max"]), info["max"]) - len(seated)
    return max(0, min(want, room))


# -------------------------------------------------------------- move choice
def current_actor(state):
    if state.get("phase") == "bidding" and isinstance(state.get("bid_turn"), int):
        return state["bid_turn"]
    turn = state.get("turn")
    return turn if isinstance(turn, int) and turn >= 0 else None


def choose_action(state, seat, legal, rng=None):
    """Pick a legal action for a bot. Always returns an element of ``legal``."""
    if not legal:
        return None
    slug = state.get("slug") or ""
    handler = _HANDLERS.get(slug)
    if handler:
        picked = handler(state, seat, legal)
        if picked is not None:
            return picked
    return _ranked(state, seat, legal)[0]


def _ranked(state, seat, legal):
    scored = [(_score(state, seat, a), i, a) for i, a in enumerate(legal)]
    scored.sort(key=lambda t: (-t[0], t[1]))          # deterministic tie-break
    return [a for _, _, a in scored]


def step(engine, bot_seats, max_steps=200, rng=None):
    """Play bot seats until it is a human's turn (or the game ends).

    Returns the list of applied ``{"seat":.., "action":..}`` moves so callers
    can append them to the move audit log.
    """
    if not bot_seats:
        return []
    applied = []
    bots = list(bot_seats)
    for _ in range(max_steps):
        if engine.is_over():
            break
        state = engine.state
        actor = current_actor(state)
        if actor is not None and actor not in bots:
            break
        order = [actor] if actor is not None else bots
        progressed = False
        for seat in order:
            legal = engine.legal_actions(seat)
            if not legal:
                continue
            for action in _candidates(state, seat, legal):
                try:
                    engine.apply(seat, action)
                except Exception:
                    continue                             # engine rejected it
                applied.append({"seat": seat, "action": action})
                progressed = True
                break
            if progressed:
                break
        if not progressed:
            break
    return applied


def _candidates(state, seat, legal):
    """Handler pick first, then every legal action as a safety net."""
    picked = choose_action(state, seat, legal)
    if picked is not None and picked in legal:
        return [picked] + [a for a in _ranked(state, seat, legal) if a != picked]
    return _ranked(state, seat, legal)


# ---------------------------------------------------------------- scoring
def _trick_cards(state):
    raw = state.get("trick") or []
    out = []
    for entry in raw:
        if isinstance(entry, dict):
            if "card" in entry:
                out.append(entry["card"])
            elif "cards" in entry:
                out.extend(entry["cards"])
        elif isinstance(entry, str):
            out.append(entry)
    return out


def _play_score(state, slug, action):
    card = action.get("card")
    cards = action.get("cards") or ([card] if card else [])
    if not cards:
        return 0.0
    if slug in TRICK_SLUGS:
        trick = _trick_cards(state)
        best = max((_card_strength(slug, c) for c in trick), default=0)
        strength = _card_strength(slug, cards[0])
        if trick and strength > best:
            return 50.0 - strength                       # cheapest winner
        return -float(strength)                          # dump the low card
    if slug in ("scopa",):
        return -float(_rank(cards[0]))
    score = -float(_rank(cards[0]))
    if slug in WILD_SLUGS and cards[0][1] == "8":
        score = -50.0                                    # keep wilds back
    return score + len(cards) * 5.0


def _score(state, seat, action):
    slug = state.get("slug") or ""
    kind = action.get("action")
    if kind == "play":
        return _play_score(state, slug, action)
    if kind == "take_discard":
        return -300.0
    if kind == "draw":
        return -500.0
    if kind == "pass":
        return -1000.0
    if kind == "meld":
        return 1000.0 + len(action.get("cards") or []) * 5.0
    if kind == "discard":
        return -float(_rank(action.get("card") or "S2"))
    if kind == "declare":
        count = int(action.get("count") or 1)
        claimed = (state.get("declared") or {}).get("count") or 0
        if claimed >= 2:
            return 300.0                                 # call the bluff
        return 200.0 - count * 2.0                       # small honest claims
    if kind == "challenge":
        claimed = (state.get("declared") or {}).get("count") or 0
        return 300.0 if claimed >= 2 else -100.0
    if kind == "see_cards":
        return 5000.0
    if kind == "grab":
        return 5000.0
    if kind == "react":
        return 3000.0
    if kind == "arrange":
        return 1000.0
    if kind == "flip":
        return 2000.0
    if kind == "slap":
        return -2000.0                                  # bots only slap on pattern
    if kind in ("hit", "check", "call", "raise", "chaal", "swap", "end_hole"):
        return 10.0
    if kind in ("stand", "double", "fold", "pack", "show"):
        return 5.0
    if kind == "bid":
        return 100.0
    if kind == "reveal_trump":
        return 50.0
    return 0.0


# ------------------------------------------------------------- hand reads
def _blackjack_value(cards):
    total = aces = 0
    for c in cards:
        r = c[1]
        if r in "TJQK":
            total += 10
        elif r == "A":
            total += 11
            aces += 1
        else:
            total += int(r)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def _poker_strength(state, seat):
    hole = state.get("hands", {}).get(str(seat)) or []
    board = state.get("visible_community") or []
    if len(hole) + len(board) >= 5:
        cat, top = evaluate_best(list(hole) + board)[:2]
        base = (cat + 1) / 9.0
        return min(1.0, base + (top / 14.0) * (1.0 / 9.0) * 0.5)
    if len(hole) < 2:
        return 0.3
    hi, lo = sorted((_rank(c) for c in hole), reverse=True)
    if hi == lo:
        value = 0.40 + hi / 32.0
    else:
        value = (hi + lo / 2.0) / 28.0
    if len(hole) == 2 and hole[0][0] == hole[1][0]:
        value += 0.06
    gap = hi - lo
    if gap == 1:
        value += 0.05
    elif gap == 2:
        value += 0.02
    return max(0.0, min(1.0, value))


def _teen_patti_strength(cards):
    vals = sorted((_rank(c) for c in cards))
    if len(vals) == 3 and vals[0] == vals[2]:
        return 0.95
    if len(vals) == 3 and (vals[0] == vals[1] or vals[1] == vals[2]):
        return 0.75
    return 0.20 + sum(vals) / 42.0


# ------------------------------------------------------------- game hooks
def _h_poker(state, seat, legal):
    strength = _poker_strength(state, seat)
    to_call = max(0, int(state.get("current_bet") or 0) -
                  int((state.get("round_bets") or {}).get(str(seat), 0)))
    pick = {a["action"]: a for a in legal}
    if to_call <= 0:
        if "raise" in pick and strength > 0.72:
            return pick["raise"]
        if "check" in pick:
            return pick["check"]
        return None
    if strength > 0.72:
        for kind in ("raise", "allin", "call"):
            if kind in pick:
                return pick[kind]
    if strength > 0.45:
        for kind in ("call", "check", "allin"):
            if kind in pick:
                return pick[kind]
    for kind in ("fold", "call"):
        if kind in pick:
            return pick[kind]
    return None


def _h_gops(state, seat, legal):
    prize = int(state.get("prize") or 0)
    chips = int((state.get("chips") or {}).get(str(seat), 0))
    target = max(0, min(chips, int(round(prize * 0.7))))
    best, best_gap = None, None
    for a in legal:
        gap = abs(int(a.get("amount", 0)) - target)
        if best_gap is None or gap < best_gap:
            best, best_gap = a, gap
    return best


def _h_blackjack(state, seat, legal):
    hole = state.get("hands", {}).get(str(seat)) or []
    value = _blackjack_value(hole)
    pick = {a["action"]: a for a in legal}
    if value < 17 and "hit" in pick:
        return pick["hit"]
    return pick.get("stand") or None


def _h_teen_patti(state, seat, legal):
    pick = {a["action"]: a for a in legal}
    if "see_cards" in pick:
        return pick["see_cards"]
    hole = state.get("hands", {}).get(str(seat)) or []
    seen = (state.get("seen") or {}).get(str(seat))
    strength = _teen_patti_strength(hole) if (seen and hole) else 0.5
    if strength > 0.62:
        for kind in ("raise", "chaal", "show"):
            if kind in pick:
                return pick[kind]
    if strength < 0.34 and int(state.get("current_bet") or 0) > 10:
        if "pack" in pick:
            return pick["pack"]
    return pick.get("chaal") or pick.get("show") or pick.get("pack")


def _h_hazari(state, seat, legal):
    from models.card_club.engines.popular_classics import Hazari
    if not any(a.get("action") == "arrange" for a in legal):
        return None
    hand = state.get("hands", {}).get(str(seat)) or []
    if len(hand) != 13:
        return {"action": "arrange"}
    four = max(itertools.combinations(hand, 4), key=Hazari.evaluate_combo)
    rest = [c for c in hand if c not in four]
    threes = []
    pool = list(rest)
    for _ in range(3):
        best = max(itertools.combinations(pool, 3), key=Hazari.evaluate_combo)
        threes.append(list(best))
        pool = [c for c in pool if c not in best]
    return {"action": "arrange", "groups": [threes[0], threes[1], threes[2], list(four)]}


def _h_bidding(state, seat, legal):
    slug = state.get("slug")
    hand = state.get("hands", {}).get(str(seat)) or []
    bids = [a for a in legal if a.get("action") == "bid"]
    if not bids:
        return None
    if slug == "call_break":
        estimate = sum(1 for c in hand if c[1] in ("A", "K")) + \
            sum(1 for c in hand if c[0] == "S" and c[1] in ("Q", "J"))
        estimate = max(1, min(estimate, 13))
        return min(bids, key=lambda a: abs(int(a.get("amount", 1)) - estimate))
    if slug == "29":
        power = sum(1 for c in hand if c[1] in ("J", "9"))
        if power >= 2:
            return min(bids, key=lambda a: int(a.get("value", 16)))
        return next((a for a in legal if a.get("action") == "pass"), None)
    if slug == "bridge":
        hcp = sum(4 if c[1] == "A" else 3 if c[1] == "K" else
                  2 if c[1] == "Q" else 1 if c[1] == "J" else 0 for c in hand)
        if hcp >= 12:
            lvl1 = [a for a in bids if int(a.get("level", 9)) == 1]
            if lvl1:
                nt = [a for a in lvl1 if a.get("suit") == "NT"]
                return (nt or lvl1)[0]
        return next((a for a in legal if a.get("action") == "pass"), None)
    return min(bids, key=lambda a: int(a.get("amount", a.get("value", 1))))


def _h_call_break(state, seat, legal):
    if state.get("phase") == "bidding":
        return _h_bidding(state, seat, legal)
    return None


def _h_29(state, seat, legal):
    if state.get("phase") == "bidding":
        return _h_bidding(state, seat, legal)
    return None


def _h_contract_bridge(state, seat, legal):
    if state.get("phase") == "bidding":
        return _h_bidding(state, seat, legal)
    return None


def _h_rummy(state, seat, legal):
    melds = [a for a in legal if a.get("action") == "meld"]
    if melds:
        return max(melds, key=lambda a: len(a.get("cards") or []))
    discards = [a for a in legal if a.get("action") == "discard"]
    if discards:
        return min(discards, key=lambda a: _rank(a.get("card")))
    return None


def _h_scopa(state, seat, legal):
    captures = [a for a in legal if a.get("capture")]
    if captures:
        return max(captures,
                   key=lambda a: (len(a["capture"]),
                                  sum(_rank(c) for c in a["capture"])))
    plain = [a for a in legal if a.get("action") == "play"]
    if plain:
        return min(plain, key=lambda a: _rank(a.get("card")))
    return None


def _h_golf(state, seat, legal):
    from models.card_club.engines.strategy import Golf
    s = state
    grid = list((s.get("grids") or {}).get(str(seat)) or [])
    stock = (s.get("stocks") or {}).get(str(seat)) or []
    up = s.get("up") or []
    source_card = {"stock": stock[-1] if stock else None,
                   "up": up[-1] if up else None}
    best, best_score = None, None
    for a in legal:
        if a.get("action") == "end_hole":
            best, best_score = a, -1
            continue
        card = source_card.get(a.get("source"))
        if not card or len(grid) != 6:
            continue
        trial = list(grid)
        trial[int(a.get("grid_index", 0))] = card
        score = Golf._score_grid(trial)
        if best_score is None or score < best_score:
            best, best_score = a, score
    return best


def _h_ers(state, seat, legal):
    pile = state.get("pile") or []
    slap_ok = False
    if len(pile) >= 2 and pile[-1][1] == pile[-2][1]:
        slap_ok = True
    elif len(pile) >= 3 and pile[-1][1] == pile[-3][1] and pile[-1][1] != pile[-2][1]:
        slap_ok = True
    elif len(pile) >= 3 and pile[-1][1] == pile[-2][1] == pile[-3][1]:
        slap_ok = True
    if slap_ok:
        for a in legal:
            if a.get("action") == "slap":
                return a
    for a in legal:
        if a.get("action") == "flip":
            return a
    return None


def _h_speed(state, seat, legal):
    plays = [a for a in legal if a.get("action") == "play" and a.get("card")]
    if plays:
        return min(plays, key=lambda a: _rank(a["card"]))
    return None


_HANDLERS = {
    "poker": _h_poker,
    "gops": _h_gops,
    "blackjack": _h_blackjack,
    "teen_patti": _h_teen_patti,
    "hazari": _h_hazari,
    "call_break": _h_call_break,
    "29": _h_29,
    "bridge": _h_contract_bridge,
    "rummy": _h_rummy,
    "scopa": _h_scopa,
    "golf": _h_golf,
    "ers": _h_ers,
    "speed": _h_speed,
}


def bot_seed(*parts):
    return int(hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)
