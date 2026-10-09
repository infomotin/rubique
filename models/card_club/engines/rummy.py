"""Rummy engine (2-6): draw, meld sets/runs, discard; first out wins."""

import random

from models.card_club.errors import IllegalMove
from models.card_club.engines.base import (
    BaseCardGame, full_deck, rank_val, suit_of, RANK_VALUE,
)


def _run(cards):
    """Cards form a straight of one suit (A low in A-2-3, A high in Q-K-A)."""
    if len(cards) < 3 or len(set(suit_of(c) for c in cards)) != 1:
        return False
    vals = sorted(rank_val(c) for c in cards)
    if vals == list(range(vals[0], vals[0] + len(vals))):
        return True
    if 14 in vals:                                   # A may act as 1 (A-2-3...)
        alt = sorted(1 if v == 14 else v for v in vals)
        return alt == list(range(alt[0], alt[0] + len(alt)))
    return False


def _set(cards):
    return len(cards) >= 3 and len(set(c[1] for c in cards)) == 1 and \
        len(set(suit_of(c) for c in cards)) >= 2


def valid_meld(cards):
    return _set(cards) or _run(cards)


class Rummy(BaseCardGame):
    slug = "rummy"
    display_name = "Rummy"
    min_players, max_players = 2, 6
    rules = ("Deal 7 each. On your turn draw from the stock or take the "
             "discard, meld any sets (3-4 of a rank) or runs (3+ same suit) "
             "you hold, then discard - or go out by melding everything. A is "
             "low in A-2-3 and high in Q-K-A. Empty hand to win; if the stock "
             "runs dry the lowest deadwood total wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        deck = full_deck()
        rng.shuffle(deck)
        hands = {i: [deck.pop() for _ in range(7)] for i in range(len(players))}
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "stock": deck, "discard": [deck.pop()],
            "melds": {str(i): [] for i in range(len(players))},
            "drew": False, "melded": False, "turn": 0,
            "finish": [], "log": [], "over": False,
        }

    @staticmethod
    def _deadwood(hand):
        return sum(rank_val(c) if c[1] != "A" else 1 for c in hand)

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "top": s["discard"][-1], "stock_count": len(s["stock"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "melds": s["melds"], "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or seat != s["turn"]:
            return []
        acts = []
        if not s["drew"]:
            if s["stock"]:
                acts.append({"action": "draw"})
            acts.append({"action": "take_discard"})
            return acts
        hand = s["hands"][str(seat)]
        acts = [{"action": "discard", "card": c} for c in hand]
        acts.extend(self._meld_moves(seat))
        return acts

    def _meld_moves(self, seat):
        """Generate playability for every valid meld subset (sizes 3-4)."""
        import itertools
        s = self.state
        hand = s["hands"][str(seat)]
        out = []
        for n in (3, 4):
            if len(hand) < n:
                continue
            seen = set()
            for combo in itertools.combinations(hand, n):
                key = tuple(sorted(combo))
                if key in seen:
                    continue
                seen.add(key)
                if valid_meld(list(combo)):
                    out.append({"action": "meld", "cards": list(combo)})
        return out

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        if seat != s["turn"]:
            raise IllegalMove("Not your turn")
        act = action.get("action")
        hand = s["hands"][str(seat)]
        if act == "draw":
            if s["drew"]:
                raise IllegalMove("Already drew")
            if not s["stock"]:
                raise IllegalMove("Stock is empty")
            hand.append(s["stock"].pop())
            s["drew"] = True
            return
        if act == "take_discard":
            if s["drew"]:
                raise IllegalMove("Already drew")
            if not s["discard"]:
                raise IllegalMove("Discard is empty")
            hand.append(s["discard"].pop())
            s["drew"] = True
            return
        if act == "meld":
            cards = action.get("cards") or []
            if not s["drew"]:
                raise IllegalMove("Draw first")
            if not cards or any(c not in hand for c in cards) or not valid_meld(cards):
                raise IllegalMove("Not a valid meld")
            for c in cards:
                hand.remove(c)
            s["melds"][str(seat)].append(list(cards))
            s["melded"] = True
            self._say(s, seat, f"melded {len(cards)} cards")
            if not hand:
                self._go_out(seat)
            return
        if act == "discard":
            if not s["drew"]:
                raise IllegalMove("Draw first")
            card = action.get("card")
            if card not in hand:
                raise IllegalMove("You do not hold that card")
            hand.remove(card)
            s["discard"].append(card)
            s["drew"] = False
            s["melded"] = False
            s["turn"] = self._next(s, seat)
            if not s["stock"]:
                self._exhaust()
            return
        raise IllegalMove("Unknown action")

    def _go_out(self, seat):
        s = self.state
        self._finish(s, seat)
        s["finish"] += [i for i in range(len(s["players"])) if i != seat]
        s["over"] = True
        s["turn"] = -1
        self._say(s, seat, "goes out")

    def _exhaust(self):
        s = self.state
        order = sorted(range(len(s["players"])),
                       key=lambda i: self._deadwood(s["hands"][str(i)]))
        s["finish"] = order
        s["over"] = True
        s["turn"] = -1
        self._say(s, None, "stock exhausted - deadwood decides")
