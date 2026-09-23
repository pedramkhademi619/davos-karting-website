from dataclasses import dataclass

from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class VerificationRequest:
    authority: str
    amount: Money  # always our stored amount, never a value taken from the browser callback
