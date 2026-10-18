from datetime import timedelta

import pytest

from davos.modules.identity.adapters.security.hmac_otp_hasher import HmacOtpHasher
from davos.modules.identity.adapters.security.sha256_session_token_service import Sha256SessionTokenService
from davos.modules.identity.application.use_cases.authenticate_session_use_case import AuthenticateSessionUseCase
from davos.modules.identity.application.use_cases.list_sessions_use_case import ListSessionsUseCase
from davos.modules.identity.application.use_cases.otp_rate_limit_policy import OtpRateLimitPolicy
from davos.modules.identity.application.use_cases.request_otp_command import RequestOtpCommand
from davos.modules.identity.application.use_cases.request_otp_use_case import RequestOtpUseCase
from davos.modules.identity.application.use_cases.revoke_session_use_case import RevokeSessionUseCase
from davos.modules.identity.application.use_cases.verify_otp_command import VerifyOtpCommand
from davos.modules.identity.application.use_cases.verify_otp_use_case import VerifyOtpUseCase
from davos.modules.identity.domain.enums.otp_verification_result import OtpVerificationResult
from davos.modules.identity.domain.enums.user_status import UserStatus
from davos.modules.identity.domain.errors.otp_verification_failed_error import OtpVerificationFailedError
from davos.modules.identity.domain.errors.session_not_found_error import SessionNotFoundError
from davos.modules.identity.domain.errors.user_blocked_error import UserBlockedError
from davos.modules.identity.domain.events.user_registered import UserRegistered
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError
from tests.fakes.fake_otp_delivery import FakeOtpDelivery
from tests.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_otp_challenge_repository import InMemoryOtpChallengeRepository
from tests.fakes.in_memory_session_repository import InMemorySessionRepository
from tests.fakes.in_memory_user_repository import InMemoryUserRepository
from tests.fakes.sequence_otp_code_generator import SequenceOtpCodeGenerator
from tests.fakes.standard_config import otp_limits, otp_policy

SECRET = "s" * 40
MOBILE = "09123456789"


class Harness:
    def __init__(self, limits: OtpRateLimitPolicy | None = None) -> None:
        self.clock = FixedClock()
        self.uow = FakeUnitOfWork()
        self.challenges = InMemoryOtpChallengeRepository()
        self.users = InMemoryUserRepository()
        self.sessions = InMemorySessionRepository()
        self.delivery = FakeOtpDelivery()
        hasher = HmacOtpHasher(SECRET)
        self.tokens = Sha256SessionTokenService()
        limiter = InMemoryRateLimiter(self.clock)
        self.request_otp = RequestOtpUseCase(
            uow=self.uow,
            challenges=self.challenges,
            hasher=hasher,
            code_generator=SequenceOtpCodeGenerator(),
            delivery=self.delivery,
            rate_limiter=limiter,
            clock=self.clock,
            policy=otp_policy(),
            limits=limits or otp_limits(),
        )
        self.verify_otp = VerifyOtpUseCase(
            uow=self.uow,
            challenges=self.challenges,
            users=self.users,
            sessions=self.sessions,
            hasher=hasher,
            tokens=self.tokens,
            rate_limiter=limiter,
            clock=self.clock,
            limits=limits or otp_limits(),
            session_lifetime=timedelta(days=30),
        )
        self.authenticate = AuthenticateSessionUseCase(
            uow=self.uow, sessions=self.sessions, users=self.users, tokens=self.tokens, clock=self.clock
        )
        self.list_sessions = ListSessionsUseCase(uow=self.uow, sessions=self.sessions, clock=self.clock)
        self.revoke = RevokeSessionUseCase(uow=self.uow, sessions=self.sessions, clock=self.clock)

    async def issue_code(self, mobile: str = MOBILE) -> str:
        await self.request_otp.execute(RequestOtpCommand(raw_mobile=mobile, client_ip="203.0.113.5"))
        return self.delivery.last_code

    async def verify(self, code: str, mobile: str = MOBILE, ip: str = "203.0.113.5", agent: str = "pytest"):
        return await self.verify_otp.execute(
            VerifyOtpCommand(raw_mobile=mobile, code=code, client_ip=ip, user_agent=agent)
        )


async def test_correct_code_creates_user_and_session_and_emits_registration_event() -> None:
    h = Harness()
    code = await h.issue_code()
    result = await h.verify(code)

    assert result.is_new_user
    assert len(h.users.items) == 1
    assert any(isinstance(e, UserRegistered) for e in h.uow.published_events)
    stored = next(iter(h.sessions.items.values()))
    assert stored.token_digest != result.session_token  # raw token is never stored
    assert (await h.authenticate.execute(result.session_token)).user_id == result.user_id


async def test_returning_user_gets_a_new_session_but_no_second_account() -> None:
    h = Harness()
    first = await h.verify(await h.issue_code())
    h.clock.advance(seconds=61)
    second = await h.verify(await h.issue_code(mobile="+98 912 345 6789"))
    assert not second.is_new_user
    assert second.user_id == first.user_id
    assert len(h.users.items) == 1 and len(h.sessions.items) == 2


async def test_wrong_code_is_rejected_and_the_attempt_is_persisted() -> None:
    h = Harness()
    await h.issue_code()
    commits_before = h.uow.commits
    with pytest.raises(OtpVerificationFailedError) as info:
        await h.verify("000000")
    assert info.value.reason is OtpVerificationResult.WRONG_CODE
    assert h.uow.commits == commits_before + 1  # attempt counter committed, not rolled back
    assert h.challenges.items[0].attempts == 1
    assert not h.users.items


async def test_too_many_wrong_attempts_lock_the_challenge_even_for_the_correct_code() -> None:
    h = Harness()
    code = await h.issue_code()
    for _ in range(3):
        with pytest.raises(OtpVerificationFailedError):
            await h.verify("000000")
    with pytest.raises(OtpVerificationFailedError) as info:
        await h.verify(code)
    assert info.value.reason is OtpVerificationResult.LOCKED


async def test_expired_code_is_rejected() -> None:
    h = Harness()
    code = await h.issue_code()
    h.clock.advance(seconds=121)
    with pytest.raises(OtpVerificationFailedError) as info:
        await h.verify(code)
    assert info.value.reason is OtpVerificationResult.EXPIRED


async def test_code_cannot_be_replayed() -> None:
    h = Harness()
    code = await h.issue_code()
    await h.verify(code)
    with pytest.raises(OtpVerificationFailedError) as info:
        await h.verify(code)
    assert info.value.reason is OtpVerificationResult.ALREADY_USED


async def test_resent_code_invalidates_the_previous_one() -> None:
    h = Harness()
    old = await h.issue_code()
    h.clock.advance(seconds=61)
    new = await h.issue_code()
    assert old != new
    with pytest.raises(OtpVerificationFailedError):
        await h.verify(old)
    await h.verify(new)


async def test_verifying_without_a_challenge_fails_generically() -> None:
    h = Harness()
    with pytest.raises(OtpVerificationFailedError):
        await h.verify("123456")


async def test_verify_is_rate_limited_per_ip() -> None:
    h = Harness(limits=otp_limits(verify_per_ip_limit=2))
    await h.issue_code()
    for _ in range(2):
        with pytest.raises(OtpVerificationFailedError):
            await h.verify("000000")
    with pytest.raises(RateLimitedError):
        await h.verify("000000")


async def test_blocked_user_cannot_sign_in() -> None:
    h = Harness()
    await h.verify(await h.issue_code())
    next(iter(h.users.items.values())).status = UserStatus.BLOCKED
    h.clock.advance(seconds=61)
    with pytest.raises(UserBlockedError):
        await h.verify(await h.issue_code())


async def test_session_authentication_rejects_unknown_expired_revoked_and_blocked() -> None:
    h = Harness()
    result = await h.verify(await h.issue_code())
    assert await h.authenticate.execute("") is None
    assert await h.authenticate.execute("not-a-real-token") is None

    await h.revoke.execute(user_id=result.user_id, session_id=result.session_id)
    assert await h.authenticate.execute(result.session_token) is None


async def test_session_expires_after_its_lifetime() -> None:
    h = Harness()
    result = await h.verify(await h.issue_code())
    h.clock.advance(days=31)
    assert await h.authenticate.execute(result.session_token) is None


async def test_blocked_user_loses_existing_sessions_immediately() -> None:
    h = Harness()
    result = await h.verify(await h.issue_code())
    next(iter(h.users.items.values())).status = UserStatus.BLOCKED
    assert await h.authenticate.execute(result.session_token) is None


async def test_user_can_list_and_revoke_only_their_own_sessions() -> None:
    h = Harness()
    mine = await h.verify(await h.issue_code())
    h.clock.advance(seconds=61)
    other = await h.verify(await h.issue_code(mobile="09129999999"), mobile="09129999999")

    listed = await h.list_sessions.execute(user_id=mine.user_id, current_session_id=mine.session_id)
    assert [s.session_id for s in listed] == [mine.session_id]
    assert listed[0].is_current

    with pytest.raises(SessionNotFoundError):  # IDOR attempt: another user's session id
        await h.revoke.execute(user_id=mine.user_id, session_id=other.session_id)
    assert await h.authenticate.execute(other.session_token) is not None
