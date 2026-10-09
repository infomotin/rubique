"""Shedding-type engines: Blitz, Cheat, Fan Tan, Mao, Palace, President,
Ranter-Go-Round. House rules are documented in each class `rules` string."""

import random

from models.card_club.errors import IllegalMove, NotYourTurn
from models.card_club.engines.base import (
    BaseCardGame, full_deck, rank_val, suit_of, RANK_VALUE, VALUE_RANK,
)


def _deal(seeded, count, players):
    deck = full_deck()
    seeded.shuffle(deck)
    hands = {i: [] for i in range(len(players))}
    for _ in range(count):
        for i in range(len(players)):
            if deck:
                hands[i].append(deck.pop())
    return hands, deck


class Blitz(BaseCardGame):
    """Crazy-Eights race (2-12). Same suit/rank as discard, 8 = wild (caller
    names suit), 2 makes next draw 2, Q reverses (skip in heads-up)."""

    slug = "blitz"
    display_name = "Blitz"
    min_players, max_players = 2, 12
    rules = ("Deal 5 each. Follow suit or rank of the discard; 8 is wild and "
             "the player names a suit. 2 forces the next player to draw 2 "
             "(one 8 cancels it). Q reverses direction (acts as skip heads-up). "
             "Empty your hand first to win.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        hands, deck = _deal(rng, 5, players)
        first = deck.pop()
        while first[1] == "8":          # never start on a wild
            deck.insert(0, first)
            rng.shuffle(deck)
            first = deck.pop()
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "draw": deck, "discard": [first], "dir": 1, "turn": 0,
            "pending_draw": 0, "passes": 0, "finish": [], "log": [], "over": False,
        }

    def _top(self):
        return self.state["discard"][-1]

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "dir": s["dir"], "finish": s["finish"], "over": s["over"],
            "top": self._top(), "draw_count": len(s["draw"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "pending_draw": s["pending_draw"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if seat != s["turn"] or s["over"]:
            return []
        top = self._top()
        acts = []
        for c in s["hands"][str(seat)]:
            if c[1] == "8" or c[1] == top[1] or suit_of(c) == suit_of(top):
                acts.append({"action": "play", "card": c, "suit": None})
        acts.append({"action": "draw"})
        if s["pending_draw"] == 0 and not s["draw"] and not acts[:-1]:
            acts.append({"action": "pass"})
        return acts

    def apply(self, seat, action):
        s = self.state
        self._require_turn(s, seat)
        act = action.get("action")
        if act == "play":
            card = action.get("card")
            hands, top = s["hands"][str(seat)], self._top()
            if card not in hands:
                raise IllegalMove("You do not hold that card")
            if s["pending_draw"] and card[1] != "8":
                raise IllegalMove("Only an 8 cancels a pending draw")
            if card[1] != "8" and card[1] != top[1] and suit_of(card) != suit_of(top):
                raise IllegalMove("Card does not match rank or suit")
            named = action.get("suit")
            if card[1] == "8" and named not in "SHDC":
                raise IllegalMove("Declare the suit for an 8")
            hands.remove(card)
            s["discard"].append(card)
            s["pending_draw"] = 0 if card[1] == "8" else s["pending_draw"]
            s["passes"] = 0
            self._say(s, seat, f"played {card}")
            if not hands:
                self._finish(s, seat)
                s["over"] = True
                s["finish"] = [seat] + [i for i in range(len(s["players"]))
                                        if i != seat]
                s["turn"] = -1
                return
            nxt = self._next(s, seat, s["dir"])
            if card[1] == "2":
                s["pending_draw"] += 2
            elif card[1] == "8":
                nxt = self._next(s, nxt, s["dir"])
            elif card[1] == "Q":
                if len(s["players"]) == 2:
                    nxt = self._next(s, nxt, s["dir"])
                else:
                    s["dir"] *= -1
            s["turn"] = nxt
        elif act == "draw":
            if s["pending_draw"]:
                n = s["pending_draw"]
                for _ in range(n):
                    if s["draw"]:
                        s["hands"][str(seat)].append(s["draw"].pop())
                s["pending_draw"] = 0
                self._say(s, seat, f"drew {n}")
            else:
                if not s["draw"]:
                    raise IllegalMove("Draw pile is empty")
                s["hands"][str(seat)].append(s["draw"].pop())
                self._say(s, seat, "drew 1")
            s["turn"] = self._next(s, seat, s["dir"])
        elif act == "pass":
            if s["pending_draw"] or s["draw"]:
                raise IllegalMove("You must draw")
            s["passes"] += 1
            s["turn"] = self._next(s, seat, s["dir"])
            if s["passes"] >= len(s["players"]) * 2:
                s["finish"] = sorted(range(len(s["players"])),
                                     key=lambda i: len(s["hands"][str(i)]))
                s["over"] = True
                s["turn"] = -1
        else:
            raise IllegalMove("Unknown action")


class Cheat(BaseCardGame):
    """Cheat / Bullshit (3-13). Declare N cards face-down as the current rank;
    the next player may challenge. Lying puts the pile on the liar."""

    slug = "cheat"
    display_name = "Cheat"
    min_players, max_players = 3, 13
    rules = ("Deal all cards. Rank cycle A,2,...,K repeats. On your turn "
             "declare 1+ cards as the current rank (bluffing allowed) or "
             "challenge the previous declaration. Liar takes the pile, honest "
             "declaration makes the challenger take it. Empty your hand and "
             "survive the next player's turn to win.")

    RANK_ORDER = list(RANK_VALUE.keys())

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
            "turn": 0, "rank_idx": 0, "pile": [], "declared": None,
            "empty_pending": None, "turns": 0, "finish": [], "log": [],
            "over": False,
        }

    @property
    def _rank(self):
        return self.RANK_ORDER[self.state["rank_idx"] % 13]

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "rank": self._rank, "declared": s["declared"],
            "pile_count": len(s["pile"]), "finish": s["finish"], "over": s["over"],
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if seat != s["turn"] or s["over"]:
            return []
        acts = [{"action": "declare", "count": k} for k in range(1, len(s["hands"][str(seat)]) + 1)]
        if s["declared"] and s["declared"]["seat"] != seat:
            acts.append({"action": "challenge"})
        return acts

    def apply(self, seat, action):
        s = self.state
        self._require_turn(s, seat)
        act = action.get("action")
        if act == "challenge":
            decl = s["declared"]
            if not decl or decl["seat"] == seat:
                raise IllegalMove("Nothing to challenge")
            liar = not all(c[1] == decl["rank"] for c in decl["cards"])
            if liar:
                s["hands"][str(decl["seat"])] += s["pile"]
                self._say(s, seat, f"caught {s['players'][decl['seat']]} cheating")
                loser = decl["seat"]
            else:
                s["hands"][str(seat)] += s["pile"]
                self._say(s, seat, "wrong challenge - takes the pile")
                loser = seat
            s["pile"] = []
            s["declared"] = None
            if not s["hands"][str(loser)] and s["empty_pending"] == loser:
                self._finish(s, loser)
            s["empty_pending"] = None
            s["turn"] = self._next(s, loser)
            if len(s["finish"]) == len(s["players"]) - 1:
                self._close(s)
            return
        if act == "declare":
            hands, n = s["hands"][str(seat)], action.get("count")
            if not isinstance(n, int) or n < 1 or n > len(hands):
                raise IllegalMove("Bad declaration count")
            prev_empty = s["empty_pending"]
            cards = []
            for _ in range(n):
                cards.append(hands.pop(0))
            s["pile"] += cards
            decl = {"seat": seat, "rank": self._rank, "cards": cards,
                    "honest": all(c[1] == self._rank for c in cards)}
            s["declared"] = decl
            s["rank_idx"] += 1
            self._say(s, seat, f"declared {n} x {decl['rank']}")
            s["turns"] += 1
            if s["turns"] > len(s["players"]) * 60:
                order = sorted(range(len(s["players"])),
                               key=lambda i: (len(s["hands"][str(i)]), i))
                s["finish"] = order
                s["over"] = True
                s["turn"] = -1
                self._say(s, None, "stalemate - fewest cards win")
                return
            if not hands and s["empty_pending"] is None:
                s["empty_pending"] = seat
            elif hands and s["empty_pending"] == seat:
                s["empty_pending"] = None
            s["turn"] = self._next(s, seat)
            # Previous seat emptied and we declared instead of challenging: out.
            if prev_empty is not None and prev_empty != seat:
                self._finish(s, prev_empty)
                s["empty_pending"] = None
                if len(s["finish"]) == len(s["players"]) - 1:
                    self._close(s)
            return
        raise IllegalMove("Unknown action")

    def _close(self, s):
        for i in range(len(s["players"])):
            if i not in s["finish"]:
                s["finish"].append(i)
        s["over"] = True
        s["turn"] = -1

    def finish_order(self):
        return list(self.state.get("finish", []))


class FanTan(BaseCardGame):
    """Fan Tan / Sevens (3-6). Build each suit up and down from the 7."""

    slug = "fantan"
    display_name = "Fan Tan"
    min_players, max_players = 3, 6
    rules = ("Deal 7 each plus a stock. Play a 7 to open its column, then "
             "extend each suit up (8,9,...) or down (6,5,...) from its ends. "
             "No play? Draw from the stock (or pass when it is empty). First "
             "to empty their hand wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        hands, deck = _deal(rng, 7, players)
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "stock": deck, "cols": {s: {"lo": None, "hi": None} for s in "SHDC"},
            "turn": 0, "finish": [], "log": [], "over": False, "passes": 0,
        }

    def _playable(self, seat):
        s = self.state
        out = []
        for c in s["hands"][str(seat)]:
            col = s["cols"][suit_of(c)]
            v = rank_val(c)
            if c[1] == "7":
                out.append(c)
            elif col["lo"] is None and col["hi"] is None:
                continue
            elif col["lo"] is not None and v == col["lo"] - 1:
                out.append(c)
            elif col["hi"] is not None and v == col["hi"] + 1:
                out.append(c)
        return out

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "cols": s["cols"], "stock_count": len(s["stock"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if seat != s["turn"] or s["over"]:
            return []
        acts = [{"action": "play", "card": c} for c in self._playable(seat)]
        acts.append({"action": "draw" if s["stock"] else "pass"})
        return acts

    def apply(self, seat, action):
        s = self.state
        self._require_turn(s, seat)
        act = action.get("action")
        if act == "play":
            card = action.get("card")
            if card not in s["hands"][str(seat)]:
                raise IllegalMove("You do not hold that card")
            if card not in self._playable(seat):
                raise IllegalMove("Card cannot extend a column")
            s["hands"][str(seat)].remove(card)
            col = s["cols"][suit_of(card)]
            if card[1] == "7":
                col["lo"] = col["hi"] = 7
            elif col["lo"] is not None and rank_val(card) == col["lo"] - 1:
                col["lo"] -= 1
            else:
                col["hi"] += 1
            self._say(s, seat, f"played {card}")
            s["passes"] = 0
            if not s["hands"][str(seat)]:
                self._finish(s, seat)
                s["finish"] += [i for i in range(len(s["players"])) if i != seat]
                s["over"] = True
                s["turn"] = -1
                return
            s["turn"] = self._next(s, seat)
        elif act == "draw":
            if not s["stock"]:
                raise IllegalMove("Stock is empty")
            s["hands"][str(seat)].append(s["stock"].pop())
            s["turn"] = self._next(s, seat)
        elif act == "pass":
            if s["stock"] or self._playable(seat):
                raise IllegalMove("You must play or draw")
            s["passes"] += 1
            s["turn"] = self._next(s, seat)
            if s["passes"] >= len(s["players"]) * 2:
                order = sorted(range(len(s["players"])),
                               key=lambda i: len(s["hands"][str(i)]))
                s["finish"] = order
                s["over"] = True
                s["turn"] = -1
        else:
            raise IllegalMove("Unknown action")


class Mao(BaseCardGame):
    """Mao (2-7). Same suit or rank as the discard, otherwise draw one."""

    slug = "mao"
    display_name = "Mao"
    min_players, max_players = 2, 7
    rules = ("Deal 5 each; top card starts the discard. Match suit or rank of "
             "the discard exactly; if you cannot (or choose not to), draw one "
             "and pass. Illegal plays are refused by the dealer (server). "
             "First to empty wins. The other rules of Mao are not to be "
             "spoken.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        hands, deck = _deal(rng, 5, players)
        first = deck.pop()
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "stock": deck, "discard": [first], "turn": 0,
            "finish": [], "log": [], "over": False, "passes": 0,
        }

    def _playable(self, seat):
        top = self.state["discard"][-1]
        return [c for c in self.state["hands"][str(seat)]
                if c[1] == top[1] or suit_of(c) == suit_of(top)]

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "top": s["discard"][-1], "stock_count": len(s["stock"]),
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if seat != s["turn"] or s["over"]:
            return []
        acts = [{"action": "play", "card": c} for c in self._playable(seat)]
        if s["stock"]:
            acts.append({"action": "draw"})
        else:
            acts.append({"action": "pass"})
        return acts

    def apply(self, seat, action):
        s = self.state
        self._require_turn(s, seat)
        act = action.get("action")
        if act == "play":
            card = action.get("card")
            if card not in s["hands"][str(seat)]:
                raise IllegalMove("You do not hold that card")
            if card not in self._playable(seat):
                raise IllegalMove("Play refused: match suit or rank")
            s["hands"][str(seat)].remove(card)
            s["discard"].append(card)
            s["passes"] = 0
            self._say(s, seat, f"played {card}")
            if not s["hands"][str(seat)]:
                self._finish(s, seat)
                s["finish"] += [i for i in range(len(s["players"])) if i != seat]
                s["over"] = True
                s["turn"] = -1
                return
            s["turn"] = self._next(s, seat)
        elif act == "draw":
            if not s["stock"]:
                raise IllegalMove("Stock is empty")
            s["hands"][str(seat)].append(s["stock"].pop())
            s["passes"] = 0
            s["turn"] = self._next(s, seat)
        elif act == "pass":
            if s["stock"]:
                raise IllegalMove("You must draw")
            s["passes"] += 1
            s["turn"] = self._next(s, seat)
            if s["passes"] >= len(s["players"]) * 3:
                s["finish"] = sorted(
                    range(len(s["players"])),
                    key=lambda i: len(s["hands"][str(i)]))
                s["over"] = True
                s["turn"] = -1
        else:
            raise IllegalMove("Unknown action")


class Palace(BaseCardGame):
    """Palace / Shithead (2-6). Clear hand, then face-up, then flip blind."""

    slug = "palace"
    display_name = "Palace"
    min_players, max_players = 2, 6
    rules = ("Deal 3 face-down, 3 face-up on top, remainder to hand (A low, K "
             "high). Play a card of equal or lower rank than the discard top; "
             "no play means pick the pile up. Clear your hand, then your "
             "face-up cards, then flip the face-down stack blind - an illegal "
             "flip picks the pile up. Clear all six palace cards to win.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        hand_n = max(1, (52 - 6 * n) // n)
        deck = full_deck()
        rng.shuffle(deck)
        zones = {}
        for i in range(n):
            down = [deck.pop() for _ in range(3)]
            up = [deck.pop() for _ in range(3)]
            hand = [deck.pop() for _ in range(min(hand_n, len(deck)))]
            zones[str(i)] = {"hand": hand, "up": up, "down": down}
        first = deck.pop() if deck else None
        return {
            "slug": cls.slug, "players": list(players), "zones": zones,
            "discard": [first] if first else [], "turn": 0, "pickups": 0,
            "finish": [], "log": [], "over": False,
        }

    def _own(self, seat):
        return self.state["zones"][str(seat)]

    def _available(self, seat):
        z = self._own(seat)
        if z["hand"]:
            return z["hand"], "hand"
        if z["up"]:
            return z["up"], "up"
        if z["down"]:
            return z["down"], "down"
        return [], None

    def _playable(self, seat):
        cards, zone = self._available(seat)
        if zone == "down":
            return []
        top = self.state["discard"][-1] if self.state["discard"] else None
        if top is None:
            return list(cards)
        return [c for c in cards if rank_val(c) <= rank_val(top)]

    def view(self, seat):
        s = self.state
        z = self._own(seat) if seat is not None else None
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "top": s["discard"][-1] if s["discard"] else None,
            "discard_count": len(s["discard"]),
            "finish": s["finish"], "over": s["over"],
            "zone": ({k: (list(v) if k != "down" else len(v))
                      for k, v in z.items()} if z else None),
            "others": {str(i): {"hand": len(self._own(i)["hand"]),
                                "up": len(self._own(i)["up"]),
                                "down": len(self._own(i)["down"])}
                       for i in range(len(s["players"]))},
            "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if seat != s["turn"] or s["over"]:
            return []
        acts = [{"action": "play", "card": c} for c in self._playable(seat)]
        cards, zone = self._available(seat)
        if zone == "down":
            acts.append({"action": "flip"})
        if zone and not acts:
            acts.append({"action": "pickup"})
        elif zone == "hand" and s["discard"] and not acts:
            acts.append({"action": "pickup"})
        return acts

    def apply(self, seat, action):
        s = self.state
        self._require_turn(s, seat)
        act = action.get("action")
        z = self._own(seat)
        if act == "play":
            card = action.get("card")
            cards, zone = self._available(seat)
            if zone == "down" or card not in cards:
                raise IllegalMove("Not playable from that zone")
            if s["discard"] and rank_val(card) > rank_val(s["discard"][-1]):
                raise IllegalMove("Card is higher than the discard top")
            cards.remove(card)
            s["discard"].append(card)
            self._say(s, seat, f"played {card} ({zone})")
        elif act == "flip":
            cards, zone = self._available(seat)
            if zone != "down":
                raise IllegalMove("Nothing to flip")
            card = cards.pop()
            if s["discard"] and rank_val(card) > rank_val(s["discard"][-1]):
                z["hand"] += s["discard"] + [card]
                s["discard"] = []
                self._say(s, seat, f"blind {card} illegal - picks the pile up")
            else:
                s["discard"].append(card)
                self._say(s, seat, f"flipped and played {card}")
        elif act == "pickup":
            if not s["discard"]:
                raise IllegalMove("Nothing to pick up")
            z["hand"] += s["discard"]
            s["discard"] = []
            s["pickups"] += 1
            self._say(s, seat, "picked up the pile")
            if s["pickups"] >= len(s["players"]) * 4:
                order = sorted(range(len(s["players"])),
                               key=lambda i: (len(self._own(i)["hand"]) +
                                              len(self._own(i)["up"]) +
                                              len(self._own(i)["down"]), i))
                s["finish"] = order
                s["over"] = True
                s["turn"] = -1
                self._say(s, None, "stalemate - fewest palace cards win")
                return
        else:
            raise IllegalMove("Unknown action")
        if not z["hand"] and not z["up"] and not z["down"]:
            self._finish(s, seat)
            s["finish"] += [i for i in range(len(s["players"])) if i != seat]
            s["over"] = True
            s["turn"] = -1
            return
        s["turn"] = self._next(s, seat)


class President(BaseCardGame):
    """President / Scum (3-16). Sets of equal cards; highest set wins the lead."""

    slug = "president"
    display_name = "President"
    min_players, max_players = 3, 16
    rules = ("Deal as evenly as the deck allows (A high). Lead any set of "
             "equal cards (1-4). Follow with the same size and a higher rank, "
             "a bomb (all four of a rank), or pass. When everyone passes the "
             "last winner leads again. First out is the President.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck()
        rng.shuffle(deck)
        base = len(deck) // n
        hands = {i: [deck.pop() for _ in range(base)] for i in range(n)}
        for extra in range(len(deck)):     # remainder to first seats in order
            hands[extra % n].append(deck.pop())
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): sorted(v, key=rank_val) for k, v in hands.items()},
            "turn": 0, "current": None, "leader": None, "passes": 0,
            "finish": [], "log": [], "over": False, "active": list(range(n)),
        }

    @staticmethod
    def _sets(hand):
        by_rank = {}
        for c in hand:
            by_rank.setdefault(c[1], []).append(c)
        out = []
        for r, cs in by_rank.items():
            for k in range(1, len(cs) + 1):
                out.append(cs[:k])
        return out

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "current": s["current"], "active": s["active"],
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "finish": s["finish"], "over": s["over"], "log": s["log"][-15:],
        }

    def legal_actions(self, seat):
        s = self.state
        if seat != s["turn"] or s["over"]:
            return []
        acts = []
        cur = s["current"]
        for set_cards in self._sets(s["hands"][str(seat)]):
            v = rank_val(set_cards[0])
            if cur is None:
                acts.append({"action": "play", "cards": list(set_cards)})
            elif len(set_cards) == len(cur["cards"]):
                if v > cur["value"]:
                    acts.append({"action": "play", "cards": list(set_cards)})
                elif len(set_cards) == 4 and v > cur["value"]:
                    acts.append({"action": "play", "cards": list(set_cards)})
            elif len(set_cards) == 4 and (cur["value"] is None or v > cur["value"] or len(cur["cards"]) != 4):
                acts.append({"action": "play", "cards": list(set_cards)})
        if s["current"] is not None:
            acts.append({"action": "pass"})
        return acts

    def apply(self, seat, action):
        s = self.state
        self._require_turn(s, seat)
        act = action.get("action")
        if act == "pass":
            if s["current"] is None:
                raise IllegalMove("You must lead a set")
            s["passes"] += 1
            nxt = self._next(s, seat)
            others = len(s["active"]) - 1
            if s["passes"] >= others and s["current"]:
                s["current"] = None
                s["passes"] = 0
                if seat == s["leader"] or s["leader"] not in s["active"]:
                    s["leader"] = nxt
                nxt = s["leader"]
                if nxt not in s["active"]:
                    nxt = nxt if nxt in s["active"] else s["active"][0]
            s["turn"] = nxt
            return
        if act == "play":
            cards = action.get("cards") or []
            hand = s["hands"][str(seat)]
            if not cards or any(c not in hand for c in cards):
                raise IllegalMove("You do not hold those cards")
            if len(set(c[1] for c in cards)) != 1:
                raise IllegalMove("A set must be one rank")
            cur = s["current"]
            v = rank_val(cards[0])
            n = len(cards)
            if cur is None:
                pass
            elif n == len(cur["cards"]) and v > cur["value"]:
                pass
            elif n == 4 and (len(cur["cards"]) != 4 or v > cur["value"]):
                pass
            else:
                raise IllegalMove("Must match size and beat the current set")
            for c in cards:
                hand.remove(c)
            s["current"] = {"cards": list(cards), "value": v, "seat": seat}
            s["leader"] = seat
            s["passes"] = 0
            self._say(s, seat, f"played {n} x {cards[0][1]}")
            if not hand:
                self._finish(s, seat)
                s["active"].remove(seat)
                if len(s["active"]) <= 1:
                    s["finish"] += s["active"]
                    s["over"] = True
                    s["turn"] = -1
                    return
            nxt = self._next(s, seat)
            s["turn"] = nxt
            return
        raise IllegalMove("Unknown action")


class RanterGoRound(BaseCardGame):
    """Ranter-Go-Round (3-12). Single-deal trick game, no trump; holder of
    the 2 of Diamonds leads the first trick; most tricks wins."""

    slug = "rantergoround"
    display_name = "Ranter-Go-Round"
    min_players, max_players = 3, 12
    rules = ("Deal the deck as evenly as possible. The holder of the 2 of "
             "Diamonds leads first. Follow suit if you can, otherwise play "
             "anything (no trump). Highest card of the led suit takes the "
             "trick and leads the next. Most tricks wins.")

    @classmethod
    def create(cls, players, seed=None):
        rng = random.Random(seed)
        n = len(players)
        deck = full_deck()
        rng.shuffle(deck)
        base = len(deck) // n
        hands = {i: [deck.pop() for _ in range(base)] for i in range(n)}
        leader = 0
        for i in range(n):
            if "D2" in hands[i]:
                leader = i
                break
        return {
            "slug": cls.slug, "players": list(players),
            "hands": {str(k): v for k, v in hands.items()},
            "tricks": {str(i): 0 for i in range(n)},
            "turn": leader, "lead_suit": None, "trick": [],
            "finish": [], "log": [], "over": False,
        }

    def view(self, seat):
        s = self.state
        return {
            "slug": s["slug"], "players": s["players"], "turn": s["turn"],
            "lead_suit": s["lead_suit"], "trick": s["trick"],
            "tricks": s["tricks"],
            "hand": list(s["hands"].get(str(seat), [])) if seat is not None else None,
            "counts": {str(k): len(v) for k, v in s["hands"].items()},
            "finish": s["finish"], "over": s["over"], "log": s["log"][-12:],
        }

    def legal_actions(self, seat):
        s = self.state
        if seat != s["turn"] or s["over"]:
            return []
        hand = s["hands"][str(seat)]
        if s["lead_suit"]:
            follows = [c for c in hand if suit_of(c) == s["lead_suit"]]
            if follows:
                return [{"action": "play", "card": c} for c in follows]
        return [{"action": "play", "card": c} for c in hand]

    def apply(self, seat, action):
        s = self.state
        self._require_turn(s, seat)
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
        if s["trick"]:
            s["lead_suit"] = s["lead_suit"] or suit_of(s["trick"][0]["card"])
        else:
            s["lead_suit"] = suit_of(card)
        s["trick"].append({"seat": seat, "card": card})
        if len(s["trick"]) == len(s["players"]):
            def strength(entry):
                c = entry["card"]
                return (1 if suit_of(c) == s["lead_suit"] else 0, rank_val(c))
            winner = max(s["trick"], key=strength)["seat"]
            s["tricks"][str(winner)] += 1
            self._say(s, winner, f"won the trick ({s['tricks'][str(winner)]})")
            s["trick"] = []
            s["lead_suit"] = None
            if all(not v for v in s["hands"].values()):
                order = sorted(range(len(s["players"])),
                               key=lambda i: -s["tricks"][str(i)])
                s["finish"] = order
                s["over"] = True
                s["turn"] = -1
                return
            s["turn"] = winner
        else:
            s["turn"] = self._next(s, seat)
