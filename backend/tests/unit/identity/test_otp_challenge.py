from datetime import UTC, datetime, timedelta

from davos.modules.identity.domain.entities.otp_challenge import OtpChallenge
from davos.modules.identity.domain.enums.otp_verification_result import OtpVerificationResult
from davos.modules.identity.domain.value_objects.otp_policy import OtpPolicy
from tests.fakes.standard_config import otp_policy

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _challenge(policy: OtpPolicy | None = None) -> OtpChallenge:
    return OtpChallenge.issue(mobile="+989123456789", code_digest="right", now=NOW, policy=policy or otp_policy())


def test_correct_code_verifies_once() -> None:
    challenge = _challenge()
    assert challenge.verify("right", NOW) is OtpVerificationResult.VERIFIED
    assert challenge.verify("right", NOW) is OtpVerificationResult.ALREADY_USED


def test_wrong_code_counts_attempts_then_locks_even_for_the_right_code() -> None:
    challenge = _challenge(otp_policy(max_attempts=3))
    for _ in range(3):
        assert challenge.verify("wrong", NOW) is OtpVerificationResult.WRONG_CODE
    assert challenge.attempts == 3
    assert challenge.verify("right", NOW) is OtpVerificationResult.LOCKED


def test_expired_code_is_rejected() -> None:
    challenge = _challenge(otp_policy(ttl_seconds=120))
    assert challenge.verify("right", NOW + timedelta(seconds=120)) is OtpVerificationResult.EXPIRED
    assert challenge.attempts == 0


def test_superseded_code_is_rejected() -> None:
    challenge = _challenge()
    challenge.supersede(NOW)
    assert challenge.verify("right", NOW) is OtpVerificationResult.SUPERSEDED


def test_supersede_does_not_touch_a_consumed_challenge() -> None:
    challenge = _challenge()
    challenge.verify("right", NOW)
    challenge.supersede(NOW)
    assert challenge.superseded_at is None
