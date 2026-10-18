from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetRow:
    account_id: uuid.UUID
    code: str
    name: str
    account_type: str
    budget_irr: int
    actual_irr: int

    @property
    def variance_irr(self) -> int:
        """Positive when the account ended above its budget."""
        return self.actual_irr - self.budget_irr
