from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from davos.shared_kernel.domain.entity import Entity

IDLE_TIMEOUT = timedelta(hours=2)
_TOUCH_EVERY = timedelta(minutes=1)


class AdminSession(Entity[uuid.UUID]):
    """A signed-in admin browser. Ends at ``expires_at``, after two idle hours, or when revoked."""

    def __init__(
        self,
        *,
        session_id: uuid.UUID,
        admin_id: uuid.UUID,
        token_digest: str,
        created_at: datetime,
        expires_at: datetime,
        last_seen_at: datetime,
        ip_hint: str = "",
        user_agent: str = "",
        revoked_at: datetime | None = None,
    ) -> None:
        super().__init__(session_id)
        self.admin_id = admin_id
        self.token_digest = token_digest
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_seen_at = last_seen_at
        self.ip_hint = ip_hint
        self.user_agent = user_agent
        self.revoked_at = revoked_at

    @classmethod
    def start(
        cls,
        *,
        admin_id: uuid.UUID,
        token_digest: str,
        now: datetime,
        lifetime: timedelta,
        ip_hint: str,
        user_agent: str,
    ) -> AdminSession:
        return cls(
            session_id=uuid.uuid4(),
            admin_id=admin_id,
            token_digest=token_digest,
            created_at=now,
            expires_at=now + lifetime,
            last_seen_at=now,
            ip_hint=ip_hint[:45],
            user_agent=user_agent[:200],
        )

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and now < self.expires_at and now - self.last_seen_at < IDLE_TIMEOUT

    def touch(self, now: datetime) -> bool:
        if now - self.last_seen_at < _TOUCH_EVERY:
            return False
        self.last_seen_at = now
        return True

    def revoke(self, now: datetime) -> None:
        if self.revoked_at is None:
            self.revoked_at = now
