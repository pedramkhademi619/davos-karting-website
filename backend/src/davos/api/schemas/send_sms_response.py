import uuid

from pydantic import BaseModel


class SendSmsResponse(BaseModel):
    batch_id: uuid.UUID
    accepted: int
    failed: int
    invalid_numbers: list[str]
