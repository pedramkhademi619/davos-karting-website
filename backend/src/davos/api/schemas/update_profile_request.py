from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(default="", max_length=80)
    marketing_opt_in: bool = False
