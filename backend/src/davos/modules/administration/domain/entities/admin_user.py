from __future__ import annotations

import re
import uuid
from datetime import datetime

from davos.modules.administration.domain.enums.admin_permission import AdminPermission
from davos.modules.administration.domain.enums.admin_role import AdminRole
from davos.modules.administration.domain.errors.weak_password_error import WeakPasswordError
from davos.modules.administration.domain.services.permission_catalog import PermissionCatalog
from davos.modules.administration.domain.value_objects.admin_security_policy import AdminSecurityPolicy
from davos.shared_kernel.domain.aggregate_root import AggregateRoot
from davos.shared_kernel.domain.errors.validation_error import ValidationError

_USERNAME = re.compile(r"[a-z][a-z0-9._-]{2,31}")


class AdminUser(AggregateRoot[uuid.UUID]):
    """A staff account for the admin panel. Only a slow, salted password hash is stored."""

    def __init__(
        self,
        *,
        admin_id: uuid.UUID,
        username: str,
        display_name: str,
        password_hash: str,
        role: AdminRole,
        is_active: bool,
        created_at: datetime,
        failed_attempts: int = 0,
        locked_until: datetime | None = None,
        last_login_at: datetime | None = None,
        permissions: frozenset[AdminPermission] | None = None,
    ) -> None:
        super().__init__(admin_id)
        self.username = username
        self.display_name = display_name
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.created_at = created_at
        self.failed_attempts = failed_attempts
        self.locked_until = locked_until
        self.last_login_at = last_login_at
        self.permissions = permissions  # None: the defaults of the role

    @classmethod
    def create(
        cls,
        *,
        username: str,
        display_name: str,
        password_hash: str,
        role: AdminRole,
        now: datetime,
        permissions: frozenset[AdminPermission] | None = None,
    ) -> AdminUser:
        username = cls.normalize_username(username)
        if not _USERNAME.fullmatch(username):
            raise ValidationError(
                "نام کاربری باید ۳ تا ۳۲ حرف انگلیسی کوچک، عدد یا . _ - باشد و با حرف شروع شود.",
                code="invalid_username",
            )
        return cls(
            admin_id=uuid.uuid4(),
            username=username,
            display_name=" ".join(display_name.split())[:60] or username,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=now,
            permissions=PermissionCatalog.closure(permissions) if permissions is not None else None,
        )

    @staticmethod
    def normalize_username(username: str) -> str:
        return username.strip().lower()

    @staticmethod
    def check_password_strength(password: str) -> None:
        if (
            len(password) < 12
            or len(password) > 200
            or not any(c.isalpha() for c in password)
            or not any(c.isdigit() for c in password)
        ):
            raise WeakPasswordError

    def is_locked_at(self, now: datetime) -> bool:
        return self.locked_until is not None and now < self.locked_until

    def seconds_locked(self, now: datetime) -> int:
        if self.locked_until is None:
            return 0
        return max(int((self.locked_until - now).total_seconds()), 1)

    def record_failed_login(self, now: datetime, policy: AdminSecurityPolicy) -> None:
        self.failed_attempts += 1
        if self.failed_attempts >= policy.max_failed_logins:
            self.locked_until = now + policy.lockout
            self.failed_attempts = 0

    def record_login(self, now: datetime) -> None:
        self.failed_attempts = 0
        self.locked_until = None
        self.last_login_at = now

    @property
    def is_owner(self) -> bool:
        return self.role is AdminRole.OWNER

    def effective_permissions(self) -> frozenset[AdminPermission]:
        """The owner can do everything; staff get what the owner chose, or the staff defaults if nothing was."""
        if self.is_owner:
            return PermissionCatalog.everything()
        if self.permissions is None:
            return PermissionCatalog.STAFF_DEFAULTS
        return self.permissions

    def set_permissions(self, permissions: frozenset[AdminPermission] | None) -> None:
        """None goes back to the role's defaults. The owner is never restricted, so their setting is ignored."""
        self.permissions = PermissionCatalog.closure(permissions) if permissions is not None else None
