from dataclasses import dataclass


@dataclass(frozen=True)
class ScreeningVerdict:
    suspicious: bool
    reasons: tuple[str, ...] = ()
