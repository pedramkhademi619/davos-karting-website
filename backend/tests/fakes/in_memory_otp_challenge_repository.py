from __future__ import annotations

from datetime import datetime

from davos.modules.identity.application.ports.otp_challenge_repository import OtpChallengeRepository
from davos.modules.identity.domain.entities.otp_challenge import OtpChallenge


class InMemoryOtpChallengeRepository(OtpChallengeRepository):
    def __init__(self) -> None:
        self.items: list[OtpChallenge] = []

    async def add(self, challenge: OtpChallenge) -> None:
        self.items.append(challenge)

    async def supersede_active_for(self, mobile: str, now: datetime) -> None:
        for item in self.items:
            if item.mobile == mobile:
                item.supersede(now)

    async def latest_created_at(self, mobile: str) -> datetime | None:
        created = [i.created_at for i in self.items if i.mobile == mobile]
        return max(created) if created else None

    async def get_latest_for_update(self, mobile: str) -> OtpChallenge | None:
        matching = [i for i in self.items if i.mobile == mobile]
        return max(matching, key=lambda i: i.created_at) if matching else None

    async def save(self, challenge: OtpChallenge) -> None:
        return None
