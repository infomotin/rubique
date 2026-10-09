"""Game catalogue: slug -> engine metadata (player ranges, real-time flags)."""

from models.card_club.engines.shedding import (
    Blitz, Cheat, FanTan, Mao, Palace, President, RanterGoRound,
)
from models.card_club.engines.realtime import EgyptianRatscrew, Speed, Spoons
from models.card_club.engines.tricks import KnockOutWhist
from models.card_club.engines.rummy import Rummy
from models.card_club.engines.scopa import Scopa
from models.card_club.engines.strategy import GOPS, Golf

ENGINES = [
    Blitz, Cheat, EgyptianRatscrew, FanTan, Golf, GOPS, KnockOutWhist,
    Mao, Palace, President, RanterGoRound, Rummy, Scopa, Speed, Spoons,
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

# Spec order for listings: Blitz ... Spoons
SPEC_ORDER = [
    "blitz", "cheat", "ers", "fantan", "golf", "gops", "knockout_whist",
    "mao", "palace", "president", "rantergoround", "rummy", "scopa",
    "speed", "spoons",
]


def ordered_catalog():
    return [CATALOG[s] for s in SPEC_ORDER if s in CATALOG]
