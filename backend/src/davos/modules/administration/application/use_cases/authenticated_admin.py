from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.administration.domain.enums.admin_role import AdminRole


@dataclass(frozen=True)
class AuthenticatedAdmin:
    admin_id: uuid.UUID
    session_id: uuid.UUID
    username: str
    display_name: str
    role: AdminRole

    @property
    def is_owner(self) -> bool:
        return self.role is AdminRole.OWNER
