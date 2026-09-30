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
            gateway=model.gateway,
            gateway_order_id=model.gateway_order_id,
            authority=model.authority,
            provider_reference=model.provider_reference,
            reference_id=model.reference_id,
            failure_reason=model.failure_reason,
            settled_at=model.settled_at,
        )

    @staticmethod
    def to_model(payment: PaymentAttempt) -> PaymentAttemptModel:
        return PaymentAttemptModel(
            id=payment.id,
            order_ref=payment.order_ref,
            customer_id=payment.customer_id,
            amount_irr=payment.amount.irr,
            gateway=payment.gateway,
            gateway_order_id=payment.gateway_order_id,
            created_at=payment.created_at,
            expires_at=payment.expires_at,
            **PaymentAttemptMapper.mutable_values(payment),
        )

    @staticmethod
    def mutable_values(payment: PaymentAttempt) -> dict[str, object]:
        return {
            "status": payment.status.value,
            "authority": payment.authority,
            "provider_reference": payment.provider_reference,
            "reference_id": payment.reference_id,
            "failure_reason": payment.failure_reason,
            "updated_at": payment.updated_at,
            "settled_at": payment.settled_at,
        }
