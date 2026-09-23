from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class AssistantInteractionModel(Base):
    """One assistant question. user_id is a plain reference (no FK) so modules stay decoupled."""

    __tablename__ = "assistant_interactions"
    __table_args__ = (
        Index("ix_assistant_interactions_retention", "retention_until"),
        Index("ix_assistant_interactions_conversation", "conversation_id"),
        Index("ix_assistant_interactions_outcome_time", "outcome", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    source_entry_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    retention_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    question_text: Mapped[str | None] = mapped_column(Text)
    answer_text: Mapped[str | None] = mapped_column(Text)
    helpful: Mapped[bool | None] = mapped_column(Boolean)
    # Plain reference (no FK): cache entries are purged on their own schedule, interactions on theirs.
    cache_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    served_from_cache: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
