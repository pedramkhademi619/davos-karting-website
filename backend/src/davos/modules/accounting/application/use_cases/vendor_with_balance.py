from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.entities.vendor import Vendor
from davos.modules.accounting.domain.value_objects.party_balance import PartyBalance


@dataclass(frozen=True)
class VendorWithBalance:
    vendor: Vendor
    balance: PartyBalance | None
