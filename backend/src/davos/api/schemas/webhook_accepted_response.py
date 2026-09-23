from pydantic import BaseModel


class WebhookAcceptedResponse(BaseModel):
    outcome: str
