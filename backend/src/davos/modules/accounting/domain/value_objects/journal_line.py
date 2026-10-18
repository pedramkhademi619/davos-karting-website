from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.accounting.domain.errors.invalid_line_error import InvalidLineError


@dataclass(frozen=True)
class JournalLine:
    """One side of a posting: a debit or a credit of whole Rial against one account (optionally for one supplier)."""

    account_id: uuid.UUID
    debit_irr: int = 0
    credit_irr: int = 0
    memo: str = ""
    party_id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        for value in (self.debit_irr, self.credit_irr):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise InvalidLineError
        if (self.debit_irr > 0) == (self.credit_irr > 0):
            raise InvalidLineError
        if len(self.memo) > 300:
            raise InvalidLineError("شرح سطر حداکثر ۳۰۰ نویسه است.")

    @property
    def amount_irr(self) -> int:
        return self.debit_irr or self.credit_irr
