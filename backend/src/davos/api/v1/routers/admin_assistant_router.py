from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response

from davos.api.dependencies.admin_authentication import require_admin, require_owner
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.assistant_overview_response import AssistantOverviewResponse
from davos.api.schemas.cached_answer_active_request import CachedAnswerActiveRequest
from davos.api.schemas.cached_answer_page_response import CachedAnswerPageResponse
from davos.api.schemas.cached_answer_response import CachedAnswerResponse
from davos.api.schemas.curated_answer_request import CuratedAnswerRequest
from davos.api.schemas.interaction_page_response import InteractionPageResponse
from davos.api.schemas.knowledge_catalog_response import KnowledgeCatalogResponse
from davos.api.schemas.knowledge_entry_request import KnowledgeEntryRequest
from davos.api.schemas.knowledge_entry_response import KnowledgeEntryResponse
from davos.api.schemas.reviewed_interaction_response import ReviewedInteractionResponse
from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError
from davos.shared_kernel.domain.errors.validation_error import ValidationError

router = APIRouter(prefix="/admin/assistant", tags=["admin"])

# What the review screen's filters mean, in terms of the stored outcome values.
_UNANSWERED = ["insufficient_information", "fallback_provider_unavailable", "fallback_budget_exhausted"]
_FILTERS: dict[str, list[str]] = {"all": [], "unanswered": _UNANSWERED, "answered": ["answered"]}

_KNOWLEDGE_MISSING = "متن دانش یافت نشد."


def _entry_id(raw: str, *, missing: str = "پاسخ ذخیره‌شده یافت نشد.") -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise NotFoundError(missing) from exc


async def _stored_answer(container: ApplicationContainer, entry_id: uuid.UUID) -> CachedAnswerResponse:
    page = await container.assistant_review().cached_answers(active=None, offset=0, limit=1, entry_id=entry_id)
    return CachedAnswerResponse.of(page.items[0])


@router.get("/overview", summary="What the assistant did over the last days")
async def overview(
    days: int = Query(default=7, ge=1, le=365),
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> AssistantOverviewResponse:
    return AssistantOverviewResponse.of(await container.assistant_review().overview(days=days))


@router.get("/interactions", summary="Stored questions, newest first (texts only where the customer agreed)")
async def interactions(
    show: Literal["all", "unanswered", "answered"] = "all",
    helpful: bool | None = None,
    with_text_only: bool = False,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> InteractionPageResponse:
    page = await container.assistant_review().interactions(
        outcomes=_FILTERS[show], helpful=helpful, with_text_only=with_text_only, offset=offset, limit=limit
    )
    return InteractionPageResponse(items=[ReviewedInteractionResponse.of(i) for i in page.items], total=page.total)


@router.get("/cache", summary="Stored answers that are reused for questions with the same meaning")
async def cached_answers(
    active: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> CachedAnswerPageResponse:
    page = await container.assistant_review().cached_answers(active=active, offset=offset, limit=limit)
    return CachedAnswerPageResponse(items=[CachedAnswerResponse.of(r) for r in page.items], total=page.total)


@router.post("/cache", status_code=201, summary="Write a stored answer by hand (owner only)")
async def add_cached_answer(
    body: CuratedAnswerRequest,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> CachedAnswerResponse:
    service = container.curated_answers()
    if service is None:
        raise ValidationError("ذخیرهٔ پاسخ‌ها در این استقرار خاموش است.")
    entry_id = await service.add(question=body.question, answer=body.answer)
    return await _stored_answer(container, entry_id)


@router.put("/cache/{entry_id}", summary="Correct a stored answer; it then becomes the owner's own (owner only)")
async def edit_cached_answer(
    entry_id: str,
    body: CuratedAnswerRequest,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> CachedAnswerResponse:
    service = container.curated_answers()
    if service is None:
        raise ValidationError("ذخیرهٔ پاسخ‌ها در این استقرار خاموش است.")
    target = _entry_id(entry_id)
    await service.edit(target, question=body.question, answer=body.answer)
    return await _stored_answer(container, target)


@router.post("/cache/{entry_id}/active", status_code=204, summary="Retire or bring back a stored answer (owner only)")
async def set_cached_answer_active(
    entry_id: str,
    body: CachedAnswerActiveRequest,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.assistant_review().set_cached_answer_active(_entry_id(entry_id), active=body.active)
    return Response(status_code=204)


@router.delete("/cache/{entry_id}", status_code=204, summary="Delete a stored answer (owner only)")
async def delete_cached_answer(
    entry_id: str,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.assistant_review().delete_cached_answer(_entry_id(entry_id))
    return Response(status_code=204)


@router.get("/knowledge", summary="Everything the assistant answers from, and how it fits the whole-base limit")
async def knowledge(
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> KnowledgeCatalogResponse:
    return KnowledgeCatalogResponse.of(await container.manage_knowledge().catalog())


@router.post("/knowledge", status_code=201, summary="Add a text the assistant may answer from (owner only)")
async def add_knowledge(
    body: KnowledgeEntryRequest,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> KnowledgeEntryResponse:
    entry = await container.manage_knowledge().add(
        source_type=KnowledgeSourceType(body.source_type), title=body.title, body=body.body, url=body.url
    )
    return KnowledgeEntryResponse.of(entry)


@router.put("/knowledge/{entry_id}", summary="Edit a knowledge text (owner only)")
async def edit_knowledge(
    entry_id: str,
    body: KnowledgeEntryRequest,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> KnowledgeEntryResponse:
    entry = await container.manage_knowledge().update(
        _entry_id(entry_id, missing=_KNOWLEDGE_MISSING),
        source_type=KnowledgeSourceType(body.source_type),
        title=body.title,
        body=body.body,
        url=body.url,
    )
    return KnowledgeEntryResponse.of(entry)


@router.delete("/knowledge/{entry_id}", status_code=204, summary="Delete a knowledge text (owner only)")
async def delete_knowledge(
    entry_id: str,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.manage_knowledge().delete(_entry_id(entry_id, missing=_KNOWLEDGE_MISSING))
    return Response(status_code=204)
