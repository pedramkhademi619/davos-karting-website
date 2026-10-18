from enum import StrEnum


class RevenueRecognition(StrEnum):
    ON_PAYMENT = "on_payment"  # a ticket is revenue the day it is paid (simple, cash-like)
    ON_SESSION = "on_session"  # a ticket is a customer advance until the session is driven (accrual)
