"""The answer cache against real PostgreSQL with pgvector: the store, and the whole ask flow on top of it."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.persistence.pg_answer_cache import PgAnswerCache
from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.use_cases.ask_assistant_command import AskAssistantCommand
from davos.modules.assistant.application.use_cases.index_knowledge_entry_command import IndexKnowledgeEntryCommand
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding
from tests.fakes.concept_embedding import ConceptEmbedding
from tests.fakes.scripted_ai_chat import ScriptedAiChat

pytestmark = pytest.mark.integration

PAYMENT = "پرداخت با چه درگاهیه؟"
SAME_TEXT_AGAIN = "پرداخت با چه درگاهیه ؟"  # the same question: the cache also normalises spacing and punctuation


@pytest.fixture
def embedding() -> EmbeddingPort:
    return ConceptEmbedding(dimensions=384)  # the size of the answer cache table's vector column


def vector(*values: float) -> QueryEmbedding:
    """A unit vector in the cache table's 384 dimensions, with the given leading components."""
    padded = [*values, *([0.0] * (384 - len(values)))]
    norm = sum(v * v for v in padded) ** 0.5
    return QueryEmbedding(tuple(v / norm for v in padded))


def entry(question: str, answer: str, embedding: QueryEmbedding, *, fingerprint: str = "f1") -> NewCacheEntry:
    return NewCacheEntry(
        entry_id=uuid.uuid4(),
        original_query=question,
        resolved_query=question,
        signature="",
        embedding=embedding,
        embedding_model="m1",
        fingerprint=fingerprint,
        response=answer,
        sources=(AnswerSource(title="نحوه رزرو", url="/booking"),),
        created_at=datetime(2026, 9, 30, tzinfo=UTC),
    )


async def test_the_store_finds_the_nearest_active_entries_of_the_same_fingerprint_and_model(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    store = PgAnswerCache(container.session_factory)
    near, far, other_fingerprint = (
        entry("نزدیک", "جواب نزدیک", vector(1.0, 0.1)),
        entry("دور", "جواب دور", vector(0.0, 1.0)),
        entry("اثر انگشت دیگر", "جواب دیگر", vector(1.0, 0.0), fingerprint="f2"),
    )
    for item in (near, far, other_fingerprint):
        await store.store(item)

    found = await store.find_candidates(vector(1.0, 0.0), embedding_model="m1", fingerprint="f1", limit=8)
    assert [c.response for c in found] == [
        "جواب نزدیک",
        "جواب دور",
    ]  # nearest first; the other fingerprint is invisible
    assert found[0].similarity > 0.99 and found[1].similarity < 0.01
    assert found[0].question == "نزدیک" and [s.url for s in found[0].sources] == ["/booking"]
    assert await store.find_candidates(vector(1.0, 0.0), embedding_model="another", fingerprint="f1", limit=8) == []


async def test_a_retired_entry_is_never_found_again_and_a_hit_is_counted(container: ApplicationContainer) -> None:
    store = PgAnswerCache(container.session_factory)
    stored = entry("سوال", "جواب", vector(1.0))
    await store.store(stored)
    await store.record_hit(stored.entry_id, datetime(2026, 10, 1, tzinfo=UTC))
    await store.deactivate(stored.entry_id)
    assert await store.find_candidates(vector(1.0), embedding_model="m1", fingerprint="f1", limit=8) == []
    async with container.session_factory() as session:
        row = (await session.execute(text("SELECT hit_count, is_active FROM assistant_answer_cache"))).one()
    assert row.hit_count == 1 and row.is_active is False


async def _publish(container: ApplicationContainer, text_: str = "پرداخت از درگاه بانک ملت انجام می‌شود.") -> None:
    await container.index_knowledge_entry().execute(
        IndexKnowledgeEntryCommand(KnowledgeSourceType.SERVICE, "booking", "نحوه رزرو", text_, "/booking", True)
    )


async def _ask(container: ApplicationContainer, question: str):
    return await container.ask_assistant().execute(AskAssistantCommand(text=question, client_ip="203.0.113.7"))


async def test_the_same_question_asked_again_is_answered_from_the_database_without_the_model(
    container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    await _publish(container)
    ai_chat.reply = "پرداخت از درگاه بانک ملت است [1]."
    first = await _ask(container, PAYMENT)
    second = await _ask(container, SAME_TEXT_AGAIN)
    assert not first.from_cache and second.from_cache
    assert second.text == first.text and [s.url for s in second.sources] == ["/booking"]
    assert ai_chat.calls == 1


async def test_a_not_helpful_vote_retires_the_stored_answer_in_the_database(
    container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    await _publish(container)
    ai_chat.reply = "پرداخت از درگاه بانک ملت است [1]."
    first = await _ask(container, PAYMENT)
    assert first.interaction_id is not None
    await container.submit_assistant_feedback().execute(interaction_id=first.interaction_id, helpful=False)
    again = await _ask(container, PAYMENT)
    assert not again.from_cache and ai_chat.calls == 2


async def test_editing_a_published_text_stops_the_old_answer_from_being_served(
    container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    await _publish(container)
    ai_chat.reply = "پرداخت از درگاه بانک ملت است [1]."
    await _ask(container, PAYMENT)
    await _publish(container, "پرداخت از درگاه بانک دیگری انجام می‌شود.")  # the owner edits the entry
    again = await _ask(container, PAYMENT)
    assert not again.from_cache and ai_chat.calls == 2


async def test_the_interaction_log_says_which_answers_came_from_the_cache(
    container: ApplicationContainer, ai_chat: ScriptedAiChat, engine: AsyncEngine
) -> None:
    await _publish(container)
    ai_chat.reply = "پرداخت از درگاه بانک ملت است [1]."
    await _ask(container, PAYMENT)
    await _ask(container, PAYMENT)
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT served_from_cache, prompt_tokens, cache_entry_id IS NOT NULL AS linked "
                    "FROM assistant_interactions ORDER BY occurred_at, served_from_cache"
                )
            )
        ).all()
    assert [r.served_from_cache for r in rows] == [False, True]
    assert rows[1].prompt_tokens == 0 and all(r.linked for r in rows)
