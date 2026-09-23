from __future__ import annotations

import hmac
import uuid
from datetime import datetime, timedelta

from davos.modules.identity.domain.enums.otp_verification_result import OtpVerificationResult
from davos.modules.identity.domain.value_objects.otp_policy import OtpPolicy
from davos.shared_kernel.domain.entity import Entity


class OtpChallenge(Entity[uuid.UUID]):
    """One issued one-time code. Only a keyed digest of the code is ever held."""

    def __init__(
        self,
        *,
        challenge_id: uuid.UUID,
        mobile: str,
        code_digest: str,
        created_at: datetime,
        expires_at: datetime,
        max_attempts: int,
        attempts: int = 0,
        consumed_at: datetime | None = None,
        superseded_at: datetime | None = None,
    ) -> None:
        super().__init__(challenge_id)
        self.mobile = mobile
        self.code_digest = code_digest
        self.created_at = created_at
        self.expires_at = expires_at
        self.max_attempts = max_attempts
        self.attempts = attempts
        self.consumed_at = consumed_at
        self.superseded_at = superseded_at

    @classmethod
    def issue(cls, *, mobile: str, code_digest: str, now: datetime, policy: OtpPolicy) -> OtpChallenge:
        return cls(
            challenge_id=uuid.uuid4(),
            mobile=mobile,
            code_digest=code_digest,
            created_at=now,
            expires_at=now + timedelta(seconds=policy.ttl_seconds),
            max_attempts=policy.max_attempts,
        )

    def supersede(self, now: datetime) -> None:
        if self.consumed_at is None and self.superseded_at is None:
            self.superseded_at = now

    def verify(self, candidate_digest: str, now: datetime) -> OtpVerificationResult:
        """Check a candidate code digest.

        This mutates attempt counters, so the caller must persist the challenge even on failure.
        """
        if self.consumed_at is not None:
            return OtpVerificationResult.ALREADY_USED
        if self.superseded_at is not None:
            return OtpVerificationResult.SUPERSEDED
        if now >= self.expires_at:
            return OtpVerificationResult.EXPIRED
        if self.attempts >= self.max_attempts:
            return OtpVerificationResult.LOCKED

        self.attempts += 1
        if hmac.compare_digest(self.code_digest, candidate_digest):
            self.consumed_at = now
            return OtpVerificationResult.VERIFIED
        return OtpVerificationResult.WRONG_CODE
