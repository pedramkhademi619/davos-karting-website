import uuid
from datetime import UTC, datetime, timedelta

import pytest

from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.payments.domain.errors.invalid_payment_transition_error import InvalidPaymentTransitionError
from davos.modules.payments.domain.events.payment_failed import PaymentFailed
from davos.modules.payments.domain.events.payment_succeeded import PaymentSucceeded
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
S = PaymentStatus


def make(status: PaymentStatus = S.CREATED) -> PaymentAttempt:
    payment = PaymentAttempt.create(order_ref="order-1", customer_id=uuid.uuid4(), amount=Money(100_000), now=NOW)
    payment.status = status
    if status is not S.CREATED:
        payment.authority = "A" * 36
    return payment


ACTIONS = {
    S.REDIRECTED: lambda p: p.mark_redirected("A" * 36, NOW),
    S.VERIFYING: lambda p: p.begin_verification(NOW),
    S.PAID: lambda p: p.mark_paid("777", NOW),
    S.FAILED: lambda p: p.mark_failed("nope", NOW),
    S.UNKNOWN: lambda p: p.mark_unknown(NOW),
    S.EXPIRED: lambda p: p.expire(NOW),
}
ALLOWED = {
    (S.CREATED, S.REDIRECTED),
    (S.CREATED, S.FAILED),
    (S.CREATED, S.EXPIRED),
    (S.REDIRECTED, S.VERIFYING),
    (S.REDIRECTED, S.FAILED),
    (S.REDIRECTED, S.EXPIRED),
    (S.VERIFYING, S.PAID),
    (S.VERIFYING, S.FAILED),
    (S.VERIFYING, S.UNKNOWN),
    (S.UNKNOWN, S.VERIFYING),
    (S.UNKNOWN, S.PAID),
    (S.UNKNOWN, S.FAILED),
}


@pytest.mark.parametrize(("start", "target"), [(a, b) for a in S for b in ACTIONS])
def test_every_transition_is_either_explicitly_allowed_or_rejected(start: PaymentStatus, target: PaymentStatus) -> None:
    payment = make(start)
    if (start, target) in ALLOWED:
        ACTIONS[target](payment)
        assert payment.status is target
    else:
        with pytest.raises(InvalidPaymentTransitionError):
            ACTIONS[target](payment)
        assert payment.status is start  # a rejected transition changes nothing


def test_terminal_states_are_final() -> None:
    assert {s for s in S if s.is_terminal} == {S.PAID, S.FAILED, S.EXPIRED}


def test_success_raises_exactly_one_event_with_the_reference() -> None:
    payment = make(S.VERIFYING)
    payment.mark_paid("777", NOW)
    events = payment.pull_events()
    assert len(events) == 1 and isinstance(events[0], PaymentSucceeded)
    assert events[0].reference_id == "777" and events[0].amount_irr == 100_000
    assert payment.pull_events() == []


def test_failure_raises_a_failure_event() -> None:
    payment = make(S.VERIFYING)
    payment.mark_failed("verification_rejected", NOW)
    assert isinstance(payment.pull_events()[0], PaymentFailed)


@pytest.mark.parametrize("irr", [0, -5])
def test_amount_must_be_positive(irr: int) -> None:
    with pytest.raises((ValidationError,)):
        PaymentAttempt.create(order_ref="o", customer_id=uuid.uuid4(), amount=Money(irr), now=NOW)


def test_only_open_attempts_expire_by_time() -> None:
    later = NOW + timedelta(minutes=31)
    assert make(S.REDIRECTED).is_expired_at(later)
    assert not make(S.REDIRECTED).is_expired_at(NOW + timedelta(minutes=1))
    assert not make(S.PAID).is_expired_at(later)
    assert not make(S.UNKNOWN).is_expired_at(later)  # unknown must be reconciled, not silently expired


def test_each_attempt_has_its_own_identifier() -> None:
    a, b = make(), make()
    assert a.id != b.id
