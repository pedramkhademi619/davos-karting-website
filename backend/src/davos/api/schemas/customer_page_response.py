from pydantic import BaseModel

from davos.api.schemas.customer_response import CustomerResponse


class CustomerPageResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
