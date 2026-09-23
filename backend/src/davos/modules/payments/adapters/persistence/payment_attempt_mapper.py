from __future__ import annotations

from davos.modules.payments.adapters.persistence.payment_attempt_model import PaymentAttemptModel
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.shared_kernel.domain.money import Money


class PaymentAttemptMapper:
    @staticmethod
    def to_domain(model: PaymentAttemptModel) -> PaymentAttempt:
        return PaymentAttempt(
            payment_id=model.id,
            order_ref=model.order_ref,
            customer_id=model.customer_id,
            amount=Money(model.amount_irr),
            status=PaymentStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            expires_at=model.expires_at,
            authority=model.authority,
            reference_id=model.reference_id,
            failure_reason=model.failure_reason,
        )

    @staticmethod
    def to_model(payment: PaymentAttempt) -> PaymentAttemptModel:
        return PaymentAttemptModel(
            id=payment.id,
            order_ref=payment.order_ref,
            customer_id=payment.customer_id,
            amount_irr=payment.amount.irr,
            status=payment.status.value,
            authority=payment.authority,
            reference_id=payment.reference_id,
            failure_reason=payment.failure_reason,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            expires_at=payment.expires_at,
        )
