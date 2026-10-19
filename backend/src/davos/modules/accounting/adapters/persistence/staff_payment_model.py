from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class StaffPaymentModel(Base):
    __tablename__ = "accounting_staff_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounting_staff.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    amount_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    month_key: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str] = mapped_column(String(300), nullable=False, server_default="")
    entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
