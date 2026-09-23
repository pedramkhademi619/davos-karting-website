from pydantic import BaseModel


class RequestOtpResponse(BaseModel):
    expires_in_seconds: int
    resend_after_seconds: int
