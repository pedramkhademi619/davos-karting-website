from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.value_objects.ledger_line import LedgerLine


@dataclass(frozen=True)
class AccountLedger:
    opening_net: int  # debit minus credit before the first day
    lines: list[LedgerLine]
