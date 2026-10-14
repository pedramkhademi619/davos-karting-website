from __future__ import annotations

import uuid
from datetime import datetime

from davos.shared_kernel.domain.entity import Entity
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class Vendor(Entity[uuid.UUID]):
    """A supplier or other party the business owes money to (fuel, tyres, rent, repairs, staff...)."""

    def __init__(
        self, *, vendor_id: uuid.UUID, name: str, phone: str, note: str, active: bool, created_at: datetime
    ) -> None:
        super().__init__(vendor_id)
        self.name = self._clean_name(name)
        self.phone = phone.strip()[:20]
        self.note = note.strip()[:300]
        self.active = active
        self.created_at = created_at

    @classmethod
    def create(cls, *, name: str, phone: str, note: str, now: datetime) -> Vendor:
        return cls(vendor_id=uuid.uuid4(), name=name, phone=phone, note=note, active=True, created_at=now)

    def edit(self, *, name: str, phone: str, note: str, active: bool) -> None:
        self.name = self._clean_name(name)
        self.phone = phone.strip()[:20]
        self.note = note.strip()[:300]
        self.active = active

    @staticmethod
    def _clean_name(name: str) -> str:
        name = " ".join(name.split())
        if not name or len(name) > 120:
            raise ValidationError("نام تامین‌کننده را وارد کنید.", code="invalid_vendor_name")
        return name
