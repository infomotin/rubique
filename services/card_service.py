"""
CubePermutation AI - Card Club Domain Service
=============================================
Encapsulates private card table lifecycle, simulated token escrow, ledger verification,
and 15 classic game engines orchestration.

Easy Description:
- Coordinates card game tables (Call Break, Hazari, 29, Teen Patti, Blackjack, Texas Hold'em, etc.).
- Verifies player coin balances, manages table bets, and settles payouts accurately.
- Enforces strict zero-sum ledger invariants so coins cannot be duplicated or lost.
"""

from typing import Dict, Any, Optional, Tuple
from models.card_club import economy, groups, gameplay
from models.user_model import UserModel


class CardService:
    """
    Card Club Gaming & Ledger Domain Service
    """

    @staticmethod
    def get_wallet_overview(user_id: int) -> Dict[str, Any]:
        """
        Retrieves user personal balance, active escrow bets, and group balances.

        Easy Description:
        Retrieves the player's wallet balance, pending bets, and club funds.
        """
        return economy.balances_view(user_id)

    @staticmethod
    def fund_group_wallet(user_id: int, group_id: int, amount: int) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Transfers coins from personal wallet into a private card club group wallet.

        Easy Description:
        Moves coins from the member's wallet into their card club table bank.
        """
        if amount <= 0:
            return False, {}, "Funding amount must be greater than zero."

        try:
            ok, msg = economy.fund_group_wallet(user_id, group_id, amount)
            if not ok:
                return False, {}, msg
            return True, {"ok": True, "message": msg}, None
        except Exception as e:
            return False, {}, str(e)

    @staticmethod
    def verify_ledger_invariants() -> Dict[str, Any]:
        """
        Verifies cryptographically hash-chained ledger and 1 Billion coin supply invariant.

        Easy Description:
        Verifies that every coin in the economy matches the fixed reserve without any inflation.
        """
        return economy.verify_ledger()
