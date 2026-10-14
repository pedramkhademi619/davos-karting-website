from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class AccountingBackfillRequest(BaseModel):
    date_from: date
    date_to: date
