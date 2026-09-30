from dataclasses import dataclass

from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class PaymentRequest:
    payment_id: str
    order_ref: str
    amount: Money
    description: str
    callback_url: str
    gateway_order_id: int  # numeric and unique per attempt (Mellat requires a long integer order id)
