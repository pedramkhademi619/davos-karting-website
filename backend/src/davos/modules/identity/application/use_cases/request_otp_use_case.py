from __future__ import annotations

from datetime import datetime, timedelta

from davos.modules.identity.application.ports.otp_challenge_repository import OtpChallengeRepository
from davos.modules.identity.application.ports.otp_code_generator import OtpCodeGenerator
from davos.modules.identity.application.ports.otp_delivery import OtpDelivery
from davos.modules.identity.application.ports.otp_hasher import OtpHasher
from davos.modules.identity.application.use_cases.otp_rate_limit_policy import OtpRateLimitPolicy
from davos.modules.identity.application.use_cases.request_otp_command import RequestOtpCommand
from davos.modules.identity.application.use_cases.request_otp_result import RequestOtpResult
from davos.modules.identity.domain.entities.otp_challenge import OtpChallenge
from davos.modules.identity.domain.errors.otp_delivery_failed_error import OtpDeliveryFailedError
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.modules.identity.domain.value_objects.otp_policy import OtpPolicy
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.rate_limiter import RateLimiter
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError

_TOO_MANY = "تعداد درخواست‌ها زیاد است. لطفا کمی بعد دوباره تلاش کنید."
_COOLDOWN = "برای دریافت مجدد کد کمی صبر کنید."


class RequestOtpUseCase:
    """Issue a one-time code and deliver it by SMS.

    The plaintext code exists only in memory between generation and delivery; storage and
    logs only ever see a keyed digest.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        challenges: OtpChallengeRepository,
        hasher: OtpHasher,
        code_generator: OtpCodeGenerator,
        delivery: OtpDelivery,
        rate_limiter: RateLimiter,
        clock: Clock,
        policy: OtpPolicy,
        limits: OtpRateLimitPolicy,
    ) -> None:
        self._uow = uow
        self._challenges = challenges
        self._hasher = hasher
        self._code_generator = code_generator
        self._delivery = delivery
        self._rate_limiter = rate_limiter
        self._clock = clock
        self._policy = policy
        self._limits = limits

    async def execute(self, command: RequestOtpCommand) -> RequestOtpResult:
        mobile = MobileNumber.parse(command.raw_mobile)
        await self._enforce_rate_limits(mobile, command.client_ip)

        code = self._code_generator.generate(self._policy.code_length)
        now = self._clock.now()

        async with self._uow:
            await self._enforce_resend_cooldown(mobile, now)
            await self._challenges.supersede_active_for(mobile.e164, now)
            challenge = OtpChallenge.issue(
                mobile=mobile.e164,
                code_digest=self._hasher.digest(mobile.e164, code),
                now=now,
                policy=self._policy,
            )
            await self._challenges.add(challenge)
            await self._uow.commit()

        if not await self._delivery.send(mobile, code, self._policy.ttl_seconds):
            raise OtpDeliveryFailedError
        return RequestOtpResult(
            expires_in_seconds=self._policy.ttl_seconds,
            resend_after_seconds=self._policy.resend_cooldown_seconds,
        )

    async def _enforce_rate_limits(self, mobile: MobileNumber, client_ip: str) -> None:
        checks = (
            (f"otp:req:mobile:{mobile.e164}", self._limits.per_mobile_limit, self._limits.per_mobile_window_seconds),
            (f"otp:req:ip:{client_ip}", self._limits.per_ip_limit, self._limits.per_ip_window_seconds),
        )
        for key, limit, window in checks:
            decision = await self._rate_limiter.hit(key, limit=limit, window_seconds=window)
            if not decision.allowed:
                raise RateLimitedError(_TOO_MANY, retry_after_seconds=decision.retry_after_seconds)

    async def _enforce_resend_cooldown(self, mobile: MobileNumber, now: datetime) -> None:
        last = await self._challenges.latest_created_at(mobile.e164)
        if last is None:
            return
        remaining = last + timedelta(seconds=self._policy.resend_cooldown_seconds) - now
        if remaining.total_seconds() > 0:
            raise RateLimitedError(_COOLDOWN, retry_after_seconds=int(remaining.total_seconds()) + 1)
