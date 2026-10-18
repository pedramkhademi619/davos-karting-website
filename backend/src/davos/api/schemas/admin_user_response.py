from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.administration.domain.entities.admin_user import AdminUser


class AdminUserResponse(BaseModel):
    admin_id: uuid.UUID
    username: str
    display_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    permissions: list[str]  # what the account can open right now
    custom_permissions: bool  # False: it still has the role's defaults

    @classmethod
    def of(cls, a: AdminUser) -> AdminUserResponse:
        return cls(
            admin_id=a.id,
            username=a.username,
            display_name=a.display_name,
            role=a.role.value,
            is_active=a.is_active,
            last_login_at=a.last_login_at,
            created_at=a.created_at,
            permissions=sorted(p.value for p in a.effective_permissions()),
            custom_permissions=a.permissions is not None,
        )
