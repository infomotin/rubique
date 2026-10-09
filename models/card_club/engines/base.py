"""Shared card utilities and the base class for all Card Club game engines.

Every engine is JSON-state driven: the state dict is persisted in
`club_tables.state` and rebuilt on each move, so any engine works over
HTTP, WebSockets or tests without pickling.
"""

import random

SUITS = "SHDC"          # Spades, Hearts, Diamonds, Clubs
RANKS = "23456789TJQKA" # T=10, A high
RANK_VALUE = {r: i + 2 for i, r in enumerate(RANKS)}  # 2..14
VALUE_RANK = {v: r for r, v in RANK_VALUE.items()}
SUIT_SYMBOL = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}


def full_deck():
    return [s + r for s in SUITS for r in RANKS]


def rank_val(card):
    return RANK_VALUE[card[1]]


def suit_of(card):
    return card[0]


def pretty(card):
    return SUIT_SYMBOL[card[0]] + card[1]


def new_rng(seed=None):
    return random.Random(seed)


class BaseCardGame:
    """Subclasses declare a `slug`, player bounds and implement
    `create`, `view`, `legal_actions`, `apply`, `is_over`, `finish_order`."""

    slug = ""
    min_players = 2
    max_players = 2
    real_time = False
    display_name = ""
    rules = ""

    def __init__(self, state):
        self.state = state

    # -- lifecycle -----------------------------------------------------
    @classmethod
    def create(cls, players, seed=None):
        raise NotImplementedError

    @classmethod
    def from_state(cls, state):
        return cls(state)

    # -- interaction ---------------------------------------------------
    def view(self, seat):
        """Private view for a seat (or None for a spectator)."""
        raise NotImplementedError

    def legal_actions(self, seat):
        return []

    def apply(self, seat, action):
        raise NotImplementedError

    # -- settlement ----------------------------------------------------
    def is_over(self):
        return bool(self.state.get("over"))

    def finish_order(self):
        """Seat indexes ordered best-first. Used for winner-takes-all."""
        return list(self.state.get("finish", []))

    def scores(self):
        return self.state.get("scores", {})

    def prize_positions(self):
        """How many top finishers share the pot (1 = winner takes all)."""
        return 1

    def game_log(self):
        return self.state.get("log", [])

    # -- helpers -------------------------------------------------------
    @staticmethod
    def _finish(state, seat):
        if seat not in state["finish"]:
            state["finish"].append(seat)
        if not state.get("winner"):
            state["winner"] = seat

    @staticmethod
    def _say(state, seat, text):
        state.setdefault("log", []).append({"seat": seat, "text": text})
        state["log"] = state["log"][-60:]

    @staticmethod
    def _next(state, seat, step=1):
        n = len(state["players"])
        done = set(state.get("finished_seats", [])) | set(state.get("finish", []))
        for i in range(1, n + 1):
            cand = (seat + step * i) % n
            if cand not in done:
                return cand
        return seat

    @staticmethod
    def _require_turn(state, seat, real_time=False):
        if real_time:
            return
        if state.get("over"):
            raise IllegalMove("Game is over")
        if seat != state.get("turn"):
            raise NotYourTurn("It is not your turn")

    @staticmethod
    def _legal_card_moves(seat, hand, predicate):
        return [{"action": "play", "card": c} for c in hand if predicate(c)]


from models.card_club.errors import IllegalMove, NotYourTurn  # noqa: E402
