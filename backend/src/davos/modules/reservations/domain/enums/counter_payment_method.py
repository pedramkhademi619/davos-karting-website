from enum import StrEnum


class CounterPaymentMethod(StrEnum):
    """How a counter sale was paid, so the accounts know where the money went."""

    NONE = "none"  # online ticket, or a seat held at the counter with no money taken
    CASH = "cash"
    CARD = "card"  # card reader at the counter
    TRANSFER = "transfer"  # bank transfer or card-to-card
