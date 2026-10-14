from __future__ import annotations

from dataclasses import dataclass

from davos.modules.administration.domain.enums.admin_permission import AdminPermission


@dataclass(frozen=True)
class PermissionEntry:
    permission: AdminPermission
    label: str
    description: str
    implies: AdminPermission | None = None  # the level below (managing a section includes looking at it)
