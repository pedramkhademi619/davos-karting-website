from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionLoad:
    """Karts already taken in one session (held, confirmed or attended)."""

    singles: int = 0
    doubles: int = 0

    def plus(self, singles: int, doubles: int) -> SessionLoad:
        return SessionLoad(self.singles + singles, self.doubles + doubles)
