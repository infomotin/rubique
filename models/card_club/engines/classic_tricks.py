"""
CubePermutation AI - Classic Trick-Taking Playing Card Game Engines
===================================================================
Implements 7 classic 4-player trick-taking playing card games:
1. TwentyNineGame (29 Card Game - South Asian 32-card classic, J=3, 9=2, A=1, 10=1)
2. BridgeGame (Contract Bridge - bidding, declarer, dummy, contracts)
3. SpadesGame (Spades - partnerships, trick bids, bags, nil, broken spades)
4. HeartsGame (Hearts - trick avoidance, penalty hearts, Queen of Spades, shooting the moon)
5. WhistGame (Classic English Whist - turned-up trump, odd-tricks scoring)
6. OhHellGame (Oh Hell! - exact trick prediction bidding)
7. EuchreGame (Euchre - 24 cards, Right & Left Bowers, march & euchre scoring)

All engines feature built-in smart AI players for seats 1, 2, and 3,
allowing the human player (seat 0) to play instantly against partner and opponent bots.
"""

import random

SUITS = ["S", "H", "D", "C"]
SUIT_NAMES = {"S": "Spades", "H": "Hearts", "D": "Diamonds", "C": "Clubs"}
SUIT_SYMBOLS = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
SUIT_COLORS = {"S": "#94a3b8", "H": "#ef4444", "D": "#f97316", "C": "#38bdf8"}

STANDARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
STANDARD_VALUES = {r: i + 2 for i, r in enumerate(STANDARD_RANKS)}

SEAT_NAMES = ["You (South)", "West (Bot)", "North (Partner Bot)", "East (Bot)"]
SEAT_ROLES = ["South", "West", "North", "East"]

def full_deck():
    return [s + r for s in SUITS for r in STANDARD_RANKS]

def suit_of(card):
    return card[0]

def rank_of(card):
    return card[1:]

def pretty_card(card):
    if not card:
        return ""
    s, r = card[0], card[1:]
    r_disp = "10" if r == "T" else r
    return f"{SUIT_SYMBOLS[s]}{r_disp}"


# =====================================================================
# 1. TWENTY-NINE (29 CARD GAME)
# =====================================================================
class TwentyNineGame:
    """
    29 Card Game: 32 cards (7, 8, Q, K, 10, A, 9, J in each suit).
    Rank order: J(3pts) > 9(2pts) > A(1pt) > 10(1pt) > K(0) > Q(0) > 8(0) > 7(0).
    Total points: 28 card points + 1 point for the 8th (last) trick = 29.
    Partnerships: Team 0 (0 & 2) vs Team 1 (1 & 3).
    Bidding: 16 to 28. Winner sets secret trump suit.
    """
    slug = "29"
    title = "29 Card Game (Twenty-Nine)"
    description = "Classic South Asian 32-card trick game with Jack=3, 9=2, Ace=1, 10=1, and secret trump bidding."

    RANKS = ["7", "8", "Q", "K", "T", "A", "9", "J"]
    RANK_STRENGTH = {"7": 1, "8": 2, "Q": 3, "K": 4, "T": 5, "A": 6, "9": 7, "J": 8}
    CARD_POINTS = {"J": 3, "9": 2, "A": 1, "T": 1, "K": 0, "Q": 0, "8": 0, "7": 0}

    @classmethod
    def create(cls, seed=None):
        rng = random.Random(seed)
        deck = [s + r for s in SUITS for r in cls.RANKS]
        rng.shuffle(deck)

        # 4 cards dealt first, next 4 cards dealt after bidding
        hands = {str(i): [deck.pop() for _ in range(4)] for i in range(4)}
        second_half = {str(i): [deck.pop() for _ in range(4)] for i in range(4)}

        state = {
            "slug": cls.slug,
            "phase": "bidding",  # bidding -> playing -> round_over
            "hands": hands,
            "second_half": second_half,
            "bids": {},
            "bid_turn": 0,
            "high_bid": 15,
            "high_bidder": None,
            "trump_suit": None,
            "trump_revealed": False,
            "tricks": {str(i): 0 for i in range(4)},
            "card_points": {"team0": 0, "team1": 0},
            "trick": [],
            "lead_suit": None,
            "turn": 0,
            "tricks_history": [],
            "log": ["Game started: 32-card deck dealt. Bidding phase begun (16 to 28)."],
            "over": False,
            "winner_team": None
        }
        return state

    @classmethod
    def legal_actions(cls, state, seat):
        if state["over"]:
            return []
        
        phase = state["phase"]
        if phase == "bidding":
            if seat != state["bid_turn"]:
                return []
            high = state["high_bid"]
            actions = [{"action": "pass"}]
            for b in range(max(16, high + 1), 29):
                actions.append({"action": "bid", "value": b})
            return actions

        elif phase == "playing":
            if seat != state["turn"]:
                return []
            hand = state["hands"][str(seat)]
            lead = state["lead_suit"]
            actions = []
            
            # Follow suit rule
            if lead:
                follows = [c for c in hand if suit_of(c) == lead]
                if follows:
                    return [{"action": "play", "card": c} for c in follows]
                # Can't follow suit: can reveal trump if not revealed and holding trump
                if not state["trump_revealed"]:
                    actions.append({"action": "reveal_trump"})
            
            # Any card in hand can be played if no follow suit restriction
            for c in hand:
                actions.append({"action": "play", "card": c})
            return actions

        return []

    @classmethod
    def apply(cls, state, seat, action):
        log = state["log"]
        act = action.get("action")

        if state["phase"] == "bidding":
            if act == "bid":
                val = int(action.get("value"))
                state["high_bid"] = val
                state["high_bidder"] = seat
                state["bids"][str(seat)] = val
                log.append(f"{SEAT_NAMES[seat]} bid {val} points.")
            else:
                state["bids"][str(seat)] = "pass"
                log.append(f"{SEAT_NAMES[seat]} passed.")

            # Check if bidding is complete (4 passes or everyone answered)
            active_bidders = [i for i in range(4) if state["bids"].get(str(i)) != "pass"]
            if len(state["bids"]) >= 4 or (len(active_bidders) <= 1 and state["high_bidder"] is not None):
                if state["high_bidder"] is None:
                    # Default minimum bidder
                    state["high_bidder"] = 0
                    state["high_bid"] = 16
                
                bidder = state["high_bidder"]
                # Bot sets trump if bot, otherwise wait for player trump or auto-set player's strongest suit
                suits_in_hand = [suit_of(c) for c in state["hands"][str(bidder)]]
                trump = action.get("trump") or max(set(suits_in_hand), key=suits_in_hand.count)
                state["trump_suit"] = trump
                state["phase"] = "playing"
                state["turn"] = bidder

                # Deal remaining 4 cards to each player
                for i in range(4):
                    state["hands"][str(i)].extend(state["second_half"][str(i)])
                state["second_half"] = {}

                log.append(f"{SEAT_NAMES[bidder]} won bidding at {state['high_bid']}! Secret trump set. Second 4 cards dealt.")
            else:
                state["bid_turn"] = (state["bid_turn"] + 1) % 4
            return state

        elif state["phase"] == "playing":
            if act == "reveal_trump":
                state["trump_revealed"] = True
                log.append(f"{SEAT_NAMES[seat]} asked for TRUMP! Trump is revealed as {SUIT_NAMES[state['trump_suit']]} ({SUIT_SYMBOLS[state['trump_suit']]})!")
                return state

            card = action.get("card")
            hand = state["hands"][str(seat)]
            hand.remove(card)

            if not state["trick"]:
                state["lead_suit"] = suit_of(card)
            state["trick"].append({"seat": seat, "card": card})
            log.append(f"{SEAT_NAMES[seat]} played {pretty_card(card)}")

            # Trick complete (4 cards)
            if len(state["trick"]) == 4:
                lead = state["lead_suit"]
                trump = state["trump_suit"] if state["trump_revealed"] else None

                def score_card(entry):
                    c = entry["card"]
                    s, r = suit_of(c), rank_of(c)
                    is_trump = 2 if s == trump else (1 if s == lead else 0)
                    return (is_trump, cls.RANK_STRENGTH[r])

                winning_entry = max(state["trick"], key=score_card)
                winner = winning_entry["seat"]
                winner_team = "team0" if winner in (0, 2) else "team1"

                # Calculate points in trick
                trick_pts = sum(cls.CARD_POINTS[rank_of(e["card"])] for e in state["trick"])
                # Last trick gets +1 point
                if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                    trick_pts += 1

                state["tricks"][str(winner)] += 1
                state["card_points"][winner_team] += trick_pts
                state["tricks_history"].append({
                    "trick": list(state["trick"]),
                    "winner": winner,
                    "points": trick_pts
                })
                log.append(f"{SEAT_NAMES[winner]} won the trick (+{trick_pts} pts, Team {winner_team[-1]} total: {state['card_points'][winner_team]})")

                state["trick"] = []
                state["lead_suit"] = None
                state["turn"] = winner

                # Check game over (all 8 tricks played)
                if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                    state["phase"] = "round_over"
                    state["over"] = True
                    bidder_team = "team0" if state["high_bidder"] in (0, 2) else "team1"
                    target = state["high_bid"]
                    achieved = state["card_points"][bidder_team]

                    if achieved >= target:
                        state["winner_team"] = bidder_team
                        log.append(f"GAME OVER: Bidder Team ({bidder_team.upper()}) made their contract! ({achieved} / {target} pts)")
                    else:
                        state["winner_team"] = "team1" if bidder_team == "team0" else "team0"
                        log.append(f"GAME OVER: Bidder Team ({bidder_team.upper()}) failed contract ({achieved} / {target} pts). Defending Team wins!")
            else:
                state["turn"] = (seat + 1) % 4

            return state

        return state


# =====================================================================
# 2. SPADES GAME
# =====================================================================
class SpadesGame:
    """
    Spades: Standard 52-card deck. Spades are always trump.
    Partnerships: Team 0 (0 & 2) vs Team 1 (1 & 3).
    Bidding: Each player bids trick count (or Nil=0). Team bid = sum of partners.
    Rules: Cannot lead Spades until broken. Follow suit.
    """
    slug = "spades"
    title = "Spades"
    description = "4-Player Partnership trick-taking game. Spades are permanent trump. Bid your tricks accurately to avoid sandbag penalties."

    @classmethod
    def create(cls, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)

        hands = {str(i): sorted([deck.pop() for _ in range(13)], key=lambda c: (c[0], STANDARD_VALUES[c[1:]])) for i in range(4)}

        state = {
            "slug": cls.slug,
            "phase": "bidding",
            "hands": hands,
            "bids": {},
            "bid_turn": 0,
            "trump_suit": "S",
            "spades_broken": False,
            "tricks": {str(i): 0 for i in range(4)},
            "trick": [],
            "lead_suit": None,
            "turn": 0,
            "team_bids": {"team0": 0, "team1": 0},
            "team_tricks": {"team0": 0, "team1": 0},
            "scores": {"team0": 0, "team1": 0},
            "log": ["Spades Match initialized: 52 cards dealt (13 to each player). Bidding open."],
            "over": False,
            "winner_team": None
        }
        return state

    @classmethod
    def legal_actions(cls, state, seat):
        if state["over"]:
            return []
        if state["phase"] == "bidding":
            if seat != state["bid_turn"]:
                return []
            return [{"action": "bid", "value": b} for b in range(0, 14)]
        
        elif state["phase"] == "playing":
            if seat != state["turn"]:
                return []
            hand = state["hands"][str(seat)]
            lead = state["lead_suit"]
            
            if lead:
                follows = [c for c in hand if suit_of(c) == lead]
                if follows:
                    return [{"action": "play", "card": c} for c in follows]
                return [{"action": "play", "card": c} for c in hand]
            else:
                # Leading card: cannot lead Spades unless broken or only Spades held
                if not state["spades_broken"]:
                    non_spades = [c for c in hand if suit_of(c) != "S"]
                    if non_spades:
                        return [{"action": "play", "card": c} for c in non_spades]
                return [{"action": "play", "card": c} for c in hand]
        return []

    @classmethod
    def apply(cls, state, seat, action):
        log = state["log"]
        act = action.get("action")

        if state["phase"] == "bidding":
            val = int(action.get("value", 3))
            state["bids"][str(seat)] = val
            log.append(f"{SEAT_NAMES[seat]} bid {val} tricks.")

            if len(state["bids"]) == 4:
                state["team_bids"]["team0"] = state["bids"]["0"] + state["bids"]["2"]
                state["team_bids"]["team1"] = state["bids"]["1"] + state["bids"]["3"]
                state["phase"] = "playing"
                state["turn"] = 0
                log.append(f"Bidding complete! Team 0 (South+North) bid {state['team_bids']['team0']}, Team 1 (West+East) bid {state['team_bids']['team1']}.")
            else:
                state["bid_turn"] = (state["bid_turn"] + 1) % 4
            return state

        elif state["phase"] == "playing":
            card = action.get("card")
            hand = state["hands"][str(seat)]
            hand.remove(card)

            if suit_of(card) == "S" and not state["spades_broken"]:
                state["spades_broken"] = True
                log.append("SPADES BROKEN! Spades may now be led.")

            if not state["trick"]:
                state["lead_suit"] = suit_of(card)
            state["trick"].append({"seat": seat, "card": card})
            log.append(f"{SEAT_NAMES[seat]} played {pretty_card(card)}")

            if len(state["trick"]) == 4:
                lead = state["lead_suit"]
                
                def eval_card(e):
                    c = e["card"]
                    s, r = suit_of(c), rank_of(c)
                    suit_mult = 2 if s == "S" else (1 if s == lead else 0)
                    return (suit_mult, STANDARD_VALUES[r])

                win_e = max(state["trick"], key=eval_card)
                winner = win_e["seat"]
                team = "team0" if winner in (0, 2) else "team1"

                state["tricks"][str(winner)] += 1
                state["team_tricks"][team] += 1
                log.append(f"{SEAT_NAMES[winner]} took the trick (Team {team[-1]} total: {state['team_tricks'][team]})")

                state["trick"] = []
                state["lead_suit"] = None
                state["turn"] = winner

                if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                    state["over"] = True
                    state["phase"] = "round_over"
                    # Calculate team scores
                    for t in ["team0", "team1"]:
                        bid = state["team_bids"][t]
                        got = state["team_tricks"][t]
                        if got >= bid:
                            bags = got - bid
                            state["scores"][t] = (bid * 10) + bags
                        else:
                            state["scores"][t] = -(bid * 10)

                    state["winner_team"] = "team0" if state["scores"]["team0"] >= state["scores"]["team1"] else "team1"
                    log.append(f"MATCH OVER! Team 0: {state['scores']['team0']} pts, Team 1: {state['scores']['team1']} pts. Winner: {state['winner_team'].upper()}")
            else:
                state["turn"] = (seat + 1) % 4
            return state

        return state


# =====================================================================
# 3. HEARTS GAME
# =====================================================================
class HeartsGame:
    """
    Hearts: 52 cards, 4 players (free-for-all).
    Penalty Cards: Each Heart = 1 pt, Queen of Spades (QS) = 13 pts.
    Rules: 2 of Clubs leads first trick. No penalties on trick 1.
    Hearts cannot be led until broken.
    Shooting the Moon: Collect all 26 penalty points = 0 for you, 26 for all others!
    Lowest penalty score wins.
    """
    slug = "hearts"
    title = "Hearts"
    description = "Classic 4-player trick avoidance game. Avoid Hearts (1 pt) and Queen of Spades (13 pts), or Shoot the Moon for 26 points!"

    @classmethod
    def create(cls, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)

        hands = {str(i): sorted([deck.pop() for _ in range(13)], key=lambda c: (c[0], STANDARD_VALUES[c[1:]])) for i in range(4)}

        # 2 of Clubs starts first trick
        starter = 0
        for i in range(4):
            if "C2" in hands[str(i)]:
                starter = i
                break

        state = {
            "slug": cls.slug,
            "phase": "playing",
            "hands": hands,
            "trick": [],
            "lead_suit": None,
            "turn": starter,
            "round_num": 1,
            "hearts_broken": False,
            "first_trick": True,
            "tricks": {str(i): 0 for i in range(4)},
            "penalty_points": {str(i): 0 for i in range(4)},
            "log": [f"Hearts started: 52 cards dealt. {SEAT_NAMES[starter]} holds 2♣ and leads the first trick."],
            "over": False,
            "winner": None
        }
        return state

    @classmethod
    def legal_actions(cls, state, seat):
        if state["over"] or seat != state["turn"]:
            return []
        hand = state["hands"][str(seat)]

        if state["first_trick"] and "C2" in hand:
            return [{"action": "play", "card": "C2"}]

        lead = state["lead_suit"]
        if lead:
            follows = [c for c in hand if suit_of(c) == lead]
            if follows:
                return [{"action": "play", "card": c} for c in follows]
            # No follow suit: can discard anything except penalty on first trick
            if state["first_trick"]:
                safe = [c for c in hand if suit_of(c) != "H" and c != "SQ"]
                if safe:
                    return [{"action": "play", "card": c} for c in safe]
            return [{"action": "play", "card": c} for c in hand]
        else:
            # Lead: cannot lead Hearts unless broken or only Hearts left
            if not state["hearts_broken"]:
                non_hearts = [c for c in hand if suit_of(c) != "H"]
                if non_hearts:
                    return [{"action": "play", "card": c} for c in non_hearts]
            return [{"action": "play", "card": c} for c in hand]

    @classmethod
    def apply(cls, state, seat, action):
        card = action.get("card")
        hand = state["hands"][str(seat)]
        hand.remove(card)
        log = state["log"]

        if suit_of(card) == "H" and not state["hearts_broken"]:
            state["hearts_broken"] = True
            log.append("HEARTS BROKEN! Hearts may now be led.")

        if not state["trick"]:
            state["lead_suit"] = suit_of(card)
        state["trick"].append({"seat": seat, "card": card})
        log.append(f"{SEAT_NAMES[seat]} played {pretty_card(card)}")

        if len(state["trick"]) == 4:
            state["first_trick"] = False
            lead = state["lead_suit"]
            
            # Winner is highest of led suit (no trump in Hearts)
            def val_e(e):
                c = e["card"]
                return STANDARD_VALUES[rank_of(c)] if suit_of(c) == lead else -1

            winner_e = max(state["trick"], key=val_e)
            winner = winner_e["seat"]

            # Calculate penalty points
            penalty = 0
            for e in state["trick"]:
                c = e["card"]
                if suit_of(c) == "H":
                    penalty += 1
                elif c == "SQ":
                    penalty += 13

            state["tricks"][str(winner)] += 1
            state["penalty_points"][str(winner)] += penalty
            pen_text = f" ({penalty} penalty pts!)" if penalty > 0 else ""
            log.append(f"{SEAT_NAMES[winner]} won trick{pen_text}")

            state["trick"] = []
            state["lead_suit"] = None
            state["turn"] = winner

            # Check end of hand
            if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                state["over"] = True
                state["phase"] = "round_over"
                # Check Shoot the Moon
                shooter = None
                for i in range(4):
                    if state["penalty_points"][str(i)] == 26:
                        shooter = i
                        break

                if shooter is not None:
                    for i in range(4):
                        state["penalty_points"][str(i)] = 0 if i == shooter else 26
                    log.append(f"MOON SHOT! {SEAT_NAMES[shooter]} shot the moon! 0 penalty points, 26 to all opponents!")

                best_player = min(range(4), key=lambda i: state["penalty_points"][str(i)])
                state["winner"] = best_player
                log.append(f"GAME OVER: Winner is {SEAT_NAMES[best_player]} with lowest penalty score ({state['penalty_points'][str(best_player)]} pts)!")
        else:
            state["turn"] = (seat + 1) % 4
        return state


# =====================================================================
# 4. CONTRACT BRIDGE
# =====================================================================
class BridgeGame:
    """
    Contract Bridge: 52 cards. 4 players in 2 partnerships (N-S vs E-W).
    Bidding: Levels 1-7 in C, D, H, S, NT. Pass.
    Contract: Sets trump and Declarer.
    Dummy: Declarer's partner's cards are opened face up after opening lead!
    """
    slug = "bridge"
    title = "Contract Bridge"
    description = "Grandmaster 4-player partnership game. Strategic bidding, declarer contract execution, and open dummy hand."

    SUIT_ORDER = ["C", "D", "H", "S", "NT"]

    @classmethod
    def create(cls, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)

        hands = {str(i): sorted([deck.pop() for _ in range(13)], key=lambda c: (c[0], STANDARD_VALUES[c[1:]])) for i in range(4)}

        state = {
            "slug": cls.slug,
            "phase": "bidding",
            "hands": hands,
            "bids": {},
            "bid_turn": 0,
            "contract": None,
            "declarer": None,
            "dummy": None,
            "dummy_revealed": False,
            "trump_suit": None,
            "contract_tricks": 0,
            "tricks": {str(i): 0 for i in range(4)},
            "team_tricks": {"team0": 0, "team1": 0},
            "trick": [],
            "lead_suit": None,
            "turn": 0,
            "log": ["Bridge Match started: 52 cards dealt. Bidding opened from South."],
            "over": False,
            "winner_team": None
        }
        return state

    @classmethod
    def legal_actions(cls, state, seat):
        if state["over"]:
            return []
        if state["phase"] == "bidding":
            if seat != state["bid_turn"]:
                return []
            actions = [{"action": "pass"}]
            # Standard simple contract bids: 1 to 4 in C, D, H, S, NT
            for lvl in range(1, 5):
                for s in cls.SUIT_ORDER:
                    actions.append({"action": "bid", "level": lvl, "suit": s})
            return actions

        elif state["phase"] == "playing":
            effective_seat = seat
            # If declarer's turn and it's dummy's turn to play, declarer controls dummy
            if state["turn"] == state["dummy"] and seat == state["declarer"]:
                effective_seat = state["dummy"]
            elif seat != state["turn"]:
                return []

            hand = state["hands"][str(effective_seat)]
            lead = state["lead_suit"]
            if lead:
                follows = [c for c in hand if suit_of(c) == lead]
                if follows:
                    return [{"action": "play", "card": c} for c in follows]
            return [{"action": "play", "card": c} for c in hand]
        return []

    @classmethod
    def apply(cls, state, seat, action):
        log = state["log"]
        act = action.get("action")

        if state["phase"] == "bidding":
            if act == "bid":
                lvl = action.get("level", 1)
                suit = action.get("suit", "NT")
                state["contract"] = f"{lvl}{suit}"
                state["declarer"] = seat
                state["trump_suit"] = None if suit == "NT" else suit
                state["contract_tricks"] = 6 + lvl
                state["bids"][str(seat)] = state["contract"]
                log.append(f"{SEAT_NAMES[seat]} bid contract: {state['contract']}")
            else:
                state["bids"][str(seat)] = "pass"
                log.append(f"{SEAT_NAMES[seat]} passed.")

            # End bidding if 4 bids evaluated and someone bid
            if len(state["bids"]) >= 4:
                if not state["contract"]:
                    state["contract"] = "1NT"
                    state["declarer"] = 0
                    state["contract_tricks"] = 7
                    state["trump_suit"] = None
                
                dec = state["declarer"]
                state["dummy"] = (dec + 2) % 4
                state["phase"] = "playing"
                state["turn"] = (dec + 1) % 4  # Opening lead is to declarer's left
                log.append(f"Contract SET: {state['contract']} by {SEAT_NAMES[dec]}. Opening lead by {SEAT_NAMES[state['turn']]}. Dummy is {SEAT_NAMES[state['dummy']]}.")
            else:
                state["bid_turn"] = (state["bid_turn"] + 1) % 4
            return state

        elif state["phase"] == "playing":
            active_seat = state["turn"]
            card = action.get("card")
            hand = state["hands"][str(active_seat)]
            hand.remove(card)

            # Dummy revealed after opening lead
            if not state["dummy_revealed"] and len(state["trick"]) >= 0:
                state["dummy_revealed"] = True
                log.append(f"Opening lead made: Dummy ({SEAT_NAMES[state['dummy']]}) cards laid face-up!")

            if not state["trick"]:
                state["lead_suit"] = suit_of(card)
            state["trick"].append({"seat": active_seat, "card": card})
            log.append(f"{SEAT_NAMES[active_seat]} played {pretty_card(card)}")

            if len(state["trick"]) == 4:
                lead = state["lead_suit"]
                trump = state["trump_suit"]

                def eval_b(e):
                    c = e["card"]
                    s, r = suit_of(c), rank_of(c)
                    mult = 2 if s == trump else (1 if s == lead else 0)
                    return (mult, STANDARD_VALUES[r])

                win_e = max(state["trick"], key=eval_b)
                winner = win_e["seat"]
                team = "team0" if winner in (0, 2) else "team1"

                state["tricks"][str(winner)] += 1
                state["team_tricks"][team] += 1
                log.append(f"{SEAT_NAMES[winner]} won the trick (Team {team[-1]} tricks: {state['team_tricks'][team]})")

                state["trick"] = []
                state["lead_suit"] = None
                state["turn"] = winner

                if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                    state["over"] = True
                    state["phase"] = "round_over"
                    dec_team = "team0" if state["declarer"] in (0, 2) else "team1"
                    target = state["contract_tricks"]
                    won = state["team_tricks"][dec_team]
                    if won >= target:
                        state["winner_team"] = dec_team
                        log.append(f"CONTRACT MADE! Declarer Team {dec_team.upper()} took {won} tricks (target: {target}).")
                    else:
                        state["winner_team"] = "team1" if dec_team == "team0" else "team0"
                        log.append(f"CONTRACT DEFEATED! Defending Team defeated contract by {target - won} trick(s).")
            else:
                state["turn"] = (active_seat + 1) % 4
            return state

        return state


# =====================================================================
# 5. WHIST (CLASSIC ENGLISH WHIST)
# =====================================================================
class WhistGame:
    """
    Classic English Whist: 52 cards, 4 players in 2 partnerships (0 & 2 vs 1 & 3).
    Last card dealt sets trump. 13 tricks.
    Odd-tricks scoring: tricks won over 6 count 1 pt each.
    """
    slug = "whist"
    title = "Whist"
    description = "The foundational 18th-century English 4-player trick-taking game. Trump is set by the cut dealer card; partnerships compete for odd tricks."

    @classmethod
    def create(cls, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)

        trump_card = deck[-1]
        trump_suit = trump_card[0]

        hands = {str(i): sorted([deck.pop() for _ in range(13)], key=lambda c: (c[0], STANDARD_VALUES[c[1:]])) for i in range(4)}

        state = {
            "slug": cls.slug,
            "phase": "playing",
            "hands": hands,
            "trump_card": trump_card,
            "trump_suit": trump_suit,
            "trick": [],
            "lead_suit": None,
            "turn": 0,
            "tricks": {str(i): 0 for i in range(4)},
            "team_tricks": {"team0": 0, "team1": 0},
            "scores": {"team0": 0, "team1": 0},
            "log": [f"Whist started: Trump turned up as {pretty_card(trump_card)} ({SUIT_NAMES[trump_suit]}). South leads first trick."],
            "over": False,
            "winner_team": None
        }
        return state

    @classmethod
    def legal_actions(cls, state, seat):
        if state["over"] or seat != state["turn"]:
            return []
        hand = state["hands"][str(seat)]
        lead = state["lead_suit"]
        if lead:
            follows = [c for c in hand if suit_of(c) == lead]
            if follows:
                return [{"action": "play", "card": c} for c in follows]
        return [{"action": "play", "card": c} for c in hand]

    @classmethod
    def apply(cls, state, seat, action):
        card = action.get("card")
        hand = state["hands"][str(seat)]
        hand.remove(card)
        log = state["log"]

        if not state["trick"]:
            state["lead_suit"] = suit_of(card)
        state["trick"].append({"seat": seat, "card": card})
        log.append(f"{SEAT_NAMES[seat]} played {pretty_card(card)}")

        if len(state["trick"]) == 4:
            lead = state["lead_suit"]
            trump = state["trump_suit"]

            def val_w(e):
                c = e["card"]
                s, r = suit_of(c), rank_of(c)
                mult = 2 if s == trump else (1 if s == lead else 0)
                return (mult, STANDARD_VALUES[r])

            winner_e = max(state["trick"], key=val_w)
            winner = winner_e["seat"]
            team = "team0" if winner in (0, 2) else "team1"

            state["tricks"][str(winner)] += 1
            state["team_tricks"][team] += 1
            log.append(f"{SEAT_NAMES[winner]} won trick (Team {team[-1]} tricks: {state['team_tricks'][team]})")

            state["trick"] = []
            state["lead_suit"] = None
            state["turn"] = winner

            if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                state["over"] = True
                state["phase"] = "round_over"
                for t in ["team0", "team1"]:
                    state["scores"][t] = max(0, state["team_tricks"][t] - 6)
                state["winner_team"] = "team0" if state["scores"]["team0"] >= state["scores"]["team1"] else "team1"
                log.append(f"WHIST MATCH OVER! Team 0: {state['scores']['team0']} pts ({state['team_tricks']['team0']} tricks), Team 1: {state['scores']['team1']} pts ({state['team_tricks']['team1']} tricks).")
        else:
            state["turn"] = (seat + 1) % 4
        return state


# =====================================================================
# 6. OH HELL! (EXACT TRICK PREDICTION)
# =====================================================================
class OhHellGame:
    """
    Oh Hell!: 4 players. Bidding exact tricks expected to win.
    Deal: 10 cards to each player. Trump card turned up.
    Scoring: Exact bid made = 10 + bid pts; missed bid = 0 pts.
    """
    slug = "oh_hell"
    title = "Oh Hell!"
    description = "Dynamic trick-taking prediction game where players must win the EXACT number of tricks they bid to score bonus points."

    @classmethod
    def create(cls, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)

        hands = {str(i): sorted([deck.pop() for _ in range(10)], key=lambda c: (c[0], STANDARD_VALUES[c[1:]])) for i in range(4)}
        trump_card = deck.pop()
        trump_suit = trump_card[0]

        state = {
            "slug": cls.slug,
            "phase": "bidding",
            "hands": hands,
            "bids": {},
            "bid_turn": 0,
            "trump_card": trump_card,
            "trump_suit": trump_suit,
            "tricks": {str(i): 0 for i in range(4)},
            "scores": {str(i): 0 for i in range(4)},
            "trick": [],
            "lead_suit": None,
            "turn": 0,
            "log": [f"Oh Hell! started: 10 cards dealt. Trump is {pretty_card(trump_card)} ({SUIT_NAMES[trump_suit]}). Bidding exact tricks (0 to 10)."],
            "over": False,
            "winner": None
        }
        return state

    @classmethod
    def legal_actions(cls, state, seat):
        if state["over"]:
            return []
        if state["phase"] == "bidding":
            if seat != state["bid_turn"]:
                return []
            return [{"action": "bid", "value": b} for b in range(0, 11)]
        elif state["phase"] == "playing":
            if seat != state["turn"]:
                return []
            hand = state["hands"][str(seat)]
            lead = state["lead_suit"]
            if lead:
                follows = [c for c in hand if suit_of(c) == lead]
                if follows:
                    return [{"action": "play", "card": c} for c in follows]
            return [{"action": "play", "card": c} for c in hand]
        return []

    @classmethod
    def apply(cls, state, seat, action):
        log = state["log"]
        if state["phase"] == "bidding":
            val = int(action.get("value", 2))
            state["bids"][str(seat)] = val
            log.append(f"{SEAT_NAMES[seat]} bid exactly {val} tricks.")

            if len(state["bids"]) == 4:
                state["phase"] = "playing"
                state["turn"] = 0
                log.append("All bids locked! 10-trick play begins.")
            else:
                state["bid_turn"] = (state["bid_turn"] + 1) % 4
            return state

        elif state["phase"] == "playing":
            card = action.get("card")
            hand = state["hands"][str(seat)]
            hand.remove(card)

            if not state["trick"]:
                state["lead_suit"] = suit_of(card)
            state["trick"].append({"seat": seat, "card": card})
            log.append(f"{SEAT_NAMES[seat]} played {pretty_card(card)}")

            if len(state["trick"]) == 4:
                lead = state["lead_suit"]
                trump = state["trump_suit"]

                def val_oh(e):
                    c = e["card"]
                    s, r = suit_of(c), rank_of(c)
                    mult = 2 if s == trump else (1 if s == lead else 0)
                    return (mult, STANDARD_VALUES[r])

                winner_e = max(state["trick"], key=val_oh)
                winner = winner_e["seat"]

                state["tricks"][str(winner)] += 1
                log.append(f"{SEAT_NAMES[winner]} won the trick (took: {state['tricks'][str(winner)]} / target: {state['bids'][str(winner)]})")

                state["trick"] = []
                state["lead_suit"] = None
                state["turn"] = winner

                if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                    state["over"] = True
                    state["phase"] = "round_over"
                    for i in range(4):
                        bid = state["bids"][str(i)]
                        won = state["tricks"][str(i)]
                        if bid == won:
                            state["scores"][str(i)] = 10 + won
                        else:
                            state["scores"][str(i)] = 0
                    best_seat = max(range(4), key=lambda i: state["scores"][str(i)])
                    state["winner"] = best_seat
                    log.append(f"ROUND FINISHED! Winner is {SEAT_NAMES[best_seat]} with {state['scores'][str(best_seat)]} pts!")
            else:
                state["turn"] = (seat + 1) % 4
            return state
        return state


# =====================================================================
# 7. EUCHRE (24-CARD FAST-PACED CLASSIC)
# =====================================================================
class EuchreGame:
    """
    Euchre: 24 cards (9, 10, J, Q, K, A in each suit).
    4 players in 2 partnerships (0 & 2 vs 1 & 3).
    Bowers:
      Right Bower = Jack of trump suit (Highest card)
      Left Bower = Jack of same-color suit (2nd highest card, acts as trump!)
    5 tricks per hand. Makers need 3 tricks to score. 5 tricks = March (2 pts).
    Defenders take 3+ tricks = Euchre (2 pts).
    """
    slug = "euchre"
    title = "Euchre"
    description = "Fast-paced 24-card game with Right & Left Bowers, partnership bidding, and exciting March or Euchre payoffs."

    EUCHRE_RANKS = ["9", "T", "J", "Q", "K", "A"]
    SAME_COLOR = {"S": "C", "C": "S", "H": "D", "D": "H"}

    @classmethod
    def create(cls, seed=None):
        rng = random.Random(seed)
        deck = [s + r for s in SUITS for r in cls.EUCHRE_RANKS]
        rng.shuffle(deck)

        hands = {str(i): sorted([deck.pop() for _ in range(5)], key=lambda c: (c[0], STANDARD_VALUES[c[1:]])) for i in range(4)}
        up_card = deck.pop()

        state = {
            "slug": cls.slug,
            "phase": "bidding",
            "hands": hands,
            "up_card": up_card,
            "bids": {},
            "bid_turn": 0,
            "trump_suit": None,
            "maker_seat": None,
            "tricks": {str(i): 0 for i in range(4)},
            "team_tricks": {"team0": 0, "team1": 0},
            "scores": {"team0": 0, "team1": 0},
            "trick": [],
            "lead_suit": None,
            "turn": 0,
            "log": [f"Euchre dealt: 5 cards each. Turn-up card is {pretty_card(up_card)} ({SUIT_NAMES[up_card[0]]}). Order up or pass."],
            "over": False,
            "winner_team": None
        }
        return state

    @classmethod
    def get_card_suit(cls, card, trump_suit):
        # Left Bower belongs to the trump suit!
        if trump_suit and card[1:] == "J" and card[0] == cls.SAME_COLOR.get(trump_suit):
            return trump_suit
        return card[0]

    @classmethod
    def get_euchre_strength(cls, card, trump_suit, lead_suit):
        s, r = card[0], card[1:]
        effective_suit = cls.get_card_suit(card, trump_suit)
        
        # Right Bower
        if trump_suit and s == trump_suit and r == "J":
            return (3, 100)
        # Left Bower
        if trump_suit and s == cls.SAME_COLOR.get(trump_suit) and r == "J":
            return (3, 99)
        # Regular trump
        if trump_suit and effective_suit == trump_suit:
            return (2, STANDARD_VALUES[r])
        # Led suit
        if lead_suit and effective_suit == lead_suit:
            return (1, STANDARD_VALUES[r])
        return (0, STANDARD_VALUES[r])

    @classmethod
    def legal_actions(cls, state, seat):
        if state["over"]:
            return []
        if state["phase"] == "bidding":
            if seat != state["bid_turn"]:
                return []
            actions = [{"action": "pass"}]
            # Order up the turn-up suit, or name any suit
            actions.append({"action": "order_up", "suit": state["up_card"][0]})
            for s in SUITS:
                if s != state["up_card"][0]:
                    actions.append({"action": "make_trump", "suit": s})
            return actions

        elif state["phase"] == "playing":
            if seat != state["turn"]:
                return []
            hand = state["hands"][str(seat)]
            trump = state["trump_suit"]
            lead = state["lead_suit"]

            if lead:
                follows = [c for c in hand if cls.get_card_suit(c, trump) == lead]
                if follows:
                    return [{"action": "play", "card": c} for c in follows]
            return [{"action": "play", "card": c} for c in hand]
        return []

    @classmethod
    def apply(cls, state, seat, action):
        log = state["log"]
        act = action.get("action")

        if state["phase"] == "bidding":
            if act in ("order_up", "make_trump"):
                suit = action.get("suit") or state["up_card"][0]
                state["trump_suit"] = suit
                state["maker_seat"] = seat
                state["phase"] = "playing"
                state["turn"] = 0
                log.append(f"{SEAT_NAMES[seat]} named TRUMP as {SUIT_NAMES[suit]} ({SUIT_SYMBOLS[suit]})! 5-trick showdown begins.")
            else:
                state["bids"][str(seat)] = "pass"
                log.append(f"{SEAT_NAMES[seat]} passed.")
                if len(state["bids"]) >= 4:
                    # Default: Maker is South with up-card suit
                    state["trump_suit"] = state["up_card"][0]
                    state["maker_seat"] = 0
                    state["phase"] = "playing"
                    state["turn"] = 0
                    log.append(f"Everyone passed. {SEAT_NAMES[0]} orders up {SUIT_NAMES[state['trump_suit']]}!")
                else:
                    state["bid_turn"] = (state["bid_turn"] + 1) % 4
            return state

        elif state["phase"] == "playing":
            card = action.get("card")
            hand = state["hands"][str(seat)]
            hand.remove(card)

            trump = state["trump_suit"]
            eff_suit = cls.get_card_suit(card, trump)
            if not state["trick"]:
                state["lead_suit"] = eff_suit

            state["trick"].append({"seat": seat, "card": card})
            log.append(f"{SEAT_NAMES[seat]} played {pretty_card(card)}")

            if len(state["trick"]) == 4:
                lead = state["lead_suit"]
                winner_e = max(state["trick"], key=lambda e: cls.get_euchre_strength(e["card"], trump, lead))
                winner = winner_e["seat"]
                team = "team0" if winner in (0, 2) else "team1"

                state["tricks"][str(winner)] += 1
                state["team_tricks"][team] += 1
                log.append(f"{SEAT_NAMES[winner]} won trick (Team {team[-1]} tricks: {state['team_tricks'][team]})")

                state["trick"] = []
                state["lead_suit"] = None
                state["turn"] = winner

                if all(len(state["hands"][str(i)]) == 0 for i in range(4)):
                    state["over"] = True
                    state["phase"] = "round_over"
                    maker_team = "team0" if state["maker_seat"] in (0, 2) else "team1"
                    maker_tricks = state["team_tricks"][maker_team]

                    if maker_tricks >= 5:
                        state["scores"][maker_team] = 2
                        state["winner_team"] = maker_team
                        log.append(f"MARCH! Maker Team {maker_team.upper()} took ALL 5 tricks! (+2 pts)")
                    elif maker_tricks >= 3:
                        state["scores"][maker_team] = 1
                        state["winner_team"] = maker_team
                        log.append(f"POINT! Maker Team {maker_team.upper()} made 3+ tricks. (+1 pt)")
                    else:
                        def_team = "team1" if maker_team == "team0" else "team0"
                        state["scores"][def_team] = 2
                        state["winner_team"] = def_team
                        log.append(f"EUCHRED! Defenders {def_team.upper()} stopped makers and took 3+ tricks! (+2 pts)")
            else:
                state["turn"] = (seat + 1) % 4
            return state

        return state


# =====================================================================
# MASTER CATALOG & DISPATCHER WITH SMART AI BOT CONTROLLER
# =====================================================================
GAME_ENGINES = {
    "29": TwentyNineGame,
    "bridge": BridgeGame,
    "spades": SpadesGame,
    "hearts": HeartsGame,
    "whist": WhistGame,
    "oh_hell": OhHellGame,
    "euchre": EuchreGame
}

CLASSIC_CATALOG = [
    {"slug": "29", "name": "29 Card Game", "deck_size": 32, "desc": "South Asian classic with Jack=3, 9=2, A=1, 10=1, 28/29 points bidding."},
    {"slug": "bridge", "name": "Contract Bridge", "deck_size": 52, "desc": "Premier 4-player partnership strategy with bidding and dummy play."},
    {"slug": "spades", "name": "Spades", "deck_size": 52, "desc": "Partnership trick-taking game. Spades are permanent trump."},
    {"slug": "hearts", "name": "Hearts", "deck_size": 52, "desc": "Trick-avoidance classic: dodge penalty Hearts and the Queen of Spades."},
    {"slug": "whist", "name": "Whist", "deck_size": 52, "desc": "18th-century English classic: cut trump card and partnership odd tricks."},
    {"slug": "oh_hell", "name": "Oh Hell!", "deck_size": 52, "desc": "Exact-prediction trick bidding game where accurate bidding wins."},
    {"slug": "euchre", "name": "Euchre", "deck_size": 24, "desc": "Fast 24-card game with Right & Left Bowers, march, and euchre."}
]


def create_classic_game(slug, seed=None):
    engine = GAME_ENGINES.get(slug, TwentyNineGame)
    return engine.create(seed=seed)


def get_game_view(state, seat=0):
    """
    Returns public/private view for the human player (seat 0):
    - Hand of seat 0 is fully visible with cards and rank/suit metadata.
    - Hands of seats 1, 2, 3 show card counts (and dummy hand if revealed in Bridge).
    - Current trick, lead suit, trump suit, bids, tricks won, scores, phase, logs, legal actions.
    """
    slug = state.get("slug", "29")
    engine = GAME_ENGINES.get(slug, TwentyNineGame)

    human_hand = state["hands"].get(str(seat), [])
    
    # Hand counts for other seats
    counts = {str(i): len(state["hands"].get(str(i), [])) for i in range(4)}
    
    # Dummy hand if revealed in Bridge
    dummy_hand = None
    if slug == "bridge" and state.get("dummy_revealed") and state.get("dummy") is not None:
        dummy_hand = state["hands"].get(str(state["dummy"]), [])

    legal_acts = engine.legal_actions(state, seat)

    return {
        "slug": slug,
        "title": getattr(engine, "title", slug),
        "description": getattr(engine, "description", ""),
        "phase": state.get("phase"),
        "over": state.get("over", False),
        "winner": state.get("winner"),
        "winner_team": state.get("winner_team"),
        "turn": state.get("turn"),
        "bid_turn": state.get("bid_turn"),
        "seat": seat,
        "seat_name": SEAT_NAMES[seat],
        "hand": human_hand,
        "counts": counts,
        "dummy_hand": dummy_hand,
        "dummy_seat": state.get("dummy"),
        "trick": state.get("trick", []),
        "lead_suit": state.get("lead_suit"),
        "trump_suit": state.get("trump_suit"),
        "trump_card": state.get("trump_card"),
        "trump_revealed": state.get("trump_revealed"),
        "spades_broken": state.get("spades_broken"),
        "hearts_broken": state.get("hearts_broken"),
        "high_bid": state.get("high_bid"),
        "high_bidder": state.get("high_bidder"),
        "contract": state.get("contract"),
        "declarer": state.get("declarer"),
        "bids": state.get("bids", {}),
        "tricks": state.get("tricks", {}),
        "team_tricks": state.get("team_tricks", {}),
        "team_bids": state.get("team_bids", {}),
        "card_points": state.get("card_points", {}),
        "penalty_points": state.get("penalty_points", {}),
        "scores": state.get("scores", {}),
        "log": state.get("log", [])[-20:],
        "legal_actions": legal_acts
    }


def step_ai_until_human(state):
    """
    Executes automated AI bot moves for seats 1, 2, and 3
    until it is either seat 0's turn (human) or the round/game ends.
    """
    slug = state.get("slug", "29")
    engine = GAME_ENGINES.get(slug, TwentyNineGame)

    max_steps = 60
    steps = 0

    while not state.get("over") and steps < max_steps:
        phase = state.get("phase")
        cur_seat = state.get("bid_turn") if phase == "bidding" else state.get("turn")

        # If it's the human's turn (seat 0), stop and wait for human input
        if cur_seat == 0:
            # In Bridge, if human is declarer and it's dummy's turn, human plays dummy
            if slug == "bridge" and state.get("dummy") == cur_seat and state.get("declarer") == 0:
                break
            break

        legal = engine.legal_actions(state, cur_seat)
        if not legal:
            break

        # AI chooses an action
        chosen_action = choose_ai_action(slug, state, cur_seat, legal)
        engine.apply(state, cur_seat, chosen_action)
        steps += 1

    return state


def choose_ai_action(slug, state, seat, legal_actions):
    """Smart heuristic bot selection for bidding and card playing."""
    if not legal_actions:
        return None

    phase = state.get("phase")
    
    # Bidding Heuristics
    if phase == "bidding":
        if slug == "29":
            # Hand evaluation for 29
            hand = state["hands"].get(str(seat), [])
            high = state.get("high_bid", 15)
            # Count Jacks and 9s
            power = sum(1 for c in hand if c[1] in ("J", "9"))
            if power >= 2 and high < 18:
                bid_candidates = [a for a in legal_actions if a.get("action") == "bid" and a.get("value") == high + 1]
                if bid_candidates:
                    return bid_candidates[0]
            return {"action": "pass"}

        elif slug == "spades":
            # Estimate trick bid: 1 pt per Ace/King + high spades
            hand = state["hands"].get(str(seat), [])
            est = sum(1 for c in hand if c[1] in ("A", "K") or (c[0] == "S" and c[1] in ("Q", "J")))
            est = max(1, min(est, 4))
            for a in legal_actions:
                if a.get("action") == "bid" and a.get("value") == est:
                    return a
            return legal_actions[0]

        elif slug == "oh_hell":
            # 1 to 3 tricks estimate
            hand = state["hands"].get(str(seat), [])
            est = sum(1 for c in hand if c[1] in ("A", "K"))
            est = max(0, min(est, 3))
            for a in legal_actions:
                if a.get("action") == "bid" and a.get("value") == est:
                    return a
            return legal_actions[0]

        elif slug == "bridge":
            # AI prefers Pass or modest 1NT/1S if holding high cards
            hand = state["hands"].get(str(seat), [])
            hcp = sum(4 if c[1] == "A" else (3 if c[1] == "K" else (2 if c[1] == "Q" else (1 if c[1] == "J" else 0))) for c in hand)
            if hcp >= 12 and not state.get("contract"):
                bid_cand = [a for a in legal_actions if a.get("action") == "bid" and a.get("level") == 1]
                if bid_cand:
                    return bid_cand[0]
            return {"action": "pass"}

        elif slug == "euchre":
            # Order up if 3+ trumps
            up = state.get("up_card", "S9")[0]
            hand = state["hands"].get(str(seat), [])
            trump_count = sum(1 for c in hand if c[0] == up)
            if trump_count >= 3:
                cand = [a for a in legal_actions if a.get("action") == "order_up"]
                if cand:
                    return cand[0]
            return {"action": "pass"}

        return legal_actions[0]

    # Card Playing Heuristics
    play_actions = [a for a in legal_actions if a.get("action") == "play"]
    if not play_actions:
        return legal_actions[0]

    trick = state.get("trick", [])
    lead = state.get("lead_suit")

    # Hearts: avoid taking tricks that have penalty points
    if slug == "hearts":
        # Discard Queen of Spades or highest Hearts if void in led suit
        if lead and any(a["card"] == "SQ" for a in play_actions):
            return {"action": "play", "card": "SQ"}
        # Play lowest legal card
        return min(play_actions, key=lambda a: STANDARD_VALUES.get(a["card"][1:], 0))

    # Standard trick taking:
    # If partner (North) is winning, play low card to save strength
    partner_seat = (seat + 2) % 4
    if len(trick) >= 2 and trick[-1]["seat"] == partner_seat:
        # Play lowest card
        return min(play_actions, key=lambda a: STANDARD_VALUES.get(a["card"][1:], 0))

    # Try to win with highest or play lowest
    return max(play_actions, key=lambda a: STANDARD_VALUES.get(a["card"][1:], 0))
