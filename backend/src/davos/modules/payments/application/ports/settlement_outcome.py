from enum import StrEnum


class SettlementOutcome(StrEnum):
    SETTLED = "settled"  # the funds are the merchant's (or already were)
    RETRY = "retry"  # not settled yet; try again later (the money is still held for us)
    REVERSED = "reversed"  # the bank had already returned the money to the customer
