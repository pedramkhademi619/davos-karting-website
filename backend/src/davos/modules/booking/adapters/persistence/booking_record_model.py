from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class BookingRecordModel(Base):
    __tablename__ = "booking_records"
    __table_args__ = (
        CheckConstraint("amount_irr >= 0", name="amount_not_negative"),
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'cancelled', 'attended', 'no_show', 'refunded')", name="status_valid"
        ),
        Index("ix_booking_records_user_session", "user_id", "session_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    external_booking_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    session_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
