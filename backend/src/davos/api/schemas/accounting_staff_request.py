from pydantic import BaseModel, Field


class AccountingStaffRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    title: str = Field(default="", max_length=80)
    mobile: str = Field(default="", max_length=20)
    monthly_salary_toman: int = Field(default=0, ge=0, le=100_000_000_000)
    note: str = Field(default="", max_length=300)
    active: bool = True
