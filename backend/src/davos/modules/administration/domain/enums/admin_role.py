from enum import StrEnum


class AdminRole(StrEnum):
    OWNER = "owner"  # everything, including prices, booking settings and staff accounts
    STAFF = "staff"  # day-to-day work: reservations, customers, SMS
