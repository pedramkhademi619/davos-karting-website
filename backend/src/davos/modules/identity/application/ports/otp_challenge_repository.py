from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.identity.domain.entities.otp_challenge import OtpChallenge


class OtpChallengeRepository(ABC):
    @abstractmethod
    async def add(self, challenge: OtpChallenge) -> None: ...

    @abstractmethod
    async def supersede_active_for(self, mobile: str, now: datetime) -> None:
        """Invalidate every unconsumed challenge of this mobile (a new code was issued)."""

    @abstractmethod
    async def latest_created_at(self, mobile: str) -> datetime | None: ...

    @abstractmethod
    async def get_latest_for_update(self, mobile: str) -> OtpChallenge | None:
        """Row-locked read so concurrent verifications cannot both consume one code."""

    @abstractmethod
    async def save(self, challenge: OtpChallenge) -> None: ...
