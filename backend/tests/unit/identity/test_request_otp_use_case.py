import pytest

from davos.modules.identity.adapters.security.hmac_otp_hasher import HmacOtpHasher
from davos.modules.identity.application.use_cases.otp_rate_limit_policy import OtpRateLimitPolicy
from davos.modules.identity.application.use_cases.request_otp_command import RequestOtpCommand
from davos.modules.identity.application.use_cases.request_otp_use_case import RequestOtpUseCase
from davos.modules.identity.domain.errors.invalid_mobile_number_error import InvalidMobileNumberError
from davos.modules.identity.domain.errors.otp_delivery_failed_error import OtpDeliveryFailedError
from davos.modules.identity.domain.value_objects.otp_policy import OtpPolicy
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError
from tests.fakes.fake_otp_delivery import FakeOtpDelivery
from tests.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_otp_challenge_repository import InMemoryOtpChallengeRepository
from tests.fakes.sequence_otp_code_generator import SequenceOtpCodeGenerator

SECRET = "s" * 40


class Harness:
    def __init__(self, *, delivery_ok: bool = True, limits: OtpRateLimitPolicy | None = None) -> None:
        self.clock = FixedClock()
        self.uow = FakeUnitOfWork()
        self.challenges = InMemoryOtpChallengeRepository()
        self.delivery = FakeOtpDelivery(succeed=delivery_ok)
        self.use_case = RequestOtpUseCase(
            uow=self.uow,
            challenges=self.challenges,
            hasher=HmacOtpHasher(SECRET),
            code_generator=SequenceOtpCodeGenerator(),
            delivery=self.delivery,
            rate_limiter=InMemoryRateLimiter(self.clock),
            clock=self.clock,
            policy=OtpPolicy(),
            limits=limits or OtpRateLimitPolicy(),
        )

    async def request(self, mobile: str = "09123456789", ip: str = "203.0.113.5") -> None:
        await self.use_case.execute(RequestOtpCommand(raw_mobile=mobile, client_ip=ip))


async def test_issues_a_challenge_and_sends_the_code_to_the_normalised_number() -> None:
    h = Harness()
    result = await h.use_case.execute(RequestOtpCommand(raw_mobile="۰۹۱۲۳۴۵۶۷۸۹", client_ip="203.0.113.5"))
    assert h.delivery.sent == [("+989123456789", "123456")]
    assert result.expires_in_seconds == 120
    assert h.uow.commits == 1


async def test_plaintext_code_is_never_stored() -> None:
    h = Harness()
    await h.request()
    stored = h.challenges.items[0]
    assert h.delivery.last_code not in vars(stored).values()
    assert len(stored.code_digest) == 64


async def test_invalid_mobile_is_rejected_before_any_side_effect() -> None:
    h = Harness()
    with pytest.raises(InvalidMobileNumberError):
        await h.request(mobile="12345")
    assert h.delivery.sent == [] and h.uow.commits == 0


async def test_resend_inside_cooldown_is_refused_and_after_it_supersedes_the_old_code() -> None:
    h = Harness()
    await h.request()
    with pytest.raises(RateLimitedError) as info:
        await h.request()
    assert 0 < info.value.retry_after_seconds <= 61

    h.clock.advance(seconds=61)
    await h.request()
    assert len(h.challenges.items) == 2
    assert h.challenges.items[0].superseded_at is not None
    assert h.challenges.items[1].superseded_at is None


async def test_per_mobile_rate_limit_blocks_after_the_configured_number_of_requests() -> None:
    h = Harness(limits=OtpRateLimitPolicy(per_mobile_limit=2))
    for _ in range(2):
        await h.request()
        h.clock.advance(seconds=61)
    with pytest.raises(RateLimitedError):
        await h.request()


async def test_per_ip_rate_limit_applies_across_different_numbers() -> None:
    h = Harness(limits=OtpRateLimitPolicy(per_ip_limit=2))
    await h.request(mobile="09120000001")
    await h.request(mobile="09120000002")
    with pytest.raises(RateLimitedError):
        await h.request(mobile="09120000003")
    await h.request(mobile="09120000003", ip="198.51.100.9")  # another IP is unaffected


async def test_delivery_failure_is_reported() -> None:
    h = Harness(delivery_ok=False)
    with pytest.raises(OtpDeliveryFailedError):
        await h.request()


async def test_rate_limit_window_resets() -> None:
    h = Harness(limits=OtpRateLimitPolicy(per_mobile_limit=1, per_mobile_window_seconds=3600))
    await h.request()
    h.clock.advance(seconds=61)
    with pytest.raises(RateLimitedError):
        await h.request()
    h.clock.advance(seconds=3600)
    await h.request()
    assert len(h.challenges.items) == 2
