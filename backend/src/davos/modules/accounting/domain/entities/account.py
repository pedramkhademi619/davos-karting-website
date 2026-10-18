from __future__ import annotations

import uuid
from datetime import datetime

from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.errors.account_not_postable_error import AccountNotPostableError
from davos.shared_kernel.domain.entity import Entity
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class Account(Entity[uuid.UUID]):
    """A line of the chart of accounts. Group accounts only add up their children; postable accounts take entries."""

    def __init__(
        self,
        *,
        account_id: uuid.UUID,
        code: str,
        name: str,
        account_type: AccountType,
        parent_id: uuid.UUID | None,
        is_group: bool,
        role: AccountRole | None,
        active: bool,
        is_system: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(account_id)
        self.code = self._clean_code(code)
        self.name = self._clean_name(name)
        self.type = account_type
        self.parent_id = parent_id
        self.is_group = is_group
        self.role = role
        self.active = active
        self.is_system = is_system
        self.created_at = created_at

    @classmethod
    def create(
        cls,
        *,
        code: str,
        name: str,
        account_type: AccountType,
        parent_id: uuid.UUID | None,
        is_group: bool,
        now: datetime,
        role: AccountRole | None = None,
        is_system: bool = False,
    ) -> Account:
        return cls(
            account_id=uuid.uuid4(),
            code=code,
            name=name,
            account_type=account_type,
            parent_id=parent_id,
            is_group=is_group,
            role=role,
            active=True,
            is_system=is_system,
            created_at=now,
        )

    @property
    def postable(self) -> bool:
        return self.active and not self.is_group

    def ensure_postable(self) -> None:
        if not self.postable:
            raise AccountNotPostableError

    def edit(self, *, code: str, name: str, active: bool) -> None:
        self.code = self._clean_code(code)
        self.name = self._clean_name(name)
        self.active = active

    @staticmethod
    def _clean_code(code: str) -> str:
        code = code.strip()
        if not code or len(code) > 20 or not code.replace("-", "").isalnum():
            raise ValidationError("کد حساب باید ۱ تا ۲۰ حرف یا رقم باشد.", code="invalid_account_code")
        return code

    @staticmethod
    def _clean_name(name: str) -> str:
        name = " ".join(name.split())
        if not name or len(name) > 120:
            raise ValidationError("نام حساب را وارد کنید (حداکثر ۱۲۰ نویسه).", code="invalid_account_name")
        return name
