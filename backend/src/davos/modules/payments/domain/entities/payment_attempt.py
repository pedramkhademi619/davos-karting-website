from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.payments.domain.errors.invalid_payment_transition_error import InvalidPaymentTransitionError
from davos.modules.payments.domain.events.payment_failed import PaymentFailed
from davos.modules.payments.domain.events.payment_succeeded import PaymentSucceeded
from davos.shared_kernel.domain.aggregate_root import AggregateRoot
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

S = PaymentStatus

# The complete, explicit lifecycle. Anything not listed here is rejected.
_ALLOWED: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    S.CREATED: frozenset({S.REDIRECTED, S.FAILED, S.EXPIRED}),
    S.REDIRECTED: frozenset({S.VERIFYING, S.FAILED, S.EXPIRED}),
    S.VERIFYING: frozenset({S.PAID, S.FAILED, S.UNKNOWN}),
    S.UNKNOWN: frozenset({S.VERIFYING, S.PAID, S.FAILED}),
    S.PAID: frozenset(),
    S.FAILED: frozenset(),
    S.EXPIRED: frozenset(),
}


class PaymentAttempt(AggregateRoot[uuid.UUID]):
    """One payment try for an order. Retrying an order creates a new attempt with its own id and authority."""

    def __init__(
        self,
        *,
        payment_id: uuid.UUID,
        order_ref: str,
        customer_id: uuid.UUID,
        amount: Money,
        status: PaymentStatus,
        created_at: datetime,
        updated_at: datetime,
        expires_at: datetime,
        authority: str | None = None,
        reference_id: str | None = None,
        failure_reason: str | None = None,
    ) -> None:
        super().__init__(payment_id)
        self.order_ref = order_ref
        self.customer_id = customer_id
        self.amount = amount
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.expires_at = expires_at
        self.authority = authority
        self.reference_id = reference_id
        self.failure_reason = failure_reason

    @classmethod
    def create(
        cls,
        *,
        order_ref: str,
        customer_id: uuid.UUID,
        amount: Money,
        now: datetime,
        ttl: timedelta = timedelta(minutes=30),
    ) -> PaymentAttempt:
        if amount.irr <= 0:
            raise ValidationError("مبلغ پرداخت باید بیشتر از صفر باشد.", code="payment_amount_not_positive")
        return cls(
            payment_id=uuid.uuid4(),
            order_ref=order_ref,
            customer_id=customer_id,
            amount=amount,
            status=S.CREATED,
            created_at=now,
            updated_at=now,
            expires_at=now + ttl,
        )

    def _transition(self, target: PaymentStatus, now: datetime) -> None:
        if target not in _ALLOWED[self.status]:
            raise InvalidPaymentTransitionError(self.status.value, target.value)
        self.status = target
        self.updated_at = now

    def mark_redirected(self, authority: str, now: datetime) -> None:
        self._transition(S.REDIRECTED, now)
        self.authority = authority

    def begin_verification(self, now: datetime) -> None:
        self._transition(S.VERIFYING, now)

    def mark_paid(self, reference_id: str, now: datetime) -> None:
        self._transition(S.PAID, now)
        self.reference_id = reference_id
        self._raise(
            PaymentSucceeded(
                payment_id=self.id,
                order_ref=self.order_ref,
                customer_id=self.customer_id,
                amount_irr=self.amount.irr,
                reference_id=reference_id,
                occurred_at=now,
            )
        )

    def mark_failed(self, reason: str, now: datetime) -> None:
        self._transition(S.FAILED, now)
        self.failure_reason = reason
        self._raise(
            PaymentFailed(
                payment_id=self.id,
                order_ref=self.order_ref,
                customer_id=self.customer_id,
                reason=reason,
                occurred_at=now,
            )
        )

    def mark_unknown(self, now: datetime) -> None:
        """Verification did not complete. The money may or may not have moved: keep it reconcilable."""
        self._transition(S.UNKNOWN, now)

    def expire(self, now: datetime) -> None:
        self._transition(S.EXPIRED, now)

    def is_expired_at(self, now: datetime) -> bool:
        return self.status in {S.CREATED, S.REDIRECTED} and now >= self.expires_at
