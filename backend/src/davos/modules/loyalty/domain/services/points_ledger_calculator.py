from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind

K = PointsEntryKind


class PointsLedgerCalculator:
    """Pure functions over ledger entries."""

    @staticmethod
    def balance(entries: Iterable[PointsEntry]) -> int:
        return sum(e.delta for e in entries)

    @staticmethod
    def lifetime_earned(entries: Iterable[PointsEntry]) -> int:
        """Tier basis: points ever earned, minus earn reversals. Spending and expiry never lower a tier."""
        total = 0
        for e in entries:
            if e.kind is K.EARN or (e.kind is K.REVERSAL and e.reverses_kind is K.EARN):
                total += e.delta
        return max(total, 0)

    @staticmethod
    def expirable(entries: Iterable[PointsEntry], now: datetime) -> int:
        """Points that have passed their expiry and are still unspent.

        Spending consumes the oldest points first, which makes this equivalent to FIFO expiry:
        expired-earned minus everything already consumed (spent or expired), floored at zero and
        never more than the current balance.
        """
        entries = list(entries)
        expired_earned = sum(e.delta for e in entries if e.kind is K.EARN and e.expires_at and e.expires_at <= now)
        consumed = -sum(e.delta for e in entries if e.kind in {K.SPEND, K.EXPIRE})
        balance = sum(e.delta for e in entries)
        return max(min(expired_earned - consumed, balance), 0)

    @staticmethod
    def expiring_within(entries: Iterable[PointsEntry], now: datetime, horizon: datetime) -> int:
        """Unspent points that will expire between now and ``horizon`` (for the customer notice)."""
        entries = list(entries)
        return max(
            PointsLedgerCalculator.expirable(entries, horizon) - PointsLedgerCalculator.expirable(entries, now), 0
        )
