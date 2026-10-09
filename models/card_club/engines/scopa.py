"""Scopa engine (2-6): capture single ranks or sums; most points wins."""

import itertools
import random

from models.card_club.errors import IllegalMove
from models.card_club.engines.base import BaseCardGame, full_deck, rank_val, RANK_VALUE


def _value(card):
    r = card[1]
    if r == "A":
        return 1
    if r in "JQK":
        return {"J": 11, "Q": 12, "K": 13}[r]
    return RANK_VALUE[r]


class Scopa(BaseCardGame):
    slug = "scopa"
    display_name = "Scopa"
    min_players, max_players = 2, 6
    rules = ("Deal 3 each and 4 to the table. Play one card: capture a table "
             "card of the same rank, any set of table cards summing to your "
             "card's value, or leave your card on the table. Emptying the "
             "table is a scopa (+1). Points at the end: most cards, the 7 of "
             "diamonds, and each scopa. Highest points wins; ties share.")

    POINTS = {"cards": 1, "settebello": 1, "scopa": 1}

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {i: [deck.pop() for _ in range(3)] for i in range(len(players))}
        table = [deck.pop() for _ in range(4)]
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "stock": deck, "table": table,
            "piles": {str(i): [] for i in range(len(players))},
            "scopas": {str(i): 0 for i in range(len(players))},
            "turn": 0, "finish": [], "log": [], "over": False,
        }

    def _captures(self, seat, card):
        """Legal capture lists: single same-rank, or any subset summing to
        the card's value (values are 1-14, so pruned subset-sum stays tiny)."""
        table = self.state["table"]
        v = _value(card)
        seen = set()
        out = []
        for c in table:
            if c[1] == card[1]:
                key = (c,)
                if key not in seen:
                    seen.add(key)
                    out.append([c])
        vals = [(_value(c), c) for c in table]

        def walk(start, need, chosen):
            if need == 0:
                key = tuple(sorted(chosen))
                if key not in seen:
                    seen.add(key)
                    out.append(list(chosen))
                return
            for i in range(start, len(vals)):
                val, card_c = vals[i]
                if val > need:
                    continue
                chosen.append(card_c)
                walk(i + 1, need - val, chosen)
                chosen.pop()

        walk(0, v, [])
        return out

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "table": list(s["table"]), "stock_count": len(s["stock"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "piles": {k: len(v) for k, v in s["piles"].items()},
            "scopas": s["scopas"],
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or seat != s["turn"]:
            return []
        acts = []
        for c in s["hands"][str(seat)]:
            acts.append({"action": "play", "card": c, "capture": []})
            for combo in self._captures(seat, c):
                acts.append({"action": "play", "card": c, "capture": list(combo)})
        return acts

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        if seat != s["turn"]:
            raise IllegalMove("Not your turn")
        if action.get("action") != "play":
            raise IllegalMove("Unknown action")
        card = action.get("card")
        capture = action.get("capture") or []
        hand = s["hands"][str(seat)]
        if card not in hand:
            raise IllegalMove("You do not hold that card")
        if capture:
            if any(c not in s["table"] for c in capture):
                raise IllegalMove("Capture cards are not on the table")
            same_rank = len(capture) == 1 and capture[0][1] == card[1]
            same_sum = sum(_value(c) for c in capture) == _value(card)
            if not (same_rank or same_sum):
                raise IllegalMove("Illegal capture (same rank or exact sum)")
        hand.remove(card)
        s["piles"][str(seat)].append(card)
        if capture:
            for c in capture:
                s["table"].remove(c)
            if not s["table"]:
                s["scopas"][str(seat)] += 1
                self._say(s, seat, "SCOPA!")
        else:
            s["table"].append(card)
        self._say(s, seat, f"played {card}" + (f" capturing {len(capture)}" if capture else ""))
        if not hand and s["stock"]:
            hand.extend([s["stock"].pop() for _ in range(3) if s["stock"]])
        if all(not v for v in s["hands"].values()):
            self._score_and_close()
            return
        nxt = self._next(s, seat)
        guard = 0
        while not s["hands"][str(nxt)] and guard < len(s["players"]):
            nxt = self._next(s, nxt)
            guard += 1
        if all(not s["hands"][str(i)] for i in range(len(s["players"]))):
            self._score_and_close()
            return
        s["turn"] = nxt

    def _score_and_close(self):
        s = self.state
        points = {str(i): 0 for i in range(len(s["players"]))}
        counts = {i: len(s["piles"][str(i)]) for i in range(len(s["players"]))}
        # leftover table cards go to the last winner (player before dealer)
        top = max(counts.values())
        winners_cards = [i for i, c in counts.items() if c == top]
        for i in winners_cards:
            points[str(i)] += 1
        for i in range(len(s["players"])):
            if any(c == "D7" for c in s["piles"][str(i)]):
                points[str(i)] += 1
            points[str(i)] += s["scopas"][str(i)]
        order = sorted(range(len(s["players"])), key=lambda i: -points[str(i)])
        best = points[str(order[0])]
        winners = [i for i in order if points[str(i)] == best]
        s["finish"] = winners + [i for i in order if i not in winners]
        s["scores"] = points
        s["over"] = True
        s["turn"] = -1
        self._say(s, None, f"final points: {points}")

    def winners(self):
        s = self.state
        if not s.get("finish"):
            return []
        best_score = s.get("scores", {}).get(str(s["finish"][0]))
        return [i for i in s["finish"]
                if s.get("scores", {}).get(str(i)) == best_score]
