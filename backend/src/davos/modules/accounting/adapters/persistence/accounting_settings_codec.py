from __future__ import annotations

from datetime import date
from typing import Any

from davos.modules.accounting.domain.enums.revenue_recognition import RevenueRecognition
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings


class AccountingSettingsCodec:
    """Stored as JSON; missing keys fall back to the defaults, so new settings never break old rows."""

    @staticmethod
    def encode(settings: AccountingSettings) -> dict[str, Any]:
        return {
            "auto_posting_enabled": settings.auto_posting_enabled,
            "vat_percent": settings.vat_percent,
            "gateway_fee_bp": settings.gateway_fee_bp,
            "revenue_recognition": settings.revenue_recognition.value,
            "locked_through": settings.locked_through.isoformat() if settings.locked_through else None,
        }

    @staticmethod
    def decode(data: dict[str, Any]) -> AccountingSettings:
        defaults = AccountingSettings()
        locked = data.get("locked_through")
        return AccountingSettings(
            auto_posting_enabled=bool(data.get("auto_posting_enabled", defaults.auto_posting_enabled)),
            vat_percent=int(data.get("vat_percent", defaults.vat_percent)),
            gateway_fee_bp=int(data.get("gateway_fee_bp", defaults.gateway_fee_bp)),
            revenue_recognition=RevenueRecognition(data.get("revenue_recognition", defaults.revenue_recognition.value)),
            locked_through=date.fromisoformat(locked) if locked else None,
        )
