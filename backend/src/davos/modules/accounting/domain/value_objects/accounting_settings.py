from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from davos.modules.accounting.domain.enums.revenue_recognition import RevenueRecognition
from davos.shared_kernel.domain.errors.validation_error import ValidationError


@dataclass(frozen=True)
class AccountingSettings:
    """What the owner chooses about the books. Defaults suit a small business that is not VAT-registered."""

    auto_posting_enabled: bool = True  # post paid online tickets and counter sales automatically
    vat_percent: int = 0  # 0 = not VAT-registered; otherwise VAT is carved out of every ticket price
    gateway_fee_bp: int = 0  # the bank/gateway's fee on online payments, in basis points (100 = 1%)
    revenue_recognition: RevenueRecognition = RevenueRecognition.ON_PAYMENT
    locked_through: date | None = None  # no entry may be dated on or before this day

    def __post_init__(self) -> None:
        if not 0 <= self.vat_percent <= 30:
            raise ValidationError("درصد مالیات بر ارزش افزوده باید بین ۰ تا ۳۰ باشد.", code="invalid_vat")
        if not 0 <= self.gateway_fee_bp <= 1000:
            raise ValidationError("کارمزد درگاه باید بین ۰ تا ۱۰ درصد باشد.", code="invalid_gateway_fee")
