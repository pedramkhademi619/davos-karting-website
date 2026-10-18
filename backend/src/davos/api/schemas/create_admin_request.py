from typing import Literal

from pydantic import BaseModel, Field

from davos.modules.administration.domain.enums.admin_permission import AdminPermission


class CreateAdminRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: str = Field(default="", max_length=60)
    password: str = Field(min_length=12, max_length=200)
    role: Literal["owner", "staff"] = "staff"
    permissions: list[AdminPermission] | None = None  # None = the staff defaults
