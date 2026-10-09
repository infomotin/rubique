"""Card Club shared exceptions."""


class CardClubError(Exception):
    """Base error for Card Club operations."""


class PermissionDenied(CardClubError):
    """User lacks the required role in the group."""


class AgeGateError(CardClubError):
    """User has not passed the 18+ self-declared DOB gate."""


class NotFoundError(CardClubError):
    """Requested resource does not exist or is invisible to this user."""


class InsufficientFunds(CardClubError):
    """Wallet balance is below the required amount."""


class PoolUnderfunded(CardClubError):
    """Group pool cannot cover its bonus obligation (hard fail, nothing changes)."""


class ZeroSumViolation(CardClubError):
    """Payout schedule does not exactly match pot + pool bonus."""


class MintBlocked(CardClubError):
    """Minting is forbidden while a table is in play."""


class EngineError(CardClubError):
    """Game engine rejected the action."""


class IllegalMove(EngineError):
    """Move is not legal in the current game state."""


class NotYourTurn(EngineError):
    """Action attempted out of turn in a turn-based game."""
