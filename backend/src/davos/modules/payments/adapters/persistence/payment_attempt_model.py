from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class PaymentAttemptModel(Base):
    __tablename__ = "payments_attempts"
    __table_args__ = (
        CheckConstraint("amount_irr > 0", name="amount_positive"),
        CheckConstraint(
            "status IN ('created', 'redirected', 'verifying', 'unknown', 'paid', 'failed', 'expired')",
            name="status_valid",
        ),
        CheckConstraint("status <> 'paid' OR reference_id IS NOT NULL", name="paid_has_reference"),
        # The database itself refuses a second successful payment for one order.
        Index("uq_payments_one_paid_per_order", "order_ref", unique=True, postgresql_where=text("status = 'paid'")),
        Index("ix_payments_status_updated", "status", "updated_at"),
        Index("ix_payments_customer", "customer_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    order_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    amount_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    authority: Mapped[str | None] = mapped_column(String(64), unique=True)
    reference_id: Mapped[str | None] = mapped_column(String(64))
    failure_reason: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
