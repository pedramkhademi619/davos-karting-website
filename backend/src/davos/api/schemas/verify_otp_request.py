from pydantic import BaseModel, ConfigDict, Field


class VerifyOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mobile: str = Field(min_length=10, max_length=20)
    code: str = Field(min_length=4, max_length=8)
