from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AccountBalance:
    """An account's movement: ``opening_net`` (debit minus credit before the period) and the period's debits/credits."""

    account_id: uuid.UUID
    opening_net: int
    debit: int
    credit: int

    @property
    def closing_net(self) -> int:
        return self.opening_net + self.debit - self.credit
