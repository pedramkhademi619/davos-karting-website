from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.errors.invalid_points_entry_error import InvalidPointsEntryError

K = PointsEntryKind


@dataclass(frozen=True)
class PointsEntry:
    """One immutable line of the points ledger. Balances are always derived from entries, never stored.

    ``source_ref`` identifies the verified business event (booking id, payment id, referral id...) so
    processing the same event twice can never grant twice. Corrections are new REVERSAL/ADJUST lines.
    """

    entry_id: uuid.UUID
    customer_id: uuid.UUID
    delta: int
    kind: PointsEntryKind
    source_ref: str
    reason: str
    created_at: datetime
    expires_at: datetime | None = None
    reverses_kind: PointsEntryKind | None = None

    def __post_init__(self) -> None:
        if self.delta == 0:
            raise InvalidPointsEntryError("مقدار امتیاز نمی‌تواند صفر باشد.")
        if not self.source_ref.strip():
            raise InvalidPointsEntryError("منبع رویداد امتیاز الزامی است.")
        if self.kind is K.EARN and self.delta < 0:
            raise InvalidPointsEntryError("امتیاز کسب‌شده باید مثبت باشد.")
        if self.kind in {K.SPEND, K.EXPIRE} and self.delta > 0:
            raise InvalidPointsEntryError("مصرف یا انقضای امتیاز باید منفی باشد.")
        if self.kind is K.ADJUST and not self.reason.strip():
            raise InvalidPointsEntryError("برای اصلاح دستی امتیاز ذکر دلیل الزامی است.")
        if self.kind is K.REVERSAL and self.reverses_kind is None:
            raise InvalidPointsEntryError("ابطال باید نوع تراکنش اصلی را مشخص کند.")
        if self.expires_at is not None and self.kind is not K.EARN:
            raise InvalidPointsEntryError("فقط امتیاز کسب‌شده تاریخ انقضا دارد.")
