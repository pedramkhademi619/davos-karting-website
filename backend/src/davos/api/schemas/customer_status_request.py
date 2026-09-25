from typing import Literal

from pydantic import BaseModel


class CustomerStatusRequest(BaseModel):
    status: Literal["active", "blocked"]
