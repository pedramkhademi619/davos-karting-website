from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.identity.domain.entities.user import User


class ProfileResponse(BaseModel):
    user_id: uuid.UUID
    mobile: str
    full_name: str
    marketing_opt_in: bool
    created_at: datetime

    @classmethod
    def of(cls, user: User) -> ProfileResponse:
        return cls(
            user_id=user.id,
            mobile=user.mobile.local,
            full_name=user.full_name,
            marketing_opt_in=user.marketing_opt_in,
            created_at=user.created_at,
        )
