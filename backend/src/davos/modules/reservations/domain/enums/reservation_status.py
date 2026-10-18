from enum import StrEnum


class ReservationStatus(StrEnum):
    HELD = "held"  # seats are held for a short time while the customer pays
    CONFIRMED = "confirmed"  # paid online, or entered by staff at the counter
    ATTENDED = "attended"  # the customer arrived and drove
    CANCELLED = "cancelled"
    EXPIRED = "expired"  # the hold ran out before a payment arrived

    @property
    def is_final(self) -> bool:
        return self in {ReservationStatus.ATTENDED, ReservationStatus.CANCELLED}
