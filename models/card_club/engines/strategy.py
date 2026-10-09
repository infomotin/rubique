"""Strategy engines: GOPS (secret bidding) and Golf (grid scoring)."""

import random

from models.card_club.errors import IllegalMove
from models.card_club.engines.base import BaseCardGame, full_deck, rank_val, RANK_VALUE


class GOPS(BaseCardGame):
    """Game of Pure Strategy (exactly 2). Secret bids, prize cards 1-13."""

    slug = "gops"
    display_name = "GOPS"
    min_players, max_players = 2, 2
    rules = ("Both start 25 chips. Each trick reveals a prize card (values "
             "1-13, shuffled). Both secretly bid 0..remaining chips; higher "
             "bid wins the prize (ties split, odd pip to seat 0), and the "
             "prize value is added to the winner's score. Whoever leads after "
             "13 tricks wins. Internal chips are game points; coins settle "
             "at the table level.")

    START_CHIPS = 25

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        prizes = list(range(1, 14))
        rng.shuffle(prizes)
        return {
            "slug": cls.slug, "players": list(players), "prizes": prizes,
            "round": 0, "bids": {}, "chips": {str(i): cls.START_CHIPS for i in range(len(players))},
            "scores": {str(i): 0 for i in range(len(players))},
            "turn": None, "finish": [], "log": [], "over": False,
        }

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"],
            "prize": s["prizes"][s["round"]] if s["round"] < len(s["prizes"]) else None,
            "round": s["round"], "bids_made": sorted(s["bids"].keys()),
            "my_bid": s["bids"].get(str(seat)),
            "my_chips": s["chips"].get(str(seat)),
            "chips": dict(s["chips"]), "scores": dict(s["scores"]),
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or str(seat) in s["bids"] or s["round"] >= len(s["prizes"]):
            return []
        chips = s["chips"][str(seat)]
        return [{"action": "bid", "amount": k} for k in range(0, chips + 1)]

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        if action.get("action") != "bid":
            raise IllegalMove("Unknown action")
        if str(seat) in s["bids"]:
            raise IllegalMove("You already bid this trick")
        amount = action.get("amount")
        chips = s["chips"][str(seat)]
        if not isinstance(amount, int) or amount < 0 or amount > chips:
            raise IllegalMove("Bid must be between 0 and your chips")
        s["bids"][str(seat)] = amount
        if len(s["bids"]) < 2:
            return                                   # wait for the other seat
        a, b = int(s["bids"]["0"]), int(s["bids"]["1"])
        prize = s["prizes"][s["round"]]
        s["chips"]["0"] -= a
        s["chips"]["1"] -= b
        if a > b:
            s["scores"]["0"] += prize
            winner = 0
        elif b > a:
            s["scores"]["1"] += prize
            winner = 1
        else:                                        # split the prize
            s["scores"]["0"] += prize // 2
            s["scores"]["1"] += prize // 2
            s["scores"]["0"] += prize % 2             # odd pip to seat 0
            winner = None
        s["chips"]["0"] += a
        s["chips"]["1"] += b                          # refunds flow back
        self._say(s, winner, f"prize {prize}: bids {a}/{b}")
        s["bids"] = {}
        s["round"] += 1
        if s["round"] >= len(s["prizes"]):
            order = sorted(range(2), key=lambda i: -s["scores"][str(i)])
            best = s["scores"][str(order[0])]
            winners = [i for i in order if s["scores"][str(i)] == best]
            s["scores"]["_winners"] = winners
            s["finish"] = winners + [i for i in order if i not in winners]
            s["over"] = True

    def winners(self):
        w = self.state.get("scores", {}).get("_winners")
        return list(w) if w else list(self.state.get("finish", []))


class Golf(BaseCardGame):
    """Golf (2-6, 6-hole house variant). Lowest total grid score wins."""

    slug = "golf"
    display_name = "Golf"
    min_players, max_players = 2, 6
    HOLES = 6
    rules = ("Six-hole house Golf. Each hole deals a 2x3 grid per player plus "
             "a stock and one up-card. Draw from stock or take the up-card, "
             "swap one grid card (the replaced card becomes the up-card) or "
             "discard a stock draw. Hole ends when the stock dries up. "
             "Scoring: matching cards in a column cancel (0); A=1, 2-10 face, "
             "J=11, Q=12, K=0. Lowest 6-hole total wins; ties share.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        state = {
            "slug": cls.slug, "players": list(players),
            "hole": 0, "holes": cls.HOLES,
            "grids": {str(i): [] for i in range(n)},
            "stocks": {}, "up": [], "discard_top": None,
            "turn": 0, "totals": {str(i): 0 for i in range(n)},
            "hole_scores": {}, "finish": [], "log": [], "over": False,
        }
        obj = cls(state)
        obj._deal_hole(rng)
        return state

    @classmethod
    def _score_grid(cls, grid):
        cols = [(grid[c], grid[c + 3]) for c in range(3)]
        total = 0
        for a, b in cols:
            if a == b:
                continue
            def v(card):
                r = card[1]
                return 0 if r == "K" else 1 if r == "A" else \
                    11 if r == "J" else 12 if r == "Q" else RANK_VALUE[r]
            total += v(a) + v(b)
        return total

    def _deal_hole(self, rng=None):
        s = self.state
        rng = rng or random.Random()
        deck = full_deck()
        rng.shuffle(deck)
        for i in range(len(s["players"])):
            s["grids"][str(i)] = [deck.pop() for _ in range(6)]
        s["stocks"] = {str(i): [] for i in range(len(s["players"]))}
        s["up"] = [deck.pop()] if deck else []
        s["discard_top"] = deck.pop() if deck else None
        base = len(deck) // len(s["players"]) if s["players"] else 0
        for i in range(len(s["players"])):
            s["stocks"][str(i)] = [deck.pop() for _ in range(base)]
        while deck:
            s["stocks"]["0"].append(deck.pop())
        s["turn"] = 0

    def _draw_options(self, seat):
        """(source, card, options) - stock top or the up-card."""
        s = self.state
        stock = s["stocks"][str(seat)]
        opts = []
        if stock:
            opts.append(("stock", stock[-1]))
        if s["up"]:
            opts.append(("up", s["up"][-1]))
        return opts

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "hole": s["hole"] + 1, "holes": s["holes"],
            "grids": {k: list(v) for k, v in s["grids"].items()},
            "stocks": {k: len(v) for k, v in s["stocks"].items()},
            "up": list(s["up"]), "totals": dict(s["totals"]),
            "hole_scores": s["hole_scores"],
            "options": self._draw_options(seat) if seat is not None else [],
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if s["over"] or seat != s["turn"]:
            return []
        acts = []
        for source, card in self._draw_options(seat):
            for gi in range(6):
                acts.append({"action": "swap", "source": source, "grid_index": gi})
        if not acts:
            acts.append({"action": "end_hole"})
        return acts

    def apply(self, seat, action):
        s = self.state
        if s["over"]:
            raise IllegalMove("Game is over")
        if seat != s["turn"]:
            raise IllegalMove("Not your turn")
        act = action.get("action")
        if act == "end_hole":
            self._close_hole()
            return
        if act != "swap":
            raise IllegalMove("Unknown action")
        source, gi = action.get("source"), action.get("grid_index")
        if gi not in range(6):
            raise IllegalMove("Bad grid index")
        stock = s["stocks"][str(seat)]
        if source == "stock":
            if not stock:
                raise IllegalMove("Your stock is empty")
            taken = stock.pop()
        elif source == "up":
            if not s["up"]:
                raise IllegalMove("Up-card pile is empty")
            taken = s["up"].pop()
        else:
            raise IllegalMove("Bad source")
        grid = s["grids"][str(seat)]
        replaced = grid[gi]
        grid[gi] = taken
        s["up"].append(replaced)
        self._say(s, seat, f"{taken} into slot {gi + 1}")
        if not any(s["stocks"].values()):
            self._close_hole()
            return
        s["turn"] = self._next(s, seat)
        while not self._draw_options(s["turn"]) and not s["over"]:
            nxt = self._next(s, s["turn"])
            if nxt == s["turn"]:
                self._close_hole()
                break
            if not any(self._draw_options(i) for i in range(len(s["players"]))):
                self._close_hole()
                break
            s["turn"] = nxt

    def _close_hole(self):
        s = self.state
        for i in range(len(s["players"])):
            sc = self._score_grid(s["grids"][str(i)])
            s["totals"][str(i)] = s["totals"].get(str(i), 0) + sc
            s["hole_scores"].setdefault(str(s["hole"]), {})[str(i)] = sc
        self._say(s, None, f"hole {s['hole'] + 1} scored: "
                  f"{s['hole_scores'][str(s['hole'])]}")
        s["hole"] += 1
        if s["hole"] >= s["holes"]:
            order = sorted(range(len(s["players"])), key=lambda i: s["totals"][str(i)])
            best = s["totals"][str(order[0])]
            winners = [i for i in order if s["totals"][str(i)] == best]
            s["finish"] = winners + [i for i in order if i not in winners]
            s["scores"] = dict(s["totals"])
            s["over"] = True
            s["turn"] = -1
            return
        self._deal_hole(random.Random())

    def winners(self):
        return list(self.state.get("finish", []))
