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

CATALOG = {
    cls.slug: {
        "slug": cls.slug,
        "name": cls.display_name,
        "min": cls.min_players,
        "max": cls.max_players,
        "real_time": cls.real_time,
        "rules": cls.rules,
        "cls": cls,
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
