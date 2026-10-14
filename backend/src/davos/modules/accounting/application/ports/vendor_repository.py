from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.accounting.domain.entities.vendor import Vendor


class VendorRepository(ABC):
    @abstractmethod
    async def add(self, vendor: Vendor) -> None: ...

    @abstractmethod
    async def save(self, vendor: Vendor) -> None: ...

    @abstractmethod
    async def get(self, vendor_id: uuid.UUID) -> Vendor | None: ...

    @abstractmethod
    async def list_all(self) -> list[Vendor]: ...
