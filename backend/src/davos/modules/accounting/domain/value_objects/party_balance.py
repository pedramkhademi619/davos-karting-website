from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class PartyBalance:
    """What the business owes one supplier, aged by the date of each unpaid bill (oldest bills are paid first)."""

    party_id: uuid.UUID
    owed_irr: int
    age_0_30: int
    age_31_60: int
    age_61_90: int
    age_over_90: int
    advance_irr: int  # paid beyond what was owed
