from pydantic import BaseModel

from davos.api.schemas.reservation_response import ReservationResponse


class ReservationPageResponse(BaseModel):
    items: list[ReservationResponse]
    total: int
