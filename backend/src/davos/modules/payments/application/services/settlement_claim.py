from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class SettlementClaim:
    """What a verifier needs after it claimed an attempt (read inside the claiming transaction)."""

    request: VerificationRequest
    order_ref: str
    customer_id: uuid.UUID
    amount: Money
