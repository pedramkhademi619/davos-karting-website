from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BookingReturnStatus:
    """What the return page may show. ``confirmed`` etc. appear only for verified, owned bookings."""

    state: str
    session_time: datetime | None = None
    amount_irr: int | None = None
