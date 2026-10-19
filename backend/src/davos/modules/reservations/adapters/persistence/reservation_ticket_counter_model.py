from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class ReservationTicketCounterModel(Base):
    """The last ticket number handed out in each shift ("2026-10-19-evening" -> 104).

    A shift's first ticket is 100. One upsert per ticket moves the counter atomically, so two bookings can never get the
    same number, and a new shift simply has no row yet.
    """

    __tablename__ = "reservation_ticket_counters"

    shift_key: Mapped[str] = mapped_column(String(24), primary_key=True)
    last_value: Mapped[int] = mapped_column(BigInteger, nullable=False)
