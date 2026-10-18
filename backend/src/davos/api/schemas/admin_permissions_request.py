from pydantic import BaseModel

from davos.modules.administration.domain.enums.admin_permission import AdminPermission


class AdminPermissionsRequest(BaseModel):
    permissions: list[AdminPermission] | None = None  # None = back to the staff defaults
