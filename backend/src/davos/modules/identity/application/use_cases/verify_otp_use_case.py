from __future__ import annotations

from datetime import timedelta

from davos.modules.identity.application.ports.otp_challenge_repository import OtpChallengeRepository
from davos.modules.identity.application.ports.otp_hasher import OtpHasher
from davos.modules.identity.application.ports.session_repository import SessionRepository
from davos.modules.identity.application.ports.session_token_service import SessionTokenService
from davos.modules.identity.application.ports.user_repository import UserRepository
from davos.modules.identity.application.use_cases.otp_rate_limit_policy import OtpRateLimitPolicy
from davos.modules.identity.application.use_cases.verify_otp_command import VerifyOtpCommand
from davos.modules.identity.application.use_cases.verify_otp_result import VerifyOtpResult
from davos.modules.identity.domain.entities.customer_session import CustomerSession
from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.enums.otp_verification_result import OtpVerificationResult
from davos.modules.identity.domain.errors.otp_verification_failed_error import OtpVerificationFailedError
from davos.modules.identity.domain.errors.user_blocked_error import UserBlockedError
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.rate_limiter import RateLimiter
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.digit_normalizer import DigitNormalizer
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError


class VerifyOtpUseCase:
    """Exchange a valid one-time code for a server-side session.

    Failed attempts are committed (the attempt counter must survive) and only then reported.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        challenges: OtpChallengeRepository,
        users: UserRepository,
        sessions: SessionRepository,
        hasher: OtpHasher,
        tokens: SessionTokenService,
        rate_limiter: RateLimiter,
        clock: Clock,
        limits: OtpRateLimitPolicy,
        session_lifetime: timedelta,
    ) -> None:
        self._uow = uow
        self._challenges = challenges
        self._users = users
        self._sessions = sessions
        self._hasher = hasher
        self._tokens = tokens
        self._rate_limiter = rate_limiter
        self._clock = clock
        self._limits = limits
        self._session_lifetime = session_lifetime

    async def execute(self, command: VerifyOtpCommand) -> VerifyOtpResult:
        mobile = MobileNumber.parse(command.raw_mobile)
        decision = await self._rate_limiter.hit(
            f"otp:verify:ip:{command.client_ip}",
            limit=self._limits.verify_per_ip_limit,
            window_seconds=self._limits.verify_per_ip_window_seconds,
        )
        if not decision.allowed:
            raise RateLimitedError(
                "تعداد تلاش‌ها زیاد است. لطفا کمی بعد دوباره تلاش کنید.",
                retry_after_seconds=decision.retry_after_seconds,
            )

        now = self._clock.now()
        async with self._uow:
            challenge = await self._challenges.get_latest_for_update(mobile.e164)
            if challenge is None:
                raise OtpVerificationFailedError(OtpVerificationResult.EXPIRED)

            code = DigitNormalizer.to_ascii(command.code).strip()
            outcome = challenge.verify(self._hasher.digest(mobile.e164, code), now)
            await self._challenges.save(challenge)
            if outcome is not OtpVerificationResult.VERIFIED:
                await self._uow.commit()  # persist the attempt counter before failing
                raise OtpVerificationFailedError(outcome)

            user, created = await self._users.add_or_get(User.register(mobile=mobile, now=now))
            if not user.can_sign_in:
                await self._uow.commit()
                raise UserBlockedError

            issued = self._tokens.issue()
            session = CustomerSession.start(
                user_id=user.id,
                token_digest=issued.digest,
                user_agent=command.user_agent,
                client_ip=command.client_ip,
                now=now,
                lifetime=self._session_lifetime,
            )
            await self._sessions.add(session)
            if created:
                self._uow.collect_events(user.pull_events())
            await self._uow.commit()

        return VerifyOtpResult(
            user_id=user.id,
            session_id=session.id,
            session_token=issued.raw,
            expires_at=session.expires_at,
            is_new_user=created,
        )
