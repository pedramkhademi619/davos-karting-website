from pydantic import BaseModel

from davos.api.schemas.reviewed_interaction_response import ReviewedInteractionResponse


class InteractionPageResponse(BaseModel):
    items: list[ReviewedInteractionResponse]
    total: int
