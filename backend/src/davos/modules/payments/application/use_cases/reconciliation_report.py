from dataclasses import dataclass


@dataclass(frozen=True)
class ReconciliationReport:
    examined: int = 0
    paid: int = 0
    failed: int = 0
    still_unknown: int = 0
    expired: int = 0
