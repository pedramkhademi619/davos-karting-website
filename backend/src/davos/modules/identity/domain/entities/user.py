from __future__ import annotations

import uuid
from datetime import datetime

from davos.modules.identity.domain.enums.user_status import UserStatus
from davos.modules.identity.domain.events.user_registered import UserRegistered
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.shared_kernel.domain.aggregate_root import AggregateRoot


class User(AggregateRoot[uuid.UUID]):
    """Customer identity. The verified mobile number is the unique natural key."""

    def __init__(
        self,
        *,
        user_id: uuid.UUID,
        mobile: MobileNumber,
        status: UserStatus,
        created_at: datetime,
    ) -> None:
        super().__init__(user_id)
        self.mobile = mobile
        self.status = status
        self.created_at = created_at

    @classmethod
    def register(cls, *, mobile: MobileNumber, now: datetime) -> User:
        user = cls(user_id=uuid.uuid4(), mobile=mobile, status=UserStatus.ACTIVE, created_at=now)
        user._raise(UserRegistered(user_id=user.id, occurred_at=now))
        return user

    @property
    def can_sign_in(self) -> bool:
        return self.status is not UserStatus.BLOCKED
