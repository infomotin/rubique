"""Real-time engines: Egyptian Ratscrew (slap), Speed (race), Spoons
(turn-based passing with a grab reaction)."""

import random

from models.card_club.errors import IllegalMove
from models.card_club.engines.base import (
    BaseCardGame, full_deck, rank_val, suit_of, RANK_VALUE,
)


class EgyptianRatscrew(BaseCardGame):
    """Egyptian Ratscrew (2-6, real-time). Flip in seat order; anyone may
    slap a double, sandwich or three-of-a-kind. False slaps pay the pile."""

    slug = "ers"
    display_name = "Egyptian Ratscrew"
    min_players, max_players = 2, 6
    real_time = True
    rules = ("Deal everything. Flip one card per turn in seat order; any player "
             "may SLAP at any moment on: a pair (two equal ranks), a sandwich "
             "(A B A), or three equal ranks in a row. Fastest valid slap takes "
             "the whole pile; a false slap feeds your top card to the pile. "
             "Last player holding cards wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {i: [] for i in range(len(players))}
        i = 0
        while deck:
            hands[i % len(players)].append(deck.pop())
            i += 1
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "pile": [], "turn": 0, "finish": [], "log": [], "over": False,
        }

    def _slap_valid(self):
        p = self.state["pile"]
        if len(p) >= 3 and p[-1][1] == p[-3][1] and p[-1][1] != p[-2][1]:
            return True                     # sandwich A B A
        if len(p) >= 3 and p[-1][1] == p[-2][1] == p[-3][1]:
            return True                     # three of a kind
        if len(p) >= 2 and p[-1][1] == p[-2][1]:
            return True                     # pair
        return False

    def _sweep(self):
        """Eliminate any player whose hand ran dry; declare a winner."""
        s = self.state
        if s["over"]:
            return
        for i in range(len(s["players"])):
            if not s["hands"][str(i)] and i not in s["finish"]:
                s["finish"].append(i)
                self._say(s, i, "is out of cards")
        alive = [i for i in range(len(s["players"])) if i not in s["finish"]]
        if len(alive) <= 1 and len(s["players"]) > 1:
            for i in alive:
                if i not in s["finish"]:
                    s["finish"].insert(0, i)
            s["over"] = True
            s["turn"] = -1
        elif alive and s["turn"] not in alive:
            while s["turn"] not in alive and not s["over"]:
                s["turn"] = self._next(s, s["turn"])

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "pile_top": s["pile"][-1] if s["pile"] else None,
            "pile_count": len(s["pile"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"]:
            return []
        acts = []
        if seat == s["turn"] and s["hands"][str(seat)]:
            acts.append({"action": "flip"})
        if s["pile"]:
            acts.append({"action": "slap"})
        return acts

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        act = action.get("action")
        if act == "flip":
            if seat != s["turn"]:
                raise IllegalMove("Not your flip")
            hand = s["hands"][str(seat)]
            if not hand:
                raise IllegalMove("You have no cards to flip")
            card = hand.pop(0)
            s["pile"].append(card)
            self._say(s, seat, f"flipped {card}")
            if not hand:
                pass  # player may still be in until sweep decides
            s["turn"] = self._next(s, seat)
            self._sweep()
            return
        if act == "slap":
            if not s["pile"]:
                raise IllegalMove("Nothing to slap")
            if not s["hands"].get(str(seat)):
                raise IllegalMove("You have no cards to slap with")
            if self._slap_valid():
                won = s["pile"]
                s["pile"] = []
                s["hands"][str(seat)] += won
                self._say(s, seat, f"SLAP! takes {len(won)} cards")
                s["turn"] = seat
                self._sweep()
            else:
                top = s["hands"][str(seat)].pop(0)
                s["pile"].append(top)
                self._say(s, seat, "false slap - pays the pile")
                self._sweep()
            return
        raise IllegalMove("Unknown action")


class Speed(BaseCardGame):
    """Speed (2-4, real-time). Race your cards onto the ascending and
    descending centre piles; empty hand and stock first."""

    slug = "speed"
    display_name = "Speed"
    min_players, max_players = 2, 4
    real_time = True
    rules = ("Each player gets a 5-card hand and a personal stock. Anyone may "
             "play at any time onto the ascending pile (start on A, climb by "
             "one, any suit) or descending pile (start on K, descend). Empty "
             "your hand and stock first. With an empty hand, top up from your "
             "stock automatically; draw when stuck.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {i: [deck.pop() for _ in range(5)] for i in range(n)}
        stock = {}
        base = max(1, (len(deck) - 0) // n)
        for i in range(n):
            stock[i] = [deck.pop() for _ in range(min(base, len(deck)))]
            if i == 0:                      # leftover cards to seat 0
                while deck:
                    stock[0].append(deck.pop())
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "stocks": {str(k): v for k, v in stock.items()},
            "up": [], "down": [], "finish": [], "log": [], "over": False,
        }

    @staticmethod
    def _card_value(card):
        r = card[1]
        return 1 if r == "A" else 11 if r == "J" else 12 if r == "Q" else \
            13 if r == "K" else RANK_VALUE[r]

    def _playable_on(self, seat, pile):
        s = self.state
        cards = s["hands"][str(seat)]
        top = s[pile][-1] if s[pile] else None
        out = []
        for c in cards:
            v = self._card_value(c)
            if pile == "up":
                if top is None and c[1] == "A":
                    out.append(c)
                elif top is not None and self._card_value(top) < 13 and v == self._card_value(top) + 1:
                    out.append(c)
            else:
                if top is None and c[1] == "K":
                    out.append(c)
                elif top is not None and self._card_value(top) > 1 and v == self._card_value(top) - 1:
                    out.append(c)
        return out

    def _top_up(self, seat):
        s = self.state
        key = str(seat)
        if not s["hands"][key] and s["stocks"][key]:
            s["hands"][key].append(s["stocks"][key].pop())

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"],
            "up": list(s["up"]), "down": list(s["down"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "stock_counts": {str(k): len(v) for k, v in s["stocks"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or seat in s["finish"]:
            return []
        acts = []
        for pile in ("up", "down"):
            for c in self._playable_on(seat, pile):
                acts.append({"action": "play", "card": c, "pile": pile})
        if not acts:
            acts.append({"action": "draw"} if s["stocks"][str(seat)]
                        else {"action": "pass"})
        return acts

    def apply(self, seat, action):
        s = self.state
        if s["over"] or seat in s["finish"]:
            raise IllegalMove("Game is over")
        act = action.get("action")
        key = str(seat)
        if act == "play":
            card, pile = action.get("card"), action.get("pile")
            if pile not in ("up", "down") or card not in s["hands"][key]:
                raise IllegalMove("Bad play")
            if card not in self._playable_on(seat, pile):
                raise IllegalMove("Card does not fit that pile")
            s["hands"][key].remove(card)
            s[pile].append(card)
            self._say(s, seat, f"{card} on {pile}")
            self._top_up(seat)
            if not s["hands"][key] and not s["stocks"][key]:
                s["finish"].append(seat)
                self._say(s, seat, "is out - wins!")
                if len(s["finish"]) == 1:
                    s["finish"] += [i for i in range(len(s["players"])) if i != seat]
                    s["over"] = True
            return
        if act == "draw":
            if not s["stocks"][key]:
                raise IllegalMove("Stock is empty")
            s["hands"][key].append(s["stocks"][key].pop())
            self._top_up(seat)
            return
        if act == "pass":
            if self._playable_on(seat, "up") or self._playable_on(seat, "down") or s["stocks"][key]:
                raise IllegalMove("You still have options")
            # Stuck: only decisive when nobody can finish anymore.
            any_stock = any(s["stocks"].values())
            any_play = any(self._playable_on(i, "up") or self._playable_on(i, "down")
                           for i in range(len(s["players"])))
            if any_stock or any_play:
                self._say(s, seat, "stuck for now")
                return
            order = sorted(range(len(s["players"])),
                           key=lambda i: (len(s["hands"][str(i)]) + len(s["stocks"][str(i)]), i))
            s["finish"] = order
            s["over"] = True
            return
        raise IllegalMove("Unknown action")


class Spoons(BaseCardGame):
    """Spoons (2-8, turn-based passing). Hold four of a kind, grab first."""

    slug = "spoons"
    display_name = "Spoons"
    min_players, max_players = 2, 8
    rules = ("Deal 4 each; spoons = players - 1 on the table. On your turn "
             "draw from the stock and pass any card to the next seat, or grab "
             "a spoon as soon as you hold four of a kind. After the first grab "
             "each remaining player in order may also grab (if qualified). "
             "Everyone left without a spoon scores +4; the first grabber wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {i: [deck.pop() for _ in range(4)] for i in range(n)}
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "stock": deck, "spoons": max(0, n - 1), "turn": 0,
            "grab_phase": False, "grabs": [], "points": {str(i): 0 for i in range(n)},
            "finish": [], "log": [], "over": False, "passes": 0,
        }

    @staticmethod
    def _has_four(hand):
        counts = {}
        for c in hand:
            counts[c[1]] = counts.get(c[1], 0) + 1
        return any(v >= 4 for v in counts.values())

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "spoons": s["spoons"], "grab_phase": s["grab_phase"],
            "grabs": list(s["grabs"]), "stock_count": len(s["stock"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"]:
            return []
        acts = []
        if (self._has_four(s["hands"][str(seat)]) and len(s["grabs"]) < s["spoons"]
                and seat == s["turn"]):
            acts.append({"action": "grab"})
        if s["grab_phase"]:
            if seat == s["turn"]:
                acts.append({"action": "react"})
            return acts
        if seat == s["turn"]:
            if s["stock"]:
                for c in s["hands"][str(seat)]:
                    acts.append({"action": "draw_pass", "card": c})
            else:
                acts.append({"action": "stalemate"})
        return acts

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        act = action.get("action")
        if act == "grab":
            if not self._has_four(s["hands"][str(seat)]):
                raise IllegalMove("You do not hold four of a kind")
            if len(s["grabs"]) >= s["spoons"]:
                raise IllegalMove("No spoons left")
            if not s["grab_phase"] and seat != s["turn"]:
                raise IllegalMove("Not your turn to grab yet")
            s["grabs"].append(seat)
            self._say(s, seat, "grabbed a spoon")
            if not s["grab_phase"]:
                s["grab_phase"] = True
                s["turn"] = self._next(s, seat)
            else:
                s["turn"] = self._next(s, s["turn"])
            if s["grab_phase"] and s["turn"] == s["grabs"][0]:
                self._resolve()
            elif len(s["grabs"]) >= s["spoons"] and s["grab_phase"]:
                self._resolve()
            return
        if act == "stalemate":
            if seat != s["turn"] or s["grab_phase"] or s["stock"]:
                raise IllegalMove("Not applicable")
            self._resolve_deadlock()
            return
        if act == "react":
            if seat != s["turn"] or not s["grab_phase"]:
                raise IllegalMove("Not your reaction")
            s["turn"] = self._next(s, seat)
            if s["turn"] == s["grabs"][0]:
                self._resolve()
            return
        if act == "draw_pass":
            if seat != s["turn"] or s["grab_phase"]:
                raise IllegalMove("Not your turn")
            if not s["stock"]:
                self._resolve_deadlock()
                return
            s["hands"][str(seat)].append(s["stock"].pop())
            hand = s["hands"][str(seat)]
            card = action.get("card") or (hand[0] if hand else None)
            if card not in hand:
                raise IllegalMove("Pass one card you hold")
            hand.remove(card)
            nxt = self._next(s, seat)
            s["hands"][str(nxt)].append(card)
            s["passes"] += 1
            s["turn"] = nxt
            if self._has_four(s["hands"][str(nxt)]):
                self._say(s, nxt, "has four of a kind")
            return
        raise IllegalMove("Unknown action")

    def _resolve_deadlock(self):
        """Stock gone and nobody qualified: round is a wash."""
        s = self.state
        s["finish"] = list(range(len(s["players"])))
        s["over"] = True
        s["turn"] = -1
        self._say(s, None, "round washed - nobody qualified")

    def _resolve(self):
        s = self.state
        grabbed = list(s["grabs"])
        for i in range(len(s["players"])):
            if i not in grabbed:
                s["points"][str(i)] += 4
        order = grabbed + [i for i in range(len(s["players"])) if i not in grabbed]
        s["finish"] = order
        s["over"] = True
        s["turn"] = -1
