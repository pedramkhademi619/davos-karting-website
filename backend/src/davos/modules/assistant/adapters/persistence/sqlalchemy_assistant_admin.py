from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ColumnElement, Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.adapters.persistence.answer_cache_entry_model import AnswerCacheEntryModel
from davos.modules.assistant.adapters.persistence.assistant_interaction_model import AssistantInteractionModel
from davos.modules.assistant.adapters.persistence.knowledge_entry_model import KnowledgeEntryModel
from davos.modules.assistant.application.ports.assistant_admin_port import AssistantAdminPort
from davos.modules.assistant.application.ports.cached_answer_page import CachedAnswerPage
from davos.modules.assistant.application.ports.interaction_page import InteractionPage
from davos.modules.assistant.domain.value_objects.assistant_overview import AssistantOverview
from davos.modules.assistant.domain.value_objects.cached_answer_record import CachedAnswerRecord
from davos.modules.assistant.domain.value_objects.curated_answer import CURATED_FINGERPRINT
from davos.modules.assistant.domain.value_objects.reviewed_interaction import ReviewedInteraction

_I = AssistantInteractionModel
_C = AnswerCacheEntryModel


class SqlAlchemyAssistantAdmin(AssistantAdminPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def overview(self, *, since: datetime, days: int) -> AssistantOverview:
        in_period = _I.occurred_at >= since
        async with self._session_factory() as session:
            outcomes = (
                await session.execute(select(_I.outcome, func.count()).where(in_period).group_by(_I.outcome))
            ).all()
            totals = (
                await session.execute(
                    select(
                        func.count().filter(_I.served_from_cache),
                        func.count().filter(_I.helpful.is_(True)),
                        func.count().filter(_I.helpful.is_(False)),
                        func.coalesce(func.sum(_I.prompt_tokens), 0),
                        func.coalesce(func.sum(_I.completion_tokens), 0),
                    ).where(in_period)
                )
            ).one()
            cache = (await session.execute(select(func.count(), func.count().filter(_C.is_active)))).one()
            entries = (await session.execute(select(func.count()).select_from(KnowledgeEntryModel))).scalar_one()
        by_outcome = {outcome: int(count) for outcome, count in outcomes}
        return AssistantOverview(
            days=days,
            questions=sum(by_outcome.values()),
            by_outcome=by_outcome,
            served_from_cache=int(totals[0]),
            helpful_votes=int(totals[1]),
            not_helpful_votes=int(totals[2]),
            prompt_tokens=int(totals[3]),
            completion_tokens=int(totals[4]),
            cached_answers_active=int(cache[1]),
            cached_answers_total=int(cache[0]),
            knowledge_entries=int(entries),
        )

    async def interactions(
        self, *, outcomes: list[str], helpful: bool | None, with_text_only: bool, offset: int, limit: int
    ) -> InteractionPage:
        where = []
        if outcomes:
            where.append(_I.outcome.in_(outcomes))
        if helpful is not None:
            where.append(_I.helpful.is_(helpful))
        if with_text_only:
            where.append(_I.question_text.is_not(None))
        async with self._session_factory() as session:
            total = (await session.execute(select(func.count()).select_from(_I).where(*where))).scalar_one()
            rows = (
                await session.scalars(
                    select(_I).where(*where).order_by(_I.occurred_at.desc()).offset(offset).limit(limit)
                )
            ).all()
        items = [
            ReviewedInteraction(
                interaction_id=row.id,
                occurred_at=row.occurred_at,
                outcome=row.outcome,
                question_text=row.question_text,
                answer_text=row.answer_text,
                helpful=row.helpful,
                served_from_cache=row.served_from_cache,
                tokens=row.prompt_tokens + row.completion_tokens,
            )
            for row in rows
        ]
        return InteractionPage(items=items, total=int(total))

    async def cached_answers(
        self, *, active: bool | None, offset: int, limit: int, entry_id: uuid.UUID | None = None
    ) -> CachedAnswerPage:
        where: list[ColumnElement[bool]] = [] if active is None else [_C.is_active.is_(active)]
        if entry_id is not None:
            where.append(_C.id == entry_id)
        columns: Select[tuple[_C]] = select(_C).where(*where)
        async with self._session_factory() as session:
            total = (await session.execute(select(func.count()).select_from(_C).where(*where))).scalar_one()
            rows = (
                await session.scalars(
                    columns.order_by(_C.hit_count.desc(), _C.created_at.desc()).offset(offset).limit(limit)
                )
            ).all()
        items = [
            CachedAnswerRecord(
                entry_id=row.id,
                question=row.original_query,
                answer=row.response,
                hit_count=row.hit_count,
                is_active=row.is_active,
                is_curated=row.fingerprint == CURATED_FINGERPRINT,
                created_at=row.created_at,
                last_used_at=row.last_used_at,
            )
            for row in rows
        ]
        return CachedAnswerPage(items=items, total=int(total))

    async def set_cached_answer_active(self, entry_id: uuid.UUID, *, active: bool) -> bool:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(update(_C).where(_C.id == entry_id).values(is_active=active))
            return bool(result.rowcount)  # type: ignore[attr-defined]

    async def delete_cached_answer(self, entry_id: uuid.UUID) -> bool:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(delete(_C).where(_C.id == entry_id))
            return bool(result.rowcount)  # type: ignore[attr-defined]
