from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.accounting.domain.entities.staff_member import StaffMember
from davos.modules.accounting.domain.entities.staff_payment import StaffPayment


class StaffRepository(ABC):
    @abstractmethod
    async def add(self, member: StaffMember) -> None: ...

    @abstractmethod
    async def save(self, member: StaffMember) -> None: ...

    @abstractmethod
    async def get(self, staff_id: uuid.UUID) -> StaffMember | None: ...

    @abstractmethod
    async def list_all(self) -> list[StaffMember]: ...

    @abstractmethod
    async def add_payment(self, payment: StaffPayment) -> None: ...

    @abstractmethod
    async def payments_of_month(self, month_key: str) -> list[StaffPayment]: ...

    @abstractmethod
    async def payments_of(self, staff_id: uuid.UUID, limit: int) -> list[StaffPayment]: ...
