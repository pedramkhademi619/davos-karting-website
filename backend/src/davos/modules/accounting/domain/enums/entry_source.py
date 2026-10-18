from enum import StrEnum


class EntrySource(StrEnum):
    MANUAL = "manual"
    OPENING = "opening"
    ONLINE_SALE = "online_sale"
    COUNTER_SALE = "counter_sale"
    RECOGNITION = "recognition"  # deferred ticket revenue earned when the session is driven
    REFUND = "refund"
    EXPENSE = "expense"
    INCOME = "income"
    VENDOR_PAYMENT = "vendor_payment"
    TRANSFER = "transfer"
    ASSET_PURCHASE = "asset_purchase"
    DEPRECIATION = "depreciation"
    CASH_CLOSE = "cash_close"
    PAYROLL = "payroll"
    REVERSAL = "reversal"
    CLOSING = "closing"  # year-end transfer of the year's profit into retained earnings

    @property
    def automatic(self) -> bool:
        """Posted by the system from another module's event, at most once per source reference."""
        return self in (EntrySource.ONLINE_SALE, EntrySource.COUNTER_SALE, EntrySource.RECOGNITION, EntrySource.REFUND)
