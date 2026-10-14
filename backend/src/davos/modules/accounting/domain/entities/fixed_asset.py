from __future__ import annotations

import uuid
from datetime import date, datetime

from davos.modules.accounting.domain.enums.asset_status import AssetStatus
from davos.shared_kernel.domain.entity import Entity
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class FixedAsset(Entity[uuid.UUID]):
    """A kart or other long-lived equipment, written off evenly over its useful life (straight-line depreciation)."""

    def __init__(
        self,
        *,
        asset_id: uuid.UUID,
        name: str,
        asset_account_id: uuid.UUID,
        cost_irr: int,
        salvage_irr: int,
        in_service_date: date,
        life_months: int,
        status: AssetStatus,
        note: str,
        created_at: datetime,
    ) -> None:
        super().__init__(asset_id)
        name = " ".join(name.split())
        if not name or len(name) > 120:
            raise ValidationError("نام دارایی را وارد کنید.", code="invalid_asset_name")
        if cost_irr <= 0 or not 0 <= salvage_irr < cost_irr:
            raise ValidationError("بهای تمام‌شده باید مثبت و ارزش اسقاط کمتر از آن باشد.", code="invalid_asset_cost")
        if not 1 <= life_months <= 600:
            raise ValidationError("عمر مفید باید بین ۱ تا ۶۰۰ ماه باشد.", code="invalid_asset_life")
        self.name = name
        self.asset_account_id = asset_account_id
        self.cost_irr = cost_irr
        self.salvage_irr = salvage_irr
        self.in_service_date = in_service_date
        self.life_months = life_months
        self.status = status
        self.note = note.strip()[:300]
        self.created_at = created_at

    @classmethod
    def register(
        cls,
        *,
        name: str,
        asset_account_id: uuid.UUID,
        cost_irr: int,
        salvage_irr: int,
        in_service_date: date,
        life_months: int,
        note: str,
        now: datetime,
    ) -> FixedAsset:
        return cls(
            asset_id=uuid.uuid4(),
            name=name,
            asset_account_id=asset_account_id,
            cost_irr=cost_irr,
            salvage_irr=salvage_irr,
            in_service_date=in_service_date,
            life_months=life_months,
            status=AssetStatus.ACTIVE,
            note=note,
            created_at=now,
        )

    @property
    def depreciable_irr(self) -> int:
        return self.cost_irr - self.salvage_irr

    def dispose(self) -> None:
        self.status = AssetStatus.DISPOSED
