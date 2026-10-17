"""
CubePermutation AI - Popular Global & Bangladeshi Card Game Engines
===================================================================
1. CallBreak (4 players) - South Asian strategic trick-taking, Spades permanent trump, bidding 1-13
2. Hazari (4 players) - 1000-point partition game: 13 cards divided into 3, 3, 3, 4 combinations
3. TwentyNine (4 players in partnerships) - 32-card classic, J=3, 9=2, A=1, 10=1, 28/29 target
4. TeenPatti (3-6 players) - 3-Card Brag / Indian Poker with Troy, Color Run, Run, Color, Pair
5. ContractBridge (4 players in partnerships) - Contract bidding, Declarer & Dummy open play
6. TexasHoldem (2-9 players) - Community card poker with Preflop, Flop, Turn, River betting rounds
7. Blackjack (2-7 players) - 21 comparing game vs dealer with Hit, Stand, Double Down, Blackjacks
8. CrazyEights (2-7 players) - Uno-style shedding with action cards (8 wild, 2 draw-two, Q skip/reverse)
"""

import random
from models.card_club.errors import IllegalMove, NotYourTurn
from models.card_club.engines.base import (
    BaseCardGame, full_deck, rank_val, suit_of, RANK_VALUE, VALUE_RANK
)
from models.card_club.engines.poker_hands import evaluate_best, describe

SUITS = ["S", "H", "D", "C"]
STANDARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]


# =====================================================================
# 1. CALL BREAK (4 Players)
# =====================================================================
class CallBreak(BaseCardGame):
    """Call Break (Nepal & Bangladesh): 4 players, 52 cards (13 each).
    Spades are permanent trump. Players bid 1-13.
    Rule: Must follow suit; MUST play higher card of led suit if holding one;
    must trump with spade if void; highest spade (or led suit) wins."""

    slug = "call_break"
    display_name = "Call Break"
    min_players, max_players = 4, 4
    rules = ("4 players, 13 cards each. Spades are permanent trump. "
             "Bid 1 to 13. You MUST follow suit and MUST beat the highest card "
             "in the trick if possible. If void, you MUST play a spade. "
             "Making your bid scores bid + 0.1 per overtrick; failing scores -bid.")

    @classmethod
    def create(cls, players, seed=None):
        if len(players) != 4:
            raise IllegalMove("Call Break requires exactly 4 players")
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {str(i): sorted([deck.pop() for _ in range(13)], key=lambda c: (c[0], rank_val(c))) for i in range(4)}
        return {
            "slug": cls.slug, "players": list(players),
            "hands": hands, "bids": {}, "tricks": {str(i): 0 for i in range(4)},
            "trick": [], "lead_suit": None, "turn": 0, "bid_turn": 0,
            "phase": "bidding", "scores": {str(i): 0.0 for i in range(4)},
            "finish": [], "log": ["Call Break deal complete. Bidding phase started."],
            "over": False
        }

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "phase": s["phase"], "bids": s["bids"], "tricks": s["tricks"],
            "trick": s["trick"], "lead_suit": s["lead_suit"], "trump": "S",
            "scores": s["scores"],
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "finish": s["finish"], "over": s["over"], "log": s["log"][-20:]
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"]:
            return []
        if s["phase"] == "bidding":
            if seat != s["bid_turn"]:
                return []
            return [{"action": "bid", "amount": b} for b in range(1, 14)]
        if s["phase"] == "playing":
            if seat != s["turn"]:
                return []
            hand = s["hands"][str(seat)]
            lead = s["lead_suit"]
            if not lead:
                return [{"action": "play", "card": c} for c in hand]

            follows = [c for c in hand if suit_of(c) == lead]
            if follows:
                # Must beat highest card in trick if possible
                highest_lead = max([rank_val(e["card"]) for e in s["trick"] if suit_of(e["card"]) == lead], default=0)
                beaters = [c for c in follows if rank_val(c) > highest_lead]
                if beaters:
                    return [{"action": "play", "card": c} for c in beaters]
                return [{"action": "play", "card": c} for c in follows]

            # Void in led suit: must play a spade if holding one
            spades = [c for c in hand if suit_of(c) == "S"]
            if spades:
                highest_spade = max([rank_val(e["card"]) for e in s["trick"] if suit_of(e["card"]) == "S"], default=0)
                better_spades = [c for c in spades if rank_val(c) > highest_spade]
                if better_spades:
                    return [{"action": "play", "card": c} for c in better_spades]
                return [{"action": "play", "card": c} for c in spades]

            return [{"action": "play", "card": c} for c in hand]
        return []

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        act = action.get("action")

        if s["phase"] == "bidding":
            if seat != s["bid_turn"]:
                raise NotYourTurn("Not your bidding turn")
            bid = int(action.get("amount", 2))
            s["bids"][str(seat)] = bid
            self._say(s, seat, f"bid {bid} tricks")
            if len(s["bids"]) == 4:
                s["phase"] = "playing"
                s["turn"] = 0
                self._say(s, None, "Bids confirmed. Trick play begins from Seat 0.")
            else:
                s["bid_turn"] = (s["bid_turn"] + 1) % 4
            return

        if s["phase"] == "playing":
            if seat != s["turn"]:
                raise NotYourTurn("Not your turn to play")
            card = action.get("card")
            hand = s["hands"][str(seat)]
            if card not in hand:
                raise IllegalMove("Card not in hand")

            legal = [a["card"] for a in self.legal_actions(seat)]
            if card not in legal:
                raise IllegalMove("Must follow suit / beat higher card")

            hand.remove(card)
            if not s["trick"]:
                s["lead_suit"] = suit_of(card)
            s["trick"].append({"seat": seat, "card": card})
            self._say(s, seat, f"played {card}")

            if len(s["trick"]) == 4:
                lead = s["lead_suit"]
                # Evaluate trick winner
                def trick_power(entry):
                    c = entry["card"]
                    return (2 if suit_of(c) == "S" else (1 if suit_of(c) == lead else 0), rank_val(c))
                winner = max(s["trick"], key=trick_power)["seat"]
                s["tricks"][str(winner)] += 1
                self._say(s, winner, f"won trick #{sum(s['tricks'].values())}")
                s["trick"] = []
                s["lead_suit"] = None
                s["turn"] = winner

                if all(len(s["hands"][str(i)]) == 0 for i in range(4)):
                    s["over"] = True
                    s["phase"] = "round_over"
                    # Calculate final round scores
                    for i in range(4):
                        b = s["bids"][str(i)]
                        t = s["tricks"][str(i)]
                        if t >= b:
                            s["scores"][str(i)] = round(b + (t - b) * 0.1, 1)
                        else:
                            s["scores"][str(i)] = -float(b)
                    ranked = sorted(range(4), key=lambda i: s["scores"][str(i)], reverse=True)
                    s["finish"] = ranked
                    self._say(s, None, f"Round ended. Winner: Seat {ranked[0]} with {s['scores'][str(ranked[0])]} pts.")
            else:
                s["turn"] = (seat + 1) % 4


# =====================================================================
# 2. HAZARI (1000-Point Partition Game)
# =====================================================================
class Hazari(BaseCardGame):
    """Hazari: 4 players, 52 cards (13 each).
    Each player arranges their 13 cards into 4 distinct groups:
    Group 1: 3 cards, Group 2: 3 cards, Group 3: 3 cards, Group 4: 4 cards.
    Rankings: Troy > Color Run > Run > Color > Pair > High Card.
    Winners of each group round collect the trick cards to score towards 1000 pts."""

    slug = "hazari"
    display_name = "Hazari"
    min_players, max_players = 4, 4
    rules = ("Arrange 13 cards into 3-3-3-4 partition groups. "
             "Combinations: Troy (3 of a kind) > Color Run (pure seq) > "
             "Run (straight) > Color (flush) > Pair > High Card. "
             "4 group showdowns are fought. Ace, King, Queen, Jack, 10 give 10 points each. "
             "First player to 1000 points wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {str(i): sorted([deck.pop() for _ in range(13)], key=lambda c: rank_val(c), reverse=True) for i in range(4)}
        return {
            "slug": cls.slug, "players": list(players),
            "hands": hands, "arranged": {}, "round_step": 0,
            "showdowns": [], "scores": {str(i): 0 for i in range(4)},
            "points_this_deal": {str(i): 0 for i in range(4)},
            "finish": [], "log": ["Hazari: 13 cards dealt. Players arrange into 3-3-3-4 partition."],
            "over": False
        }

    @staticmethod
    def evaluate_combo(cards):
        """Returns tuple (rank_tier, high_vals) for combo comparison:
        6 = Troy, 5 = Color Run, 4 = Run, 3 = Color, 2 = Pair, 1 = High."""
        vals = sorted([rank_val(c) for c in cards], reverse=True)
        suits = [suit_of(c) for c in cards]
        is_flush = len(set(suits)) == 1

        # Check Troy
        if len(set(vals[:3])) == 1:
            return (6, vals[0])

        # Check Straight (Run)
        is_straight = False
        if len(cards) >= 3:
            v0, v1, v2 = vals[0], vals[1], vals[2]
            if (v0 - v1 == 1 and v1 - v2 == 1) or (vals == [14, 3, 2]):
                is_straight = True

        if is_flush and is_straight:
            return (5, vals[0])
        if is_straight:
            return (4, vals[0])
        if is_flush:
            return (3, vals)
        if len(cards) >= 2 and (vals[0] == vals[1] or vals[1] == vals[2]):
            pair_v = vals[1]
            return (2, pair_v, vals)
        return (1, vals)

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "round_step": s["round_step"],
            "arranged_status": {str(k): bool(k in s["arranged"]) for k in range(4)},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "arranged": s["arranged"].get(str(seat)) if seat is not None else None,
            "showdowns": s["showdowns"], "scores": s["scores"],
            "finish": s["finish"], "over": s["over"], "log": s["log"][-20:]
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"]:
            return []
        if str(seat) not in s["arranged"]:
            # Action: arrange partition [[c1,c2,c3], [c4,c5,c6], [c7,c8,c9], [c10,c11,c12,c13]]
            return [{"action": "arrange", "note": "Provide 4 groups of 3, 3, 3, and 4 cards"}]
        return []

    def apply(self, seat, action):
        s = self.state
        if action.get("action") == "arrange":
            groups = action.get("groups")
            hand = s["hands"][str(seat)]
            # If auto-arranging or provided valid partition:
            if not groups or len(groups) != 4:
                # Default auto-partition: 3, 3, 3, 4 sorted by rank
                groups = [hand[0:3], hand[3:6], hand[6:9], hand[9:13]]
            s["arranged"][str(seat)] = groups
            self._say(s, seat, "partition arranged (3-3-3-4)")

            # When all 4 players arranged, execute the 4 showdown rounds
            if len(s["arranged"]) == 4:
                for round_idx in range(4):
                    round_plays = []
                    for p in range(4):
                        round_plays.append({"seat": p, "cards": s["arranged"][str(p)][round_idx]})
                    
                    winner = max(round_plays, key=lambda rp: self.evaluate_combo(rp["cards"]))["seat"]
                    # Calculate points: 10 pts per A, K, Q, J, 10
                    pts = 0
                    for rp in round_plays:
                        for c in rp["cards"]:
                            if c[1] in ("A", "K", "Q", "J", "T"):
                                pts += 10
                    s["scores"][str(winner)] += pts
                    s["showdowns"].append({"round": round_idx + 1, "winner": winner, "points": pts})
                    self._say(s, winner, f"won Hazari Group {round_idx + 1} (+{pts} pts)")

                s["over"] = True
                best = max(range(4), key=lambda i: s["scores"][str(i)])
                s["finish"] = sorted(range(4), key=lambda i: s["scores"][str(i)], reverse=True)
                self._say(s, None, f"Hazari deal over! Leader: Seat {best} with {s['scores'][str(best)]} points.")


# =====================================================================
# 3. TWENTY-NINE / 29 (4 Players in Partnerships)
# =====================================================================
class TwentyNine(BaseCardGame):
    """29 Card Game: 32 cards (J=3, 9=2, A=1, 10=1). Target 28+1=29.
    Partnerships: (0 & 2) vs (1 & 3). Bidding 16-28 sets secret trump."""

    slug = "29"
    display_name = "Twenty-Nine (29)"
    min_players, max_players = 4, 4
    rules = ("32 cards (7, 8, Q, K, 10, A, 9, J). Jack=3, 9=2, Ace=1, 10=1. "
             "Partnerships: Team 0 (0 & 2) vs Team 1 (1 & 3). "
             "Bids from 16 to 28. Winner sets secret trump. 8 tricks to reach contract.")

    RANKS = ["7", "8", "Q", "K", "T", "A", "9", "J"]
    RANK_STRENGTH = {"7": 1, "8": 2, "Q": 3, "K": 4, "T": 5, "A": 6, "9": 7, "J": 8}
    CARD_POINTS = {"J": 3, "9": 2, "A": 1, "T": 1, "K": 0, "Q": 0, "8": 0, "7": 0}

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        deck = [s + r for s in SUITS for r in cls.RANKS]
        rng.shuffle(deck)
        hands = {str(i): [deck.pop() for _ in range(4)] for i in range(4)}
        second_half = {str(i): [deck.pop() for _ in range(4)] for i in range(4)}
        return {
            "slug": cls.slug, "players": list(players), "phase": "bidding",
            "hands": hands, "second_half": second_half, "bids": {},
            "bid_turn": 0, "high_bid": 15, "high_bidder": None,
            "trump_suit": None, "trump_revealed": False,
            "tricks": {str(i): 0 for i in range(4)},
            "card_points": {"team0": 0, "team1": 0}, "trick": [],
            "lead_suit": None, "turn": 0, "finish": [],
            "log": ["29 Card Game dealt. Bidding open from 16 to 28."], "over": False
        }

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "phase": s["phase"],
            "turn": s["turn"], "bid_turn": s["bid_turn"], "high_bid": s["high_bid"],
            "high_bidder": s["high_bidder"], "trump_revealed": s["trump_revealed"],
            "trump_suit": s["trump_suit"] if s["trump_revealed"] else None,
            "trick": s["trick"], "lead_suit": s["lead_suit"],
            "tricks": s["tricks"], "card_points": s["card_points"],
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "finish": s["finish"], "over": s["over"], "log": s["log"][-20:]
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"]:
            return []
        if s["phase"] == "bidding":
            if seat != s["bid_turn"]:
                return []
            high = s["high_bid"]
            actions = [{"action": "pass"}]
            for b in range(max(16, high + 1), 29):
                actions.append({"action": "bid", "value": b})
            return actions

        if s["phase"] == "playing":
            if seat != s["turn"]:
                return []
            hand = s["hands"][str(seat)]
            lead = s["lead_suit"]
            if lead:
                follows = [c for c in hand if suit_of(c) == lead]
                if follows:
                    return [{"action": "play", "card": c} for c in follows]
                if not s["trump_revealed"]:
                    return [{"action": "reveal_trump"}] + [{"action": "play", "card": c} for c in hand]
            return [{"action": "play", "card": c} for c in hand]
        return []

    def apply(self, seat, action):
        s = self.state
        act = action.get("action")

        if s["phase"] == "bidding":
            if act == "bid":
                val = int(action.get("value"))
                s["high_bid"] = val
                s["high_bidder"] = seat
                s["bids"][str(seat)] = val
                self._say(s, seat, f"bid {val}")
            else:
                s["bids"][str(seat)] = "pass"
                self._say(s, seat, "passed")

            if len(s["bids"]) >= 4 or (len([v for v in s["bids"].values() if v != "pass"]) <= 1 and s["high_bidder"] is not None):
                bidder = s["high_bidder"] or 0
                s["high_bidder"] = bidder
                s["high_bid"] = max(16, s["high_bid"])
                suits = [suit_of(c) for c in s["hands"][str(bidder)]]
                s["trump_suit"] = action.get("trump") or max(set(suits), key=suits.count)
                s["phase"] = "playing"
                s["turn"] = bidder
                for i in range(4):
                    s["hands"][str(i)].extend(s["second_half"][str(i)])
                s["second_half"] = {}
                self._say(s, bidder, f"won bidding at {s['high_bid']}! Trump set. Play begins.")
            else:
                s["bid_turn"] = (s["bid_turn"] + 1) % 4
            return

        if s["phase"] == "playing":
            if act == "reveal_trump":
                s["trump_revealed"] = True
                self._say(s, seat, f"revealed trump: {s['trump_suit']}")
                return

            card = action.get("card")
            s["hands"][str(seat)].remove(card)
            if not s["trick"]:
                s["lead_suit"] = suit_of(card)
            s["trick"].append({"seat": seat, "card": card})
            self._say(s, seat, f"played {card}")

            if len(s["trick"]) == 4:
                lead = s["lead_suit"]
                trump = s["trump_suit"] if s["trump_revealed"] else None

                def power_29(e):
                    c = e["card"]
                    return (2 if suit_of(c) == trump else (1 if suit_of(c) == lead else 0),
                            self.RANK_STRENGTH[c[1:]])

                winner = max(s["trick"], key=power_29)["seat"]
                team = "team0" if winner in (0, 2) else "team1"
                pts = sum(self.CARD_POINTS[e["card"][1:]] for e in s["trick"])
                if all(len(s["hands"][str(i)]) == 0 for i in range(4)):
                    pts += 1  # 8th trick +1 pt

                s["tricks"][str(winner)] += 1
                s["card_points"][team] += pts
                self._say(s, winner, f"won trick (+{pts} pts)")
                s["trick"] = []
                s["lead_suit"] = None
                s["turn"] = winner

                if all(len(s["hands"][str(i)]) == 0 for i in range(4)):
                    s["over"] = True
                    b_team = "team0" if s["high_bidder"] in (0, 2) else "team1"
                    if s["card_points"][b_team] >= s["high_bid"]:
                        s["finish"] = [0, 2, 1, 3] if b_team == "team0" else [1, 3, 0, 2]
                    else:
                        s["finish"] = [1, 3, 0, 2] if b_team == "team0" else [0, 2, 1, 3]
                    self._say(s, None, f"Game ended. Team {b_team} card points: {s['card_points'][b_team]}/{s['high_bid']}")
            else:
                s["turn"] = (seat + 1) % 4


# =====================================================================
# 4. TEEN PATTI / 3-CARD BRAG (3-6 Players)
# =====================================================================
class TeenPatti(BaseCardGame):
    """Teen Patti / 3-Card Brag: 3-6 players. 3 cards each.
    Troy > Color Run > Run > Color > Pair > High Card.
    Blind & Seen betting rounds, folding, showdown."""

    slug = "teen_patti"
    display_name = "Teen Patti (3-Card Brag)"
    min_players, max_players = 3, 6
    rules = ("3 cards dealt. Hand rankings: Trail/Troy (3 of a kind) > "
             "Pure Sequence (Color Run) > Sequence (Run) > Color (Flush) > "
             "Pair > High Card. Bet Blind or Seen. Pack to fold. Last player or showdown wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {str(i): [deck.pop() for _ in range(3)] for i in range(n)}
        return {
            "slug": cls.slug, "players": list(players), "hands": hands,
            "pot": n * 10, "current_bet": 10, "turn": 0,
            "seen": {str(i): False for i in range(n)},
            "folded": [], "finish": [], "log": ["Teen Patti started: 3 cards dealt. Boot collected."],
            "over": False
        }

    @staticmethod
    def eval_3card(cards):
        vals = sorted([rank_val(c) for c in cards], reverse=True)
        suits = [suit_of(c) for c in cards]
        is_flush = len(set(suits)) == 1
        is_seq = (vals[0] - vals[1] == 1 and vals[1] - vals[2] == 1) or (vals == [14, 3, 2])

        if len(set(vals)) == 1:
            return (6, vals[0])
        if is_flush and is_seq:
            return (5, vals[0])
        if is_seq:
            return (4, vals[0])
        if is_flush:
            return (3, vals)
        if vals[0] == vals[1] or vals[1] == vals[2]:
            pair_v = vals[1]
            return (2, pair_v, vals)
        return (1, vals)

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "pot": s["pot"], "current_bet": s["current_bet"],
            "seen": s["seen"].get(str(seat), False),
            "folded": s["folded"], "finish": s["finish"],
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None and s["seen"].get(str(seat)) else None,
            "over": s["over"], "log": s["log"][-20:]
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or seat != s["turn"] or seat in s["folded"]:
            return []
        acts = [{"action": "see_cards"}] if not s["seen"].get(str(seat)) else []
        acts.append({"action": "chaal", "amount": s["current_bet"]})
        acts.append({"action": "raise", "amount": s["current_bet"] * 2})
        acts.append({"action": "pack"})
        active = [i for i in range(len(s["players"])) if i not in s["folded"]]
        if len(active) == 2:
            acts.append({"action": "show"})
        return acts

    def apply(self, seat, action):
        s = self.state
        act = action.get("action")
        active = [i for i in range(len(s["players"])) if i not in s["folded"]]

        if act == "see_cards":
            s["seen"][str(seat)] = True
            self._say(s, seat, "looked at their cards (SEEN)")
            return

        if act == "pack":
            s["folded"].append(seat)
            self._say(s, seat, "folded (PACK)")
            rem = [i for i in range(len(s["players"])) if i not in s["folded"]]
            if len(rem) == 1:
                s["over"] = True
                s["finish"] = [rem[0]] + list(s["folded"])
                self._say(s, rem[0], f"won the pot of {s['pot']} by default!")
                return
        elif act in ("chaal", "raise"):
            amt = int(action.get("amount", s["current_bet"]))
            s["pot"] += amt
            if act == "raise":
                s["current_bet"] = amt
            self._say(s, seat, f"{act} {amt} (pot: {s['pot']})")
        elif act == "show":
            s["pot"] += s["current_bet"]
            winner = max(active, key=lambda p: self.eval_3card(s["hands"][str(p)]))
            s["over"] = True
            s["finish"] = [winner] + [p for p in active if p != winner] + list(s["folded"])
            self._say(s, winner, f"won showdown with best hand! Pot: {s['pot']}")
            return

        # Betting round cap: force a showdown so a table can never stall
        # in an endless call/raise loop (auto-play and idle tables).
        s["actions"] = s.get("actions", 0) + 1
        if s["actions"] >= len(s["players"]) * 15:
            winner = max(active, key=lambda p: self.eval_3card(s["hands"][str(p)]))
            s["over"] = True
            s["finish"] = [winner] + [p for p in active if p != winner] + list(s["folded"])
            self._say(s, winner, f"round limit reached - showdown won with best hand! Pot: {s['pot']}")
            return

        # Advance turn to next active player
        n = len(s["players"])
        nxt = (seat + 1) % n
        while nxt in s["folded"]:
            nxt = (nxt + 1) % n
        s["turn"] = nxt


# =====================================================================
# 5. CONTRACT BRIDGE (4 Players in Partnerships)
# =====================================================================
class ContractBridge(BaseCardGame):
    """Contract Bridge: 4 players, partnerships (0&2 vs 1&3).
    Bidding 1C-7NT sets declarer & trump. Dummy opens face-up."""

    slug = "bridge"
    display_name = "Contract Bridge"
    min_players, max_players = 4, 4
    rules = ("Partnerships: N-S vs E-W. 13 cards each. "
             "Bidding 1C to 7NT sets Contract & Declarer. "
             "Dummy's cards are opened face-up after opening lead. "
             "Declarer plays both hands. 6 + level tricks needed.")

    SUIT_ORDER = ["C", "D", "H", "S", "NT"]

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {str(i): sorted([deck.pop() for _ in range(13)], key=lambda c: (c[0], rank_val(c))) for i in range(4)}
        return {
            "slug": cls.slug, "players": list(players), "phase": "bidding",
            "hands": hands, "bids": {}, "bid_turn": 0, "contract": None,
            "declarer": None, "dummy": None, "dummy_revealed": False,
            "trump_suit": None, "contract_tricks": 0, "trick": [],
            "lead_suit": None, "tricks": {str(i): 0 for i in range(4)},
            "team_tricks": {"team0": 0, "team1": 0}, "turn": 0, "finish": [],
            "log": ["Bridge Match begun: 52 cards dealt. Bidding open."], "over": False
        }

    def view(self, seat):
        s = self.state
        dummy_h = list(s["hands"][str(s["dummy"])]) if s.get("dummy_revealed") and s.get("dummy") is not None else None
        return {
            "slug": s["slug"], "players": s["players"], "phase": s["phase"],
            "turn": s["turn"], "contract": s["contract"], "declarer": s["declarer"],
            "dummy": s["dummy"], "dummy_hand": dummy_h,
            "trick": s["trick"], "lead_suit": s["lead_suit"],
            "team_tricks": s["team_tricks"],
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "finish": s["finish"], "over": s["over"], "log": s["log"][-20:]
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"]:
            return []
        if s["phase"] == "bidding":
            if seat != s["bid_turn"]:
                return []
            acts = [{"action": "pass"}]
            for lvl in range(1, 5):
                for st in self.SUIT_ORDER:
                    acts.append({"action": "bid", "level": lvl, "suit": st})
            return acts
        if s["phase"] == "playing":
            effective = s["dummy"] if s["turn"] == s.get("dummy") and seat == s.get("declarer") else seat
            if effective != s["turn"]:
                return []
            hand = s["hands"][str(effective)]
            lead = s["lead_suit"]
            if lead:
                follows = [c for c in hand if suit_of(c) == lead]
                if follows:
                    return [{"action": "play", "card": c} for c in follows]
            return [{"action": "play", "card": c} for c in hand]
        return []

    def apply(self, seat, action):
        s = self.state
        act = action.get("action")

        if s["phase"] == "bidding":
            if act == "bid":
                lvl = action.get("level", 1)
                st = action.get("suit", "NT")
                s["contract"] = f"{lvl}{st}"
                s["declarer"] = seat
                s["trump_suit"] = None if st == "NT" else st
                s["contract_tricks"] = 6 + lvl
                s["bids"][str(seat)] = s["contract"]
                self._say(s, seat, f"bid contract {s['contract']}")
            else:
                s["bids"][str(seat)] = "pass"
                self._say(s, seat, "passed")

            if len(s["bids"]) >= 4:
                dec = s["declarer"] if s["declarer"] is not None else 0
                s["declarer"] = dec
                s["contract"] = s["contract"] or "1NT"
                s["contract_tricks"] = s["contract_tricks"] or 7
                s["dummy"] = (dec + 2) % 4
                s["phase"] = "playing"
                s["turn"] = (dec + 1) % 4
                self._say(s, None, f"Contract locked: {s['contract']} by Seat {dec}. Dummy is Seat {s['dummy']}.")
            else:
                s["bid_turn"] = (s["bid_turn"] + 1) % 4
            return

        if s["phase"] == "playing":
            active_p = s["turn"]
            card = action.get("card")
            s["hands"][str(active_p)].remove(card)
            s["dummy_revealed"] = True

            if not s["trick"]:
                s["lead_suit"] = suit_of(card)
            s["trick"].append({"seat": active_p, "card": card})
            self._say(s, active_p, f"played {card}")

            if len(s["trick"]) == 4:
                lead = s["lead_suit"]
                trump = s["trump_suit"]

                def power_b(e):
                    c = e["card"]
                    return (2 if suit_of(c) == trump else (1 if suit_of(c) == lead else 0), rank_val(c))

                winner = max(s["trick"], key=power_b)["seat"]
                team = "team0" if winner in (0, 2) else "team1"
                s["tricks"][str(winner)] += 1
                s["team_tricks"][team] += 1
                self._say(s, winner, f"won trick (Team {team[-1]} total: {s['team_tricks'][team]})")
                s["trick"] = []
                s["lead_suit"] = None
                s["turn"] = winner

                if all(len(s["hands"][str(i)]) == 0 for i in range(4)):
                    s["over"] = True
                    dec_t = "team0" if s["declarer"] in (0, 2) else "team1"
                    won = s["team_tricks"][dec_t]
                    req = s["contract_tricks"]
                    if won >= req:
                        s["finish"] = [0, 2, 1, 3] if dec_t == "team0" else [1, 3, 0, 2]
                    else:
                        s["finish"] = [1, 3, 0, 2] if dec_t == "team0" else [0, 2, 1, 3]
                    self._say(s, None, f"Bridge round over. Declarer {dec_t} took {won}/{req} tricks.")
            else:
                s["turn"] = (active_p + 1) % 4


# =====================================================================
# 6. TEXAS HOLD'EM POKER (2-9 Players)
# =====================================================================
class TexasHoldem(BaseCardGame):
    """Texas Hold'em Poker: 2-9 players. 2 hole cards each.
    Community cards: Flop (3), Turn (1), River (1).
    Real betting rounds (blinds, check/call/raise/fold/all-in) that only
    advance once every live player has acted and matched the bet, then a
    genuine best-5-of-7 showdown via ``poker_hands.evaluate_best``."""

    slug = "poker"
    display_name = "Texas Hold'em Poker"
    min_players, max_players = 2, 9
    rules = ("2 hole cards each. Flop (3), Turn (1), River (1) community cards. "
             "Small/big blinds, then Check, Call, Raise, Fold, All-In each round. "
             "Best 5-card hand out of your 2 + the 5 community cards wins the pot.")

    START_STACK = 1000
    SMALL_BLIND = 10
    BIG_BLIND = 20
    RAISE_STEP = 100
    STAGES = ("preflop", "flop", "turn", "river")
    REVEAL_AT = {"flop": 3, "turn": 4, "river": 5}

    # ---------------------------------------------------------------- setup
    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {str(i): [deck.pop(), deck.pop()] for i in range(n)}
        community = [deck.pop() for _ in range(5)]
        sb, bb = cls.SMALL_BLIND, cls.BIG_BLIND
        stacks = {str(i): cls.START_STACK for i in range(n)}
        stacks[str(0)] -= sb                      # blinds come out of the
        if n > 1:                                 # posters' own stacks so
            stacks[str(1)] -= bb                  # chips stay conserved
        return {
            "slug": cls.slug, "players": list(players), "hands": hands,
            "community_cards": community, "visible_community": [],
            "pot": sb + bb, "current_bet": bb, "stage": "preflop",
            "turn": 2 if n > 2 else 0, "folded": [], "finish": [],
            "stacks": stacks,
            "round_bets": {str(0): sb, str(1): bb} if n > 1 else {},
            "acted": [],
            "log": ["Texas Hold'em started: blinds posted. Preflop betting."],
            "over": False,
        }

    def _norm(self, s):
        """Fill keys introduced by this rewrite so older stored states load."""
        n = len(s.get("players", []))
        s.setdefault("stacks", {str(i): self.START_STACK for i in range(n)})
        s.setdefault("round_bets", {str(i): 0 for i in range(n)})
        s.setdefault("acted", [])
        s.setdefault("folded", [])
        s.setdefault("visible_community", [])
        s.setdefault("finish", [])
        return s

    def view(self, seat):
        s = self._norm(self.state)
        to_call = None
        if seat is not None and seat not in s["folded"] and not s["over"]:
            to_call = max(0, s["current_bet"] - s["round_bets"].get(str(seat), 0))
        return {
            "slug": s["slug"], "players": s["players"], "stage": s["stage"],
            "pot": s["pot"], "current_bet": s["current_bet"], "turn": s["turn"],
            "community": s["visible_community"], "folded": s["folded"],
            "stacks": dict(s["stacks"]),
            "my_stack": s["stacks"].get(str(seat)) if seat is not None else None,
            "to_call": to_call,
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "hand_rank": (describe(evaluate_best(
                list(s["hands"].get(str(seat), []) + s["visible_community"]))
                ) if seat is not None and len(s["visible_community"]) >= 3 else None),
            "showdown_hands": s.get("showdown_hands", {}) if s["over"] else {},
            "finish": s["finish"], "over": s["over"], "log": s["log"][-20:]
        }

    # -------------------------------------------------------- betting logic
    def _needs_action(self, s, seat):
        if seat in s["folded"]:
            return False
        if s["stacks"].get(str(seat), 0) <= 0:
            return False                                    # all-in
        if seat not in s["acted"]:
            return True
        return s["round_bets"].get(str(seat), 0) != s["current_bet"]

    def _pending(self, s):
        return [i for i in range(len(s["players"])) if self._needs_action(s, i)]

    @staticmethod
    def _after(s, seat):
        n = len(s["players"])
        for i in range(1, n + 1):
            cand = (seat + i) % n
            if cand not in s["folded"] and s["stacks"].get(str(cand), 0) > 0:
                return cand
        return None

    def _match(self, legal, action):
        """Accept a client action that equals one of the generated ones
        (extra client-side keys are ignored, required keys must match)."""
        for a in legal:
            if a.get("action") != action.get("action"):
                continue
            if all(action.get(k) == v for k, v in a.items()):
                return a
        return None

    def legal_actions(self, seat):
        s = self._norm(self.state)
        if s["over"] or seat != s["turn"] or seat in s["folded"]:
            return []
        if s["stage"] not in self.STAGES:
            return []
        stack = s["stacks"].get(str(seat), 0)
        to_call = s["current_bet"] - s["round_bets"].get(str(seat), 0)
        acts = []
        if to_call <= 0:
            acts.append({"action": "check"})
        elif stack <= to_call:
            acts.append({"action": "allin", "amount": stack})
        else:
            acts.append({"action": "call", "amount": to_call})
        if stack > to_call:
            ceiling = s["round_bets"].get(str(seat), 0) + stack
            target = min(s["current_bet"] + self.RAISE_STEP, ceiling)
            if target > s["current_bet"]:
                acts.append({"action": "raise", "amount": target})
        acts.append({"action": "fold"})
        return acts

    def _pay(self, s, seat, amount):
        stack = s["stacks"].get(str(seat), 0)
        amount = max(0, min(int(amount), stack))
        s["stacks"][str(seat)] = stack - amount
        s["round_bets"][str(seat)] = s["round_bets"].get(str(seat), 0) + amount
        s["pot"] += amount
        return amount

    def apply(self, seat, action):
        s = self._norm(self.state)
        self._require_turn(s, seat)
        if seat in s["folded"]:
            raise IllegalMove("You already folded")
        legal = self.legal_actions(seat)
        move = self._match(legal, action)
        if move is None:
            raise IllegalMove("That action is not available in this betting round")

        kind = move["action"]
        stack = s["stacks"].get(str(seat), 0)
        to_call = s["current_bet"] - s["round_bets"].get(str(seat), 0)

        if kind == "fold":
            s["folded"].append(seat)
            s["acted"].append(seat)
            self._say(s, seat, "folded")
        elif kind == "check":
            s["acted"].append(seat)
            self._say(s, seat, "checked")
        elif kind in ("call", "allin"):
            paid = self._pay(s, seat, min(to_call, stack))
            s["acted"].append(seat)
            if s["round_bets"][str(seat)] > s["current_bet"]:
                s["current_bet"] = s["round_bets"][str(seat)]
                s["acted"] = [seat]                        # others must respond
            verb = "calls" if kind == "call" else "is all-in for"
            self._say(s, seat, f"{verb} {paid} (pot: {s['pot']})")
        else:                                              # raise
            target = int(move["amount"])
            self._pay(s, seat, target - s["round_bets"].get(str(seat), 0))
            s["current_bet"] = s["round_bets"][str(seat)]
            s["acted"] = [seat]                            # re-open the action
            self._say(s, seat, f"raises to {s['current_bet']} (pot: {s['pot']})")

        active = [i for i in range(len(s["players"])) if i not in s["folded"]]
        if len(active) <= 1:
            self._win_by_fold(s, active[0] if active else seat)
            return

        if not self._pending(s):
            self._next_street(s)
        else:
            nxt = self._after(s, seat)
            while nxt is not None and not self._needs_action(s, nxt):
                nxt = self._after(s, nxt)
            s["turn"] = nxt if nxt is not None else self._first_pending(s)

    def _first_pending(self, s):
        pending = self._pending(s)
        return pending[0] if pending else None

    # ------------------------------------------------------------- streets
    def _win_by_fold(self, s, seat):
        s["over"] = True
        s["stage"] = "showdown"
        s["turn"] = -1
        s["finish"] = [seat] + [i for i in reversed(s["folded"]) if i != seat]
        s["showdown_winners"] = [seat]
        self._say(s, seat, f"wins the pot of {s['pot']} - everyone else folded")

    def _next_street(self, s):
        idx = self.STAGES.index(s["stage"]) if s["stage"] in self.STAGES else 0
        if s["stage"] == "river":
            self._showdown(s)
            return
        nxt_stage = self.STAGES[idx + 1]
        s["stage"] = nxt_stage
        s["visible_community"] = s["community_cards"][:self.REVEAL_AT[nxt_stage]]
        s["round_bets"] = {str(i): 0 for i in range(len(s["players"]))}
        s["current_bet"] = 0
        s["acted"] = []
        card = s["visible_community"][-1] if s["stage"] != "flop" else None
        self._say(s, None, (f"Flop: {' '.join(s['visible_community'])}"
                            if s["stage"] == "flop" else f"{s['stage'].title()}: {card}"))

        # Nobody can bet any more (everyone all-in): run the board out.
        if not self._pending(s):
            while s["stage"] != "river":
                i = self.STAGES.index(s["stage"]) + 1
                s["stage"] = self.STAGES[i]
                s["visible_community"] = s["community_cards"][:self.REVEAL_AT[s["stage"]]]
            self._showdown(s)
            return
        # Postflop the first player to act is the one left of the button.
        first = self._after(s, 0)
        s["turn"] = first if first is not None else self._first_pending(s)

    def _showdown(self, s):
        s["visible_community"] = list(s["community_cards"])
        s["stage"] = "showdown"
        s["over"] = True
        s["turn"] = -1
        active = [i for i in range(len(s["players"])) if i not in s["folded"]]
        board = s["visible_community"]
        scores = {}
        ranks = {}
        for i in active:
            cards = list(s["hands"][str(i)]) + board
            scores[i] = evaluate_best(cards)
            ranks[str(i)] = describe(scores[i])
        order = sorted(active, key=lambda i: scores[i], reverse=True)
        best = scores[order[0]]
        winners = [i for i in order if scores[i] == best]
        s["showdown_winners"] = winners
        s["showdown_hands"] = ranks
        s["finish"] = winners + [i for i in order if i not in winners] + \
            [i for i in reversed(s["folded"]) if i not in order]
        label = describe(best)
        if len(winners) > 1:
            self._say(s, None, f"Showdown: {label} splits the pot of {s['pot']} "
                               f"between seats {winners}")
        else:
            self._say(s, winners[0], f"wins the showdown with {label} "
                                     f"(pot: {s['pot']})")

    def winners(self):
        w = self.state.get("showdown_winners")
        if w:
            return list(w)
        finish = self.state.get("finish") or []
        return finish[:1]


# =====================================================================
# 7. BLACKJACK / 21 (2-7 Players vs Dealer)
# =====================================================================
class Blackjack(BaseCardGame):
    """Blackjack: 2-7 players. Dealer plays at seat 0 (or house).
    Card values: 2-10 face value, J/Q/K = 10, Ace = 1 or 11.
    Hit, Stand, Double Down. Bust on >21. Closest to 21 wins."""

    slug = "blackjack"
    display_name = "Blackjack (21)"
    min_players, max_players = 2, 7
    rules = ("Get closer to 21 than the dealer without busting. "
             "J, Q, K = 10, Ace = 1 or 11. Actions: Hit, Stand, Double Down. "
             "Dealer must hit until 17+.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck() * 2
        rng.shuffle(deck)
        hands = {str(i): [deck.pop(), deck.pop()] for i in range(n)}
        dealer_hand = [deck.pop(), deck.pop()]
        return {
            "slug": cls.slug, "players": list(players), "deck": deck,
            "hands": hands, "dealer": dealer_hand, "turn": 0,
            "status": {str(i): "playing" for i in range(n)},
            "dealer_revealed": False, "finish": [],
            "log": ["Blackjack shoe shuffled. Cards dealt."], "over": False
        }

    @staticmethod
    def hand_val(cards):
        total = 0
        aces = 0
        for c in cards:
            r = c[1:]
            if r in ("J", "Q", "K", "T"):
                total += 10
            elif r == "A":
                total += 11
                aces += 1
            else:
                total += int(r)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def view(self, seat):
        s = self.state
        d_view = [s["dealer"][0], "??" ] if not s["dealer_revealed"] else s["dealer"]
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "dealer_cards": d_view, "dealer_val": self.hand_val(s["dealer"]) if s["dealer_revealed"] else None,
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "hand_val": self.hand_val(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-20:]
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or seat != s["turn"] or s["status"].get(str(seat)) != "playing":
            return []
        v = self.hand_val(s["hands"][str(seat)])
        if v >= 21:
            return [{"action": "stand"}]
        return [{"action": "hit"}, {"action": "stand"}, {"action": "double"}]

    def apply(self, seat, action):
        s = self.state
        act = action.get("action")
        hand = s["hands"][str(seat)]

        if act in ("hit", "double"):
            card = s["deck"].pop()
            hand.append(card)
            val = self.hand_val(hand)
            self._say(s, seat, f"drew {card} (total: {val})")
            if val > 21:
                s["status"][str(seat)] = "bust"
                self._say(s, seat, f"BUSTED ({val})")
            elif act == "double" or val == 21:
                s["status"][str(seat)] = "stood"
        else:
            s["status"][str(seat)] = "stood"
            self._say(s, seat, f"stands on {self.hand_val(hand)}")

        # Next player or dealer resolution
        n = len(s["players"])
        nxt = seat + 1
        while nxt < n and s["status"].get(str(nxt)) != "playing":
            nxt += 1

        if nxt >= n:
            # Dealer turn
            s["dealer_revealed"] = True
            d_val = self.hand_val(s["dealer"])
            while d_val < 17:
                c = s["deck"].pop()
                s["dealer"].append(c)
                d_val = self.hand_val(s["dealer"])
                self._say(s, None, f"Dealer drew {c} (total: {d_val})")

            s["over"] = True
            # Winner determination
            winners = []
            for i in range(n):
                p_val = self.hand_val(s["hands"][str(i)])
                if p_val <= 21 and (d_val > 21 or p_val > d_val):
                    winners.append(i)
            s["finish"] = winners if winners else [0]
            self._say(s, None, f"Round resolved. Dealer finished with {d_val}.")
        else:
            s["turn"] = nxt


# =====================================================================
# 8. CRAZY EIGHTS / UNO STYLE (2-7 Players)
# =====================================================================
from models.card_club.engines.shedding import Blitz

class CrazyEights(Blitz):
    """Crazy Eights / Uno-Style Card Game: 2-7 players.
    Match by suit or rank. 8 is wild (names suit).
    2 forces next player to draw 2. Q skips / reverses."""

    slug = "crazy_eights"
    display_name = "Crazy Eights (Uno Style)"
    min_players, max_players = 2, 7
    rules = ("Match top card by suit or rank. 8 is wild (choose suit). "
             "2 forces next player to draw 2 cards. "
             "Queen reverses turn direction. Empty your hand first to win.")
