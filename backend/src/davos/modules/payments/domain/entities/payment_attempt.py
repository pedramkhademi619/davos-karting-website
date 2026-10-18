from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.payments.domain.errors.invalid_payment_transition_error import InvalidPaymentTransitionError
from davos.modules.payments.domain.events.payment_failed import PaymentFailed
from davos.modules.payments.domain.events.payment_reversed import PaymentReversed
from davos.modules.payments.domain.events.payment_succeeded import PaymentSucceeded
from davos.shared_kernel.domain.aggregate_root import AggregateRoot
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

S = PaymentStatus

# The complete, explicit lifecycle. Anything not listed here is rejected.
_ALLOWED: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    S.CREATED: frozenset({S.REDIRECTED, S.FAILED, S.EXPIRED}),
    S.REDIRECTED: frozenset({S.VERIFYING, S.FAILED, S.EXPIRED}),
    S.VERIFYING: frozenset({S.PAID, S.FAILED, S.UNKNOWN, S.REFUND_PENDING}),
    S.UNKNOWN: frozenset({S.VERIFYING, S.PAID, S.FAILED, S.REFUND_PENDING}),
    S.PAID: frozenset({S.REVERSED}),  # only when the bank itself reversed an unsettled payment
    S.REFUND_PENDING: frozenset({S.REVERSED}),
    S.FAILED: frozenset(),
    S.EXPIRED: frozenset(),
    S.REVERSED: frozenset(),
}


class PaymentAttempt(AggregateRoot[uuid.UUID]):
    """One payment try for an order. Retrying an order creates a new attempt with its own ids.

    ``gateway_order_id`` is the unique numeric order id sent to the bank (never reused). ``authority`` is the
    gateway's token for the attempt (Mellat RefId, Zarinpal authority). ``provider_reference`` is the bank's
    reference for the money movement (Mellat SaleReferenceId); it is unique across all attempts, so one bank
    transaction can never pay for two orders.
    """

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
        gateway: str = "",
        gateway_order_id: int | None = None,
        authority: str | None = None,
        provider_reference: str | None = None,
        reference_id: str | None = None,
        failure_reason: str | None = None,
        settled_at: datetime | None = None,
    ) -> None:
        super().__init__(payment_id)
        self.order_ref = order_ref
        self.customer_id = customer_id
        self.amount = amount
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.expires_at = expires_at
        self.gateway = gateway
        self.gateway_order_id = gateway_order_id
        self.authority = authority
        self.provider_reference = provider_reference
        self.reference_id = reference_id
        self.failure_reason = failure_reason
        self.settled_at = settled_at

    @classmethod
    def create(
        cls,
        *,
        order_ref: str,
        customer_id: uuid.UUID,
        amount: Money,
        now: datetime,
        gateway: str = "",
        gateway_order_id: int | None = None,
        ttl: timedelta,
    ) -> PaymentAttempt:
        if amount.irr <= 0:
            raise ValidationError("مبلغ پرداخت باید بیشتر از صفر باشد.", code="payment_amount_not_positive")
        if gateway_order_id is not None and gateway_order_id <= 0:
            raise ValidationError("شماره سفارش درگاه معتبر نیست.", code="gateway_order_id_invalid")
        return cls(
            payment_id=uuid.uuid4(),
            order_ref=order_ref,
            customer_id=customer_id,
            amount=amount,
            status=S.CREATED,
            created_at=now,
            updated_at=now,
            expires_at=now + ttl,
            gateway=gateway,
            gateway_order_id=gateway_order_id,
        )

    @property
    def needs_settlement(self) -> bool:
        return self.status is S.PAID and self.settled_at is None

    def _transition(self, target: PaymentStatus, now: datetime) -> None:
        if target not in _ALLOWED[self.status]:
            raise InvalidPaymentTransitionError(self.status.value, target.value)
        self.status = target
        self.updated_at = now

    def mark_redirected(self, authority: str, now: datetime) -> None:
        if not authority:
            raise ValidationError("شناسه درگاه خالی است.", code="authority_missing")
        self._transition(S.REDIRECTED, now)
        self.authority = authority

    def record_provider_reference(self, reference: str, now: datetime) -> None:
        """The bank's sale reference from the callback. Set once; a different value later is refused."""
        reference = reference.strip()
        if not reference or len(reference) > 64 or not (reference.isascii() and reference.isdigit()):
            raise ValidationError("شماره مرجع بانک معتبر نیست.", code="provider_reference_invalid")
        if self.provider_reference is not None and self.provider_reference != reference:
            raise InvalidPaymentTransitionError(self.status.value, "provider_reference_changed")
        if self.status not in {S.REDIRECTED, S.UNKNOWN}:
            raise InvalidPaymentTransitionError(self.status.value, "provider_reference")
        self.provider_reference = reference
        self.updated_at = now

    def begin_verification(self, now: datetime) -> None:
        self._transition(S.VERIFYING, now)

    def mark_paid(self, reference_id: str, now: datetime) -> None:
        if not reference_id:
            raise ValidationError("شماره پیگیری پرداخت خالی است.", code="reference_missing")
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

    def mark_settled(self, now: datetime) -> None:
        if self.status is not S.PAID:
            raise InvalidPaymentTransitionError(self.status.value, "settled")
        if self.settled_at is None:
            self.settled_at = now
            self.updated_at = now

    def mark_refund_pending(self, reason: str, reference_id: str | None, now: datetime) -> None:
        """Verified money that the order will not take (paid twice, or the order is no longer valid)."""
        self._transition(S.REFUND_PENDING, now)
        self.failure_reason = reason[:64]
        self.reference_id = reference_id

    def mark_reversed(self, now: datetime) -> None:
        was_paid = self.status is S.PAID
        if was_paid and self.settled_at is not None:
            raise InvalidPaymentTransitionError(self.status.value, S.REVERSED.value)
        self._transition(S.REVERSED, now)
        self._raise(
            PaymentReversed(
                payment_id=self.id,
                order_ref=self.order_ref,
                customer_id=self.customer_id,
                amount_irr=self.amount.irr,
                was_paid=was_paid,
                occurred_at=now,
            )
        )

    def mark_failed(self, reason: str, now: datetime) -> None:
        self._transition(S.FAILED, now)
        self.failure_reason = reason[:64]
        self._raise(
            PaymentFailed(
                payment_id=self.id,
                order_ref=self.order_ref,
                customer_id=self.customer_id,
                reason=self.failure_reason,
                occurred_at=now,
            )
        )

    def mark_unknown(self, now: datetime) -> None:
        """Verification did not complete. The money may or may not have moved: keep it reconcilable."""
        self._transition(S.UNKNOWN, now)

    def expire(self, now: datetime) -> None:
        self._transition(S.EXPIRED, now)

    def is_expired_at(self, now: datetime) -> bool:
        """Only an attempt the bank has never reported back on can expire; one with a sale reference is verified."""
        return self.status in {S.CREATED, S.REDIRECTED} and self.provider_reference is None and now >= self.expires_at
