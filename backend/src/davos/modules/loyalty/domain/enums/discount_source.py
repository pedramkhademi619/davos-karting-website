from enum import StrEnum


class DiscountSource(StrEnum):
    """Also the deterministic tie-break order: earlier members win ties."""

    PERMANENT_CUSTOMER = "permanent_customer"
    TIER = "tier"
    COUPON = "coupon"
