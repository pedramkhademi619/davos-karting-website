from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.administration.domain.enums.admin_permission import AdminPermission
from davos.modules.administration.domain.enums.admin_role import AdminRole


@dataclass(frozen=True)
class AuthenticatedAdmin:
    admin_id: uuid.UUID
    session_id: uuid.UUID
    username: str
    display_name: str
    role: AdminRole
    permissions: frozenset[AdminPermission]

    @property
    def is_owner(self) -> bool:
        return self.role is AdminRole.OWNER

    def can(self, permission: AdminPermission) -> bool:
        return permission in self.permissions
