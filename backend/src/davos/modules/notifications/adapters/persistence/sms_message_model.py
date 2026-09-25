from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class SmsMessageModel(Base):
    __tablename__ = "notifications_sms_messages"
    __table_args__ = (
        CheckConstraint("kind IN ('transactional', 'bulk')", name="kind_valid"),
        CheckConstraint(
            "status IN ('queued', 'sent', 'delivered', 'failed', 'blocked', 'unknown')", name="status_valid"
        ),
        Index("ix_sms_created", "created_at"),
        Index("ix_sms_pending", "created_at", postgresql_where=text("status IN ('queued', 'sent', 'unknown')")),
        Index("ix_sms_provider_id", "provider_message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    recipient: Mapped[str] = mapped_column(String(16), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(40))
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    sent_by: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    error: Mapped[str] = mapped_column(String(200), nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
