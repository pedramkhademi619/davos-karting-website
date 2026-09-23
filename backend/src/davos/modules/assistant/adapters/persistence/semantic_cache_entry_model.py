from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base

EMBEDDING_DIMENSIONS = 768  # multilingual-e5-base; a model with another size needs a new column and a new migration


class SemanticCacheEntryModel(Base):
    """A model answer kept so that a later question with the same meaning can be answered without the model.

    Reads and writes go through raw SQL in ``PgVectorSemanticCache`` (a text -> vector cast, so the async driver
    needs no custom codec); this class is the schema's source of truth for Alembic and for the drift test.

    TODO: Admin Panel Review System. ``is_flagged_for_review`` and ``is_active`` are the hooks for a review screen
    (SQLAdmin or custom endpoints): list flagged and most-used entries, edit ``response``, approve (clear the
    flag) or deprecate (``is_active = False``). Entries flagged for review are never purged automatically.
    """

    __tablename__ = "assistant_semantic_cache"
    __table_args__ = (
        # Approximate nearest-neighbour index on cosine distance (the operator the queries use, `<=>`).
        Index(
            "ix_assistant_semantic_cache_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_assistant_semantic_cache_fingerprint_active", "fingerprint", "is_active"),
        Index("ix_assistant_semantic_cache_last_used", "last_used_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    original_query: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_query: Mapped[str] = mapped_column(Text, nullable=False)
    # Numbers and discriminator words of the question; an entry may only answer a question with the same signature.
    signature: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    # Hash of the knowledge, style notes, fixed rules and model that produced the answer.
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False, server_default="[]")
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_flagged_for_review: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
