from pydantic import BaseModel

from davos.api.schemas.sms_log_response import SmsLogResponse


class SmsLogPageResponse(BaseModel):
    items: list[SmsLogResponse]
    total: int
