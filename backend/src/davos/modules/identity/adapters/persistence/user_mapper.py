from __future__ import annotations

from davos.modules.identity.adapters.persistence.user_model import UserModel
from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.enums.user_status import UserStatus
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber


class UserMapper:
    @staticmethod
    def to_domain(model: UserModel) -> User:
        return User(
            user_id=model.id,
            mobile=MobileNumber(model.mobile),
            status=UserStatus(model.status),
            created_at=model.created_at,
        )
