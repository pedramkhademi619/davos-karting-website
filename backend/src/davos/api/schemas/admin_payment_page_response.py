from pydantic import BaseModel

from davos.api.schemas.admin_payment_response import AdminPaymentResponse


class AdminPaymentPageResponse(BaseModel):
    items: list[AdminPaymentResponse]
    total: int
    paid_total_toman: int
