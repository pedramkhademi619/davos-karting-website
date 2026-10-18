from __future__ import annotations

import uuid
from datetime import datetime

from davos.modules.identity.domain.enums.user_status import UserStatus
from davos.modules.identity.domain.events.user_registered import UserRegistered
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.shared_kernel.domain.aggregate_root import AggregateRoot
from davos.shared_kernel.domain.errors.validation_error import ValidationError

MAX_NAME_CHARS = 80


class User(AggregateRoot[uuid.UUID]):
    """Customer identity. The verified mobile number is the unique natural key."""

    def __init__(
        self,
        *,
        user_id: uuid.UUID,
        mobile: MobileNumber,
        status: UserStatus,
        created_at: datetime,
        full_name: str = "",
        marketing_opt_in: bool = False,
    ) -> None:
        super().__init__(user_id)
        self.mobile = mobile
        self.status = status
        self.created_at = created_at
        self.full_name = full_name
        self.marketing_opt_in = marketing_opt_in

    @classmethod
    def register(cls, *, mobile: MobileNumber, now: datetime) -> User:
        user = cls(user_id=uuid.uuid4(), mobile=mobile, status=UserStatus.ACTIVE, created_at=now)
        user._raise(UserRegistered(user_id=user.id, occurred_at=now))
        return user

    @property
    def can_sign_in(self) -> bool:
        return self.status is not UserStatus.BLOCKED

    def update_profile(self, *, full_name: str, marketing_opt_in: bool) -> None:
        cleaned = " ".join(full_name.split())
        if len(cleaned) > MAX_NAME_CHARS:
            raise ValidationError(f"نام حداکثر {MAX_NAME_CHARS} نویسه است.", code="name_too_long")
        if any(ch in cleaned for ch in "<>{}"):
            raise ValidationError("نام شامل نویسه‌های غیرمجاز است.", code="name_invalid")
        self.full_name = cleaned
        self.marketing_opt_in = marketing_opt_in

    def change_status(self, status: UserStatus) -> None:
        self.status = status
