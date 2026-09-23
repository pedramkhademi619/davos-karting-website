from pydantic import BaseModel, ConfigDict, Field


class RequestOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mobile: str = Field(min_length=10, max_length=20, examples=["09123456789"])
