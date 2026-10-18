from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base

EMBEDDING_DIMENSIONS = 384  # paraphrase-multilingual-MiniLM-L12-v2; another model needs a new column and migration


class AnswerCacheEntryModel(Base):
    """A model's answer kept so that a later question with the same meaning can be answered without the model.

    Reads and writes go through raw SQL in ``PgAnswerCache`` (a text -> vector cast, so the async driver needs no
    custom codec); this class is the schema's source of truth for Alembic and for the drift test.

    There is no vector index on purpose: a search first narrows the table to one fingerprint (the btree index below)
    and then orders that handful of rows by cosine distance exactly. An approximate index would only be needed for
    tens of thousands of live entries, and would skip a fresh match hidden behind old ones.
    """

    __tablename__ = "assistant_answer_cache"
    __table_args__ = (Index("ix_assistant_answer_cache_fingerprint_active", "fingerprint", "is_active"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    original_query: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_query: Mapped[str] = mapped_column(Text, nullable=False)
    # The question's numbers and discriminator words; an entry may only answer a question with the same signature.
    signature: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    # Hash of everything the answer was written from (AnswerFingerprint): change any of it and the entry stops matching.
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False, server_default="[]")
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
