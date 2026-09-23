from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from davos.modules.identity.domain.services.ip_anonymizer import IpAnonymizer
from davos.shared_kernel.domain.entity import Entity


class CustomerSession(Entity[uuid.UUID]):
    """Server-side session. Only the digest of the bearer token is stored."""

    def __init__(
        self,
        *,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        token_digest: str,
        user_agent: str,
        ip_hint: str,
        created_at: datetime,
        expires_at: datetime,
        last_seen_at: datetime,
        revoked_at: datetime | None = None,
    ) -> None:
        super().__init__(session_id)
        self.user_id = user_id
        self.token_digest = token_digest
        self.user_agent = user_agent
        self.ip_hint = ip_hint
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_seen_at = last_seen_at
        self.revoked_at = revoked_at

    @classmethod
    def start(
        cls,
        *,
        user_id: uuid.UUID,
        token_digest: str,
        user_agent: str,
        client_ip: str,
        now: datetime,
        lifetime: timedelta,
    ) -> CustomerSession:
        return cls(
            session_id=uuid.uuid4(),
            user_id=user_id,
            token_digest=token_digest,
            user_agent=user_agent[:200],
            ip_hint=IpAnonymizer.anonymize(client_ip),
            created_at=now,
            expires_at=now + lifetime,
            last_seen_at=now,
        )

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and now < self.expires_at

    def revoke(self, now: datetime) -> None:
        if self.revoked_at is None:
            self.revoked_at = now

    def touch(self, now: datetime, *, min_interval: timedelta = timedelta(minutes=5)) -> bool:
        """Refresh last_seen_at at most once per interval; returns True when it changed."""
        if now - self.last_seen_at < min_interval:
            return False
        self.last_seen_at = now
        return True
