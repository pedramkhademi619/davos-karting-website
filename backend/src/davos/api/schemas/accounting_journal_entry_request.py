from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from davos.api.schemas.accounting_journal_line_request import AccountingJournalLineRequest


class AccountingJournalEntryRequest(BaseModel):
    date: date
    description: str = Field(min_length=1, max_length=300)
    lines: list[AccountingJournalLineRequest] = Field(min_length=2, max_length=60)
    opening: bool = False
