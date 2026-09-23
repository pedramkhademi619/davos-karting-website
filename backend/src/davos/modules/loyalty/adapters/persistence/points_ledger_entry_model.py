from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class PointsLedgerEntryModel(Base):
    """Append-only (enforced by a database trigger, see migration 0005)."""

    __tablename__ = "loyalty_points_ledger"
    __table_args__ = (
        UniqueConstraint("customer_id", "kind", "source_ref", name="uq_loyalty_ledger_source"),
        CheckConstraint("delta <> 0", name="delta_not_zero"),
        CheckConstraint("kind IN ('earn', 'spend', 'expire', 'adjust', 'reversal')", name="kind_valid"),
        CheckConstraint("kind <> 'earn' OR delta > 0", name="earn_positive"),
        CheckConstraint("kind NOT IN ('spend', 'expire') OR delta < 0", name="spend_expire_negative"),
        Index("ix_loyalty_ledger_customer_time", "customer_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loyalty_accounts.customer_id"), nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    reverses_kind: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
