from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class KnowledgeEntryModel(Base):
    """Published, approved public content the assistant may retrieve. Never holds drafts or private data."""

    __tablename__ = "assistant_knowledge_entries"
    __table_args__ = (
        UniqueConstraint("source_type", "source_ref", name="uq_assistant_knowledge_source"),
        CheckConstraint("source_type IN ('faq', 'policy', 'service', 'pricing', 'contact')", name="source_type_valid"),
        CheckConstraint("url LIKE '/%' AND url NOT LIKE '//%'", name="url_is_internal_path"),
        Index(
            "ix_assistant_knowledge_search_text_trgm",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
        Index(
            "ix_assistant_knowledge_title_trgm",
            "title_norm",
            postgresql_using="gin",
            postgresql_ops={"title_norm": "gin_trgm_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(300), nullable=False)
    title_norm: Mapped[str] = mapped_column(Text, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
