from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, Response

from davos.api.dependencies.client_ip import client_ip
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.answer_source_response import AnswerSourceResponse
from davos.api.schemas.ask_assistant_request import AskAssistantRequest
from davos.api.schemas.assistant_answer_response import AssistantAnswerResponse
from davos.api.schemas.assistant_feedback_request import AssistantFeedbackRequest
from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.application.use_cases.ask_assistant_command import AskAssistantCommand
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError

router = APIRouter(prefix="/assistant", tags=["assistant"])


async def _optional_user_id(request: Request, container: ApplicationContainer) -> uuid.UUID | None:
    raw = request.cookies.get(container.settings.session_cookie_name, "")
    customer = await container.authenticate_session().execute(raw) if raw else None
    return customer.user_id if customer else None


@router.post("/ask", summary="Ask the Davos assistant (answers only from published content)")
async def ask(
    body: AskAssistantRequest,
    request: Request,
    ip: str = Depends(client_ip),
    container: ApplicationContainer = Depends(get_container),
) -> AssistantAnswerResponse:
    answer = await container.ask_assistant().execute(
        AskAssistantCommand(
            text=body.question,
            client_ip=ip,
            conversation_id=body.conversation_id,
            user_id=await _optional_user_id(request, container),
            consent_to_store=body.consent_to_store,
        )
    )
    return AssistantAnswerResponse(
        answer=answer.text,
        outcome=answer.outcome.value,
        sources=[AnswerSourceResponse(title=s.title, url=s.url) for s in answer.sources],
        suggest_ticket=answer.suggest_ticket,
        interaction_id=answer.interaction_id,
    )


@router.post("/answers/{interaction_id}/feedback", status_code=204, summary="Was the answer helpful?")
async def feedback(
    interaction_id: str,
    body: AssistantFeedbackRequest,
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    try:
        target = uuid.UUID(interaction_id)
    except ValueError as exc:
        raise NotFoundError("پاسخ موردنظر یافت نشد.") from exc
    await container.submit_assistant_feedback().execute(interaction_id=target, helpful=body.helpful)
    return Response(status_code=204)
