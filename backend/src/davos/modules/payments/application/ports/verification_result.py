from dataclasses import dataclass

from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome


@dataclass(frozen=True)
class VerificationResult:
    outcome: VerificationOutcome
    reference_id: str | None = None
    provider_code: int | None = None
