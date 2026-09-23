from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update

from davos.modules.identity.adapters.persistence.otp_challenge_mapper import OtpChallengeMapper
from davos.modules.identity.adapters.persistence.otp_challenge_model import OtpChallengeModel
from davos.modules.identity.application.ports.otp_challenge_repository import OtpChallengeRepository
from davos.modules.identity.domain.entities.otp_challenge import OtpChallenge
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyOtpChallengeRepository(OtpChallengeRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, challenge: OtpChallenge) -> None:
        self._uow.session.add(OtpChallengeMapper.to_model(challenge))
        await self._uow.session.flush()

    async def supersede_active_for(self, mobile: str, now: datetime) -> None:
        await self._uow.session.execute(
            update(OtpChallengeModel)
            .where(
                OtpChallengeModel.mobile == mobile,
                OtpChallengeModel.consumed_at.is_(None),
                OtpChallengeModel.superseded_at.is_(None),
            )
            .values(superseded_at=now)
        )

    async def latest_created_at(self, mobile: str) -> datetime | None:
        result = await self._uow.session.execute(
            select(func.max(OtpChallengeModel.created_at)).where(OtpChallengeModel.mobile == mobile)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_update(self, mobile: str) -> OtpChallenge | None:
        result = await self._uow.session.execute(
            select(OtpChallengeModel)
            .where(OtpChallengeModel.mobile == mobile)
            .order_by(OtpChallengeModel.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        return OtpChallengeMapper.to_domain(model) if model else None

    async def save(self, challenge: OtpChallenge) -> None:
        await self._uow.session.execute(
            update(OtpChallengeModel)
            .where(OtpChallengeModel.id == challenge.id)
            .values(
                attempts=challenge.attempts,
                consumed_at=challenge.consumed_at,
                superseded_at=challenge.superseded_at,
            )
        )
