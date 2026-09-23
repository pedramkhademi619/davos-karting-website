from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class BookingWebhookInboxModel(Base):
    """Every signed delivery. The primary key is the provider event id, which is what makes replays harmless."""

    __tablename__ = "booking_webhook_inbox"
    __table_args__ = (
        CheckConstraint("status IN ('received', 'processed', 'failed')", name="status_valid"),
        Index("ix_booking_inbox_failed", "received_at", postgresql_where=text("status = 'failed'")),
    )

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
