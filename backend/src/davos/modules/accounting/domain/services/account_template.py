from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.account_type import AccountType


@dataclass(frozen=True)
class AccountTemplate:
    code: str
    name: str
    account_type: AccountType
    parent_code: str | None
    is_group: bool = False
    role: AccountRole | None = None
