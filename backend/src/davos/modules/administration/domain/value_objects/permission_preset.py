from __future__ import annotations

from dataclasses import dataclass

from davos.modules.administration.domain.enums.admin_permission import AdminPermission


@dataclass(frozen=True)
class PermissionPreset:
    """A ready-made set of permissions for a typical job, offered as a shortcut in the permission editor."""

    key: str
    label: str
    permissions: frozenset[AdminPermission]
