from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    Sequence,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base

# The customer-facing ticket number (never the primary key: that stays the uuid id): short, easy to read out at the
# the counter, and starting again at 100 in every shift (see ReservationTicketCounterModel). The Postgres sequence below
# is the old, global numbering: kept for rows made before per-shift numbers and for the demo-data tools.
TICKET_NUMBER_SEQUENCE = Sequence("reservations_ticket_number_seq", start=100, metadata=Base.metadata)


class ReservationModel(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("single_count >= 0 AND double_count >= 0", name="counts_not_negative"),
        CheckConstraint("single_count + double_count > 0", name="at_least_one_kart"),
        CheckConstraint("amount_irr >= 0", name="amount_not_negative"),
        CheckConstraint("payment_method IN ('none', 'cash', 'card', 'transfer')", name="payment_method_valid"),
        CheckConstraint("status IN ('held', 'confirmed', 'attended', 'cancelled', 'expired')", name="status_valid"),
        CheckConstraint("source IN ('online', 'staff')", name="source_valid"),
        CheckConstraint("status <> 'held' OR hold_expires_at IS NOT NULL", name="hold_has_expiry"),
        CheckConstraint("source <> 'online' OR customer_id IS NOT NULL", name="online_has_customer"),
        Index("ix_reservations_session", "business_date", "session_time"),
        Index("ix_reservations_customer", "customer_id", "created_at"),
        Index("ix_reservations_holds", "hold_expires_at", postgresql_where=text("status = 'held'")),
        UniqueConstraint("shift_key", "ticket_number", name="uq_reservations_shift_ticket"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    ticket_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shift_key: Mapped[str | None] = mapped_column(String(24), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(12), nullable=False, server_default="none")
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    business_date: Mapped[date] = mapped_column(Date, nullable=False)
    session_time: Mapped[time] = mapped_column(Time, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    single_count: Mapped[int] = mapped_column(Integer, nullable=False)
    double_count: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    contact_mobile: Mapped[str] = mapped_column(String(16), nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_ref: Mapped[str | None] = mapped_column(String(64))
    confirmed_late: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    cancel_reason: Mapped[str] = mapped_column(String(300), nullable=False, server_default="")
