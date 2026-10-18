from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class CashClosingModel(Base):
    __tablename__ = "accounting_cash_closings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    day: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    expected_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    counted_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entry_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("accounting_journal_entries.id"))
    note: Mapped[str] = mapped_column(String(300), nullable=False, server_default="")
    closed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
