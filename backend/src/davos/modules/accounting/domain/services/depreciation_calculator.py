from __future__ import annotations

from davos.modules.accounting.domain.entities.fixed_asset import FixedAsset
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar


class DepreciationCalculator:
    """Straight-line depreciation by Jalali month: the cost less salvage value is spread evenly over the useful life,
    starting in the month the asset enters service; the last month takes the rounding remainder."""

    @staticmethod
    def amount_for_month(asset: FixedAsset, year: int, month: int, already_irr: int) -> int:
        start_year, start_month = FiscalCalendar.month_of(asset.in_service_date)
        index = (year - start_year) * 12 + (month - start_month)
        if index < 0 or index >= asset.life_months:
            return 0
        remaining = asset.depreciable_irr - already_irr
        if remaining <= 0:
            return 0
        if index == asset.life_months - 1:
            return remaining
        return min(asset.depreciable_irr // asset.life_months, remaining)
