from __future__ import annotations

from dataclasses import dataclass

from davos.modules.identity.domain.entities.user import User


@dataclass(frozen=True)
class CustomerPage:
    items: list[User]
    total: int
