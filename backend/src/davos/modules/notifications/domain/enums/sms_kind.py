from enum import StrEnum


class SmsKind(StrEnum):
    TRANSACTIONAL = "transactional"  # booking confirmations and other messages the customer expects
    BULK = "bulk"  # sent by staff from the admin panel
