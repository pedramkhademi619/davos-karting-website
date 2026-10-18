from pydantic import BaseModel


class RequestOtpResponse(BaseModel):
    expires_in_seconds: int
    resend_after_seconds: int
    # Local development only (DEV_SMS_ECHO_ENABLED; production refuses to start with it): no SMS is sent, so the code.
    dev_code: str | None = None
