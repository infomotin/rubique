"""Trick-taking engines: Knock Out Whist (2-7, multi-round elimination)."""

import random

from models.card_club.errors import IllegalMove
from models.card_club.engines.base import (
    BaseCardGame, full_deck, rank_val, suit_of,
)


class KnockOutWhist(BaseCardGame):
    """Knock Out Whist (2-7). Fresh deal each round, trump from a flipped
    card; take zero tricks and you are out. Last player standing wins."""

    slug = "knockout_whist"
    display_name = "Knock Out Whist"
    min_players, max_players = 2, 7
    rules = ("Each round deals up to 7 cards (deck permitting); the next card "
             "trumped face-up sets the trump suit. Follow suit if you can, "
             "otherwise trump or discard. Highest trump (or highest of the led "
             "suit) wins the trick and leads. Anyone who takes zero tricks in "
             "a round is knocked out. Last player alive wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck()
        rng.shuffle(deck)
        state = {
            "slug": cls.slug, "players": list(players), "deck": deck,
            "hands": {str(i): [] for i in range(n)},
            "tricks": {str(i): 0 for i in range(n)},
            "trick": [], "lead_suit": None, "trump": None,
            "turn": 0, "round": 0, "elim_order": [],
            "finish": [], "log": [], "over": False,
        }
        obj = cls(state)
        obj._deal_round()
        return state

    @property
    def active(self):
        return [i for i in range(len(self.state["players"]))
                if i not in self.state["elim_order"]]

    def _deal_round(self):
        s = self.state
        n = len(self.active)
        deal = min(7, len(s["deck"]) // n) if n else 0
        if deal < 1:
            self._close(s)
            return
        for seat in self.active:
            s["hands"][str(seat)] = [s["deck"].pop() for _ in range(deal)]
        trump_card = s["deck"].pop()
        s["trump"] = trump_card[0]
        s["tricks"] = {str(i): 0 for i in range(len(s["players"]))}
        s["trick"] = []
        s["lead_suit"] = None
        s["round"] += 1
        self._say(s, None, f"round {s['round']}: trump is {s['trump']} ({trump_card})")
        order = self.active
        s["turn"] = order[0]

    def _close(self, s):
        survivors = [i for i in self.active]
        rest = list(reversed(s["elim_order"]))
        s["finish"] = survivors + [i for i in rest if i not in survivors]
        if not s["finish"]:
            s["finish"] = list(range(len(s["players"])))
        s["over"] = True
        s["turn"] = -1

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "round": s["round"], "trump": s["trump"], "lead_suit": s["lead_suit"],
            "trick": s["trick"], "tricks": s["tricks"],
            "active": self.active, "eliminated": s["elim_order"],
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or seat != s["turn"]:
            return []
        hand = s["hands"][str(seat)]
        if s["lead_suit"]:
            follows = [c for c in hand if suit_of(c) == s["lead_suit"]]
            if follows:
                return [{"action": "play", "card": c} for c in follows]
        return [{"action": "play", "card": c} for c in hand]

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        if seat != s["turn"]:
            raise IllegalMove("Not your turn")
        if action.get("action") != "play":
            raise IllegalMove("Unknown action")
        card = action.get("card")
        hand = s["hands"][str(seat)]
        if card not in hand:
            raise IllegalMove("You do not hold that card")
        if s["lead_suit"] and suit_of(card) != s["lead_suit"] and \
                any(suit_of(c) == s["lead_suit"] for c in hand):
            raise IllegalMove("You must follow suit")
        hand.remove(card)
        if not s["trick"]:
            s["lead_suit"] = suit_of(card)
        s["trick"].append({"seat": seat, "card": card})
        if len(s["trick"]) == len(self.active):
            def strength(entry):
                c = entry["card"]
                suit = suit_of(c)
                return (2 if suit == s["trump"] else
                        1 if suit == s["lead_suit"] else 0, rank_val(c))
            winner = max(s["trick"], key=strength)["seat"]
            s["tricks"][str(winner)] += 1
            self._say(s, winner, f"won the trick (round total {s['tricks'][str(winner)]})")
            s["trick"] = []
            s["lead_suit"] = None
            if all(not s["hands"][str(i)] for i in self.active):
                self._end_round()
            else:
                s["turn"] = winner
        else:
            nxt = self._next(s, seat)
            while nxt in s["elim_order"] and not s["over"]:
                nxt = self._next(s, nxt)
            s["turn"] = nxt

    def _end_round(self):
        s = self.state
        knocked = [i for i in self.active if s["tricks"][str(i)] == 0]
        if len(knocked) == len(self.active):
            knocked = [i for i in self.active[1:]]   # never wipe the table
        for i in knocked:
            s["elim_order"].append(i)
            self._say(s, i, "took no tricks - KNOCKED OUT")
        alive = [i for i in self.active]
        if len(alive) <= 1:
            self._close(s)
            return
        self._deal_round()
