from pydantic import BaseModel, Field

from davos.api.schemas.error_detail import ErrorDetail


class ErrorResponse(BaseModel):
    """Uniform error body. Never contains stack traces or raw provider messages."""

    code: str = Field(examples=["otp_verification_failed"])
    message: str = Field(description="Persian, safe to show to the user")
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: str
