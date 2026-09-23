from dataclasses import dataclass


@dataclass(frozen=True)
class RelayReport:
    dispatched: int = 0
    failed: int = 0
    dead_lettered: int = 0
