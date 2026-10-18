from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class JournalEntryModel(Base):
    __tablename__ = "accounting_journal_entries"
    __table_args__ = (
        UniqueConstraint("fiscal_year", "number", name="uq_accounting_entries_year_number"),
        # An automatic posting (a sale, its earning or its refund) exists at most once per reservation.
        Index(
            "uq_accounting_entries_auto_source",
            "source",
            "source_ref",
            unique=True,
            postgresql_where=text(
                "source_ref IS NOT NULL AND source IN ('online_sale', 'counter_sale', 'recognition', 'refund')"
            ),
        ),
        Index("ix_accounting_entries_date", "entry_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(80))
    source_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    reversed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reversal_of_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
