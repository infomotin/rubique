from models.card_club.engines.shedding import (
    Blitz, Cheat, FanTan, Mao, Palace, President, RanterGoRound,
)
from models.card_club.engines.realtime import EgyptianRatscrew, Speed, Spoons
from models.card_club.engines.tricks import KnockOutWhist
from models.card_club.engines.rummy import Rummy
from models.card_club.engines.scopa import Scopa
from models.card_club.engines.strategy import GOPS, Golf
from models.card_club.engines.popular_classics import (
    CallBreak, Hazari, TwentyNine, TeenPatti, ContractBridge,
    TexasHoldem, Blackjack, CrazyEights
)

ENGINES = [
    CallBreak, Hazari, TwentyNine, TeenPatti, Rummy, ContractBridge,
    TexasHoldem, Blackjack, President, Cheat, Speed, CrazyEights,
    Blitz, EgyptianRatscrew, FanTan, Golf, GOPS, KnockOutWhist,
    Mao, Palace, RanterGoRound, Scopa, Spoons,
]

GAME_MODES = {
    # 23 Games classified across Solo (Nije Nije), COM vs Person, and Multiplayer
    "call_break": {"modes": ["vs_com", "multiplayer"], "category": "Trick Taking", "badge": "Popular"},
    "hazari": {"modes": ["vs_com", "multiplayer"], "category": "1000-Point Partition", "badge": "Bangla Classic"},
    "29": {"modes": ["vs_com", "multiplayer"], "category": "Partnership Trick", "badge": "Hot"},
    "teen_patti": {"modes": ["vs_com", "multiplayer"], "category": "South Asian Poker", "badge": "VIP"},
    "rummy": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Meld & Sets", "badge": "Classic"},
    "bridge": {"modes": ["vs_com", "multiplayer"], "category": "Contract Trick", "badge": "Strategic"},
    "poker": {"modes": ["vs_com", "multiplayer"], "category": "Texas Hold'em", "badge": "Global"},
    "blackjack": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Casino 21", "badge": "Fast"},
    "president": {"modes": ["vs_com", "multiplayer"], "category": "Shedding / Hierarchy", "badge": "Party"},
    "cheat": {"modes": ["vs_com", "multiplayer"], "category": "Bluffing & Challenge", "badge": "Bluff"},
    "speed": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Real-time Shedding", "badge": "Live"},
    "crazy_eights": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Uno-style Action", "badge": "Fun"},
    "blitz": {"modes": ["solo", "multiplayer"], "category": "Speed Melding", "badge": "Speed"},
    "ers": {"modes": ["vs_com", "multiplayer"], "category": "Egyptian Ratscrew (Slap)", "badge": "Action"},
    "fantan": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Sevens / Layout", "badge": "Layout"},
    "golf": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Memory & Low Score", "badge": "Puzzle"},
    "gops": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Game of Pure Strategy", "badge": "Strategy"},
    "knockout_whist": {"modes": ["vs_com", "multiplayer"], "category": "Elimination Trick", "badge": "Knockout"},
    "mao": {"modes": ["vs_com", "multiplayer"], "category": "Secret Rule Shedding", "badge": "Mystery"},
    "palace": {"modes": ["vs_com", "multiplayer"], "category": "Tabletop Shedding", "badge": "Casual"},
    "rantergoround": {"modes": ["vs_com", "multiplayer"], "category": "Passing Elimination", "badge": "Family"},
    "scopa": {"modes": ["solo", "vs_com", "multiplayer"], "category": "Italian Sweeps", "badge": "Classic"},
    "spoons": {"modes": ["vs_com", "multiplayer"], "category": "Pass & Grab Spoons", "badge": "Party"},
}

CATALOG = {
    cls.slug: {
        "slug": cls.slug,
        "name": cls.display_name,
        "min": cls.min_players,
        "max": cls.max_players,
        "real_time": cls.real_time,
        "rules": cls.rules,
        "cls": cls,
        "modes": GAME_MODES.get(cls.slug, {}).get("modes", ["multiplayer"]),
        "category": GAME_MODES.get(cls.slug, {}).get("category", "Card Game"),
        "badge": GAME_MODES.get(cls.slug, {}).get("badge", "Card"),
        "supports_solo": "solo" in GAME_MODES.get(cls.slug, {}).get("modes", []),
        "supports_com": "vs_com" in GAME_MODES.get(cls.slug, {}).get("modes", []),
        "supports_multiplayer": "multiplayer" in GAME_MODES.get(cls.slug, {}).get("modes", []),
    }
    for cls in ENGINES
}

# Spec order for listings prioritizing the user's requested 12 games first
SPEC_ORDER = [
    "call_break", "hazari", "29", "teen_patti", "rummy", "bridge",
    "poker", "blackjack", "president", "cheat", "speed", "crazy_eights",
    "blitz", "ers", "fantan", "golf", "gops", "knockout_whist",
    "mao", "palace", "rantergoround", "scopa", "spoons",
]


def ordered_catalog():
    return [CATALOG[s] for s in SPEC_ORDER if s in CATALOG]

