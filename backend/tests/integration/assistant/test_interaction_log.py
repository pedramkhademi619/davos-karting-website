from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.persistence.sqlalchemy_interaction_log import SqlAlchemyInteractionLog
from davos.modules.assistant.application.use_cases.ask_assistant_command import AskAssistantCommand
from davos.modules.assistant.application.use_cases.index_knowledge_entry_command import IndexKnowledgeEntryCommand
from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.assistant_policy import AssistantPolicy
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError
from tests.fakes.scripted_ai_chat import ScriptedAiChat

pytestmark = pytest.mark.integration

_SELECT_INTERACTION = text(
    "SELECT outcome, prompt_tokens, completion_tokens, question_text, answer_text FROM assistant_interactions"
)


async def _seed(container: ApplicationContainer) -> None:
    await container.index_knowledge_entry().execute(
        IndexKnowledgeEntryCommand(
            KnowledgeSourceType.POLICY,
            "cancel",
            "لغو رزرو",
            "برای لغو رزرو ۲۴ ساعت قبل اقدام کنید. (متن نمونه)",
            "/policies/cancellation",
            True,
        )
    )


async def test_end_to_end_answer_uses_real_retrieval_and_persists_the_interaction(
    container: ApplicationContainer, ai_chat: ScriptedAiChat, engine: AsyncEngine
) -> None:
    await _seed(container)
    ai_chat.reply = "می‌توانید ۲۴ ساعت قبل لغو کنید [1]."
    answer = await container.ask_assistant().execute(
        AskAssistantCommand(text="چطور رزرو را لغو کنم؟", client_ip="203.0.113.7")
    )

    assert answer.outcome is AnswerOutcome.ANSWERED
    assert [s.url for s in answer.sources] == ["/policies/cancellation"]
    assert "لغو رزرو" in ai_chat.user_prompt  # the retrieved passage, not the whole site, was sent
    async with engine.connect() as conn:
        row = (await conn.execute(_SELECT_INTERACTION)).one()
    assert row.outcome == "answered" and row.prompt_tokens > 0
    assert row.question_text is None and row.answer_text is None  # no consent -> no text stored


async def test_unknown_topic_in_a_large_knowledge_base_is_answered_without_calling_the_model(
    container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    container._assistant_policy = AssistantPolicy(whole_knowledge_max_entries=0)  # "large": never sent whole
    await _seed(container)
    answer = await container.ask_assistant().execute(
        AskAssistantCommand(text="قیمت بیت کوین امروز چند است؟", client_ip="203.0.113.7")
    )
    assert answer.outcome is AnswerOutcome.INSUFFICIENT_INFORMATION and answer.suggest_ticket
    assert ai_chat.calls == 0


async def test_unknown_topic_in_a_small_knowledge_base_is_declined_by_the_model_itself(
    container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    ai_chat.reply = "NO_ANSWER"
    await _seed(container)
    answer = await container.ask_assistant().execute(
        AskAssistantCommand(text="قیمت بیت کوین امروز چند است؟", client_ip="203.0.113.7")
    )
    assert answer.outcome is AnswerOutcome.INSUFFICIENT_INFORMATION and answer.suggest_ticket
    assert answer.sources == () and ai_chat.calls == 1  # the small base is sent whole, the model says it cannot answer


async def test_draft_content_is_never_visible_to_the_assistant(
    container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    await container.index_knowledge_entry().execute(
        IndexKnowledgeEntryCommand(KnowledgeSourceType.FAQ, "secret", "تخفیف داخلی مدیران", "متن پیش نویس", "/x", False)
    )
    answer = await container.ask_assistant().execute(
        AskAssistantCommand(text="تخفیف داخلی مدیران چیست؟", client_ip="203.0.113.7")
    )
    assert answer.outcome is AnswerOutcome.INSUFFICIENT_INFORMATION and ai_chat.calls == 0


async def test_consented_conversation_is_stored_then_feedback_and_purge_work(
    container: ApplicationContainer, ai_chat: ScriptedAiChat, engine: AsyncEngine, clock
) -> None:
    await _seed(container)
    ai_chat.reply = "لغو ممکن است [1]."
    conversation = uuid.uuid4()
    answer = await container.ask_assistant().execute(
        AskAssistantCommand(
            text="لغو رزرو چطور است؟", client_ip="203.0.113.7", conversation_id=conversation, consent_to_store=True
        )
    )
    assert answer.interaction_id is not None
    log = SqlAlchemyInteractionLog(container.session_factory)
    assert await log.count_in_conversation(conversation) == 1

    await container.submit_assistant_feedback().execute(interaction_id=answer.interaction_id, helpful=False)
    async with engine.connect() as conn:
        row = (await conn.execute(text("SELECT question_text, helpful FROM assistant_interactions"))).one()
    assert row.question_text == "لغو رزرو چطور است؟" and row.helpful is False

    assert await container.purge_expired_interactions().execute() == 0
    clock.advance(days=91)
    assert await container.purge_expired_interactions().execute() == 1
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM assistant_interactions"))).scalar_one() == 0


async def test_feedback_for_an_unknown_interaction_is_not_found(container: ApplicationContainer) -> None:
    with pytest.raises(NotFoundError):
        await container.submit_assistant_feedback().execute(interaction_id=uuid.uuid4(), helpful=True)


async def test_retention_date_is_stored_in_utc(container: ApplicationContainer, engine: AsyncEngine, clock) -> None:
    await _seed(container)
    await container.ask_assistant().execute(AskAssistantCommand(text="لغو رزرو", client_ip="203.0.113.7"))
    async with engine.connect() as conn:
        retention = (await conn.execute(text("SELECT retention_until FROM assistant_interactions"))).scalar_one()
    assert retention == clock.now() + timedelta(days=90)
