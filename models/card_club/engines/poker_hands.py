"""Standard 5-card poker hand evaluation for Texas Hold'em.

A hand is scored as a comparable tuple: (category, tiebreak1, tiebreak2, ...).
Higher tuples win, so `max()` over a list of scores decides the showdown for
any number of players (including exact ties that split the pot).

Categories (high -> low):
  8 straight flush   7 four of a kind   6 full house      5 flush
  4 straight         3 three of a kind  2 two pair        1 pair
  0 high card
"""

import itertools

from models.card_club.engines.base import RANK_VALUE


def _rank(card):
    return RANK_VALUE[card[1]]


def _straight_high(ranks):
    """High card of a straight, or None. Ace plays low for A-2-3-4-5."""
    uniq = sorted(set(ranks))
    if len(uniq) != 5:
        return None
    if uniq[4] - uniq[0] == 4:
        return uniq[4]
    if uniq == [2, 3, 4, 5, 14]:
        return 5
    return None


def evaluate_five(cards):
    """Score exactly five cards. Returns a comparable tuple."""
    if len(cards) != 5:
        raise ValueError("evaluate_five needs exactly 5 cards")
    ranks = [_rank(c) for c in cards]
    suits = [c[0] for c in cards]
    flush = len(set(suits)) == 1
    straight_high = _straight_high(ranks)

    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    # groups sorted by (count, rank) so kickers fall out naturally
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    shape = tuple(c for _, c in groups)
    order = tuple(r for r, _ in groups)

    if flush and straight_high:
        return (8, straight_high)
    if shape == (4, 1):
        return (7,) + order
    if shape == (3, 2):
        return (6,) + order
    if flush:
        return (5,) + tuple(sorted(ranks, reverse=True))
    if straight_high:
        return (4, straight_high)
    if shape == (3, 1, 1):
        return (3,) + order
    if shape == (2, 2, 1):
        return (2,) + order
    if shape == (2, 1, 1, 1):
        return (1,) + order
    return (0,) + tuple(sorted(ranks, reverse=True))


def evaluate_best(cards):
    """Best 5-card hand out of 5, 6 or 7 cards (hole + community cards)."""
    cards = list(cards)
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand")
    if len(cards) == 5:
        return evaluate_five(cards)
    best = None
    for combo in itertools.combinations(cards, 5):
        score = evaluate_five(combo)
        if best is None or score > best:
            best = score
    return best


HAND_NAMES = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Card",
}


def describe(score):
    return HAND_NAMES.get(score[0], "High Card")
