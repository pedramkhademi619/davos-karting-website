from __future__ import annotations

from fastapi import APIRouter, Depends

from davos.api.dependencies.admin_authentication import require_admin
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.admin_guide_request import AdminGuideRequest
from davos.composition.application_container import ApplicationContainer
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError

router = APIRouter(prefix="/admin/guide", tags=["admin"])

_PER_HOUR = 60


@router.post("/ask", summary="Ask the panel's own helper how to do something in the panel (any signed-in staff)")
async def ask(
    body: AdminGuideRequest,
    auth: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, str]:
    decision = await container.rate_limiter.hit(
        f"admin-guide:{auth.admin.admin_id}", limit=_PER_HOUR, window_seconds=3600
    )
    if not decision.allowed:
        raise RateLimitedError(
            "سؤال‌های این ساعت زیاد شد؛ کمی بعد دوباره بپرسید.", retry_after_seconds=decision.retry_after_seconds
        )
    answer = await container.admin_guide().ask([(m.role, m.content) for m in body.messages])
    return {"answer": answer}
