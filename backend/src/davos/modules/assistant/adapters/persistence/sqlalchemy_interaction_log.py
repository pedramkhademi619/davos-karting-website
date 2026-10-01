from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.adapters.persistence.assistant_interaction_model import AssistantInteractionModel
from davos.modules.assistant.application.ports.feedback_recorded import FeedbackRecorded
from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.modules.assistant.domain.entities.assistant_interaction import AssistantInteraction


class SqlAlchemyInteractionLog(InteractionLogPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(self, interaction: AssistantInteraction) -> None:
        async with self._session_factory() as session, session.begin():
            session.add(
                AssistantInteractionModel(
                    id=interaction.interaction_id,
                    occurred_at=interaction.occurred_at,
                    outcome=interaction.outcome.value,
                    prompt_tokens=interaction.usage.prompt_tokens,
                    completion_tokens=interaction.usage.completion_tokens,
                    source_entry_ids=[str(i) for i in interaction.source_entry_ids],
                    retention_until=interaction.retention_until,
                    conversation_id=interaction.conversation_id,
                    user_id=interaction.user_id,
                    question_text=interaction.question_text,
                    answer_text=interaction.answer_text,
                    cache_entry_id=interaction.cache_entry_id,
                    served_from_cache=interaction.served_from_cache,
                )
            )

    async def record_feedback(self, interaction_id: uuid.UUID, *, helpful: bool) -> FeedbackRecorded | None:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                update(AssistantInteractionModel)
                .where(AssistantInteractionModel.id == interaction_id)
                .values(helpful=helpful)
                .returning(AssistantInteractionModel.cache_entry_id)
            )
            row = result.one_or_none()
            return None if row is None else FeedbackRecorded(cache_entry_id=row[0])

    async def count_in_conversation(self, conversation_id: uuid.UUID) -> int:
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count())
                .select_from(AssistantInteractionModel)
                .where(AssistantInteractionModel.conversation_id == conversation_id)
            )
            return int(result.scalar_one())

    async def purge_expired(self, now: datetime) -> int:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                delete(AssistantInteractionModel).where(AssistantInteractionModel.retention_until < now)
            )
            return int(result.rowcount or 0)  # type: ignore[attr-defined]
