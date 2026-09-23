from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.background.asyncio_background_runner import AsyncioBackgroundRunner
from davos.modules.assistant.adapters.context.in_memory_conversation_context import InMemoryConversationContext
from davos.modules.assistant.adapters.embedding.sentence_transformer_embedding import SentenceTransformerEmbedding
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.modules.assistant.application.use_cases.purge_semantic_cache_use_case import PurgeSemanticCacheUseCase
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding
from davos.platform.settings.app_settings import AppSettings
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_semantic_cache import InMemorySemanticCache
from tests.fakes.static_knowledge_digest import StaticKnowledgeDigest
from tests.fakes.static_persona import StaticPersona

# ---- background runner ---------------------------------------------------------------------------------------


async def test_background_work_runs_after_the_caller_has_moved_on() -> None:
    runner = AsyncioBackgroundRunner()
    done = asyncio.Event()

    async def work() -> None:
        done.set()

    runner.run(work(), name="test")
    assert not done.is_set(), "run() returns at once"
    await runner.drain()
    assert done.is_set()


async def test_a_failing_background_job_is_logged_and_never_raised(caplog: pytest.LogCaptureFixture) -> None:
    runner = AsyncioBackgroundRunner()

    async def broken() -> None:
        raise RuntimeError("secret detail that must not be logged")

    with caplog.at_level(logging.WARNING):
        runner.run(broken(), name="cache-store")
        await runner.drain()
    assert "cache-store failed: RuntimeError" in caplog.text
    assert "secret detail" not in caplog.text


async def test_finished_jobs_are_forgotten() -> None:
    runner = AsyncioBackgroundRunner()

    async def quick() -> None:
        return None

    runner.run(quick(), name="a")
    await runner.drain()
    await asyncio.sleep(0)
    assert runner._tasks == set()


# ---- conversation memory -------------------------------------------------------------------------------------


def turn(n: int) -> ConversationTurn:
    return ConversationTurn(question=f"پرسش {n}", answer=f"پاسخ {n}")


async def test_the_memory_keeps_the_latest_turns_oldest_first() -> None:
    memory = InMemoryConversationContext(FixedClock(), max_turns=3, ttl_seconds=60)
    conversation = uuid.uuid4()
    for n in range(1, 6):
        await memory.append(conversation, turn(n))
    assert await memory.recent(conversation) == (turn(3), turn(4), turn(5))


async def test_conversations_are_kept_apart_and_can_be_cleared() -> None:
    memory = InMemoryConversationContext(FixedClock(), max_turns=3, ttl_seconds=60)
    a, b = uuid.uuid4(), uuid.uuid4()
    await memory.append(a, turn(1))
    await memory.append(b, turn(2))
    await memory.clear(a)
    assert await memory.recent(a) == () and await memory.recent(b) == (turn(2),)


async def test_a_conversation_is_forgotten_after_its_lifetime_and_each_turn_renews_it() -> None:
    clock = FixedClock()
    memory = InMemoryConversationContext(clock, max_turns=3, ttl_seconds=60)
    conversation = uuid.uuid4()
    await memory.append(conversation, turn(1))
    clock.advance(seconds=50)
    await memory.append(conversation, turn(2))  # renews the lifetime
    clock.advance(seconds=50)
    assert await memory.recent(conversation) == (turn(1), turn(2))
    clock.advance(seconds=11)
    assert await memory.recent(conversation) == ()


# ---- the local embedding model (its failure behaviour; no torch needed) ------------------------------------------


class FakeModel:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def encode(self, text: str, **_: object) -> list[float]:
        self.texts.append(text)
        return [0.6, 0.8]


def embedding(path: str = "/nonexistent/model", **overrides: object) -> SentenceTransformerEmbedding:
    return SentenceTransformerEmbedding(model_path=path, model_name="test-model", dimension=2, **overrides)  # type: ignore[arg-type]


async def test_a_model_that_cannot_be_loaded_switches_the_cache_off_without_raising() -> None:
    model = embedding()
    await model.warm_up()  # must not raise
    assert model.is_ready is False
    with pytest.raises(EmbeddingUnavailableError):
        await model.embed_query("سلام")
    await model.warm_up()  # and asking again is harmless
    model.close()


async def test_before_the_model_is_ready_a_question_gets_a_prompt_refusal_not_a_wait() -> None:
    model = embedding()
    with pytest.raises(EmbeddingUnavailableError):
        await model.embed_query("سلام")
    model.close()


async def test_a_loaded_model_embeds_with_the_query_prefix_and_remembers_recent_texts() -> None:
    model = embedding(lru_size=2)
    fake = FakeModel()
    model._model = fake
    first = await model.embed_query("الف")
    again = await model.embed_query("الف")
    assert first == again == QueryEmbedding(values=(0.6, 0.8), model="test-model")
    assert fake.texts == ["query: الف"], "the second call came from the LRU; E5 wants the 'query: ' prefix"
    await model.embed_query("ب")
    await model.embed_query("ج")  # evicts "الف"
    await model.embed_query("الف")
    assert fake.texts == ["query: الف", "query: ب", "query: ج", "query: الف"]
    model.close()


def test_a_model_folder_of_the_wrong_size_is_reported_at_load_time() -> None:
    model = embedding()
    assert model.dimension == 2 and model.model_name == "test-model"
    model.close()


# ---- what switches the cache on ----------------------------------------------------------------------------


def settings(**overrides: object) -> AppSettings:
    return AppSettings(_env_file=None, **overrides)  # type: ignore[call-arg, arg-type]


def test_the_cache_is_off_unless_enabled() -> None:
    assert ApplicationContainer._build_embedding(settings()) is None


def test_the_cache_stays_off_and_says_so_when_the_model_folder_is_missing(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        result = ApplicationContainer._build_embedding(
            settings(semantic_cache_enabled=True, embedding_model_path="/no/such/folder")
        )
    assert result is None and "fetch_embedding_model" in caplog.text


def test_the_cache_is_built_when_enabled_and_the_folder_exists(tmp_path: Path) -> None:
    result = ApplicationContainer._build_embedding(
        settings(semantic_cache_enabled=True, embedding_model_path=str(tmp_path), embedding_threads=1)
    )
    assert isinstance(result, SentenceTransformerEmbedding) and result.dimension == 768
    assert result.is_ready is False, "building the object never loads the model"
    result.close()


def test_the_policy_is_built_from_the_settings() -> None:
    policy = ApplicationContainer._semantic_cache_policy(
        settings(
            semantic_cache_similarity_threshold=0.91,
            semantic_cache_excluded_source_types=["policy", "pricing"],
            semantic_cache_extra_discriminators=["اسکوتر"],
            semantic_cache_max_age_days=7,
        )
    )
    assert policy.similarity_threshold == 0.91 and policy.max_age_days == 7
    assert policy.excluded_source_types == {KnowledgeSourceType.POLICY, KnowledgeSourceType.PRICING}
    assert policy.extra_discriminator_words == {"اسکوتر"}


# ---- purge -------------------------------------------------------------------------------------------------


def entry(fingerprint: str, created_at) -> NewCacheEntry:
    return NewCacheEntry(
        entry_id=uuid.uuid4(),
        original_query="پرسش",
        resolved_query="پرسش",
        signature="",
        embedding=QueryEmbedding((1.0,), "m"),
        fingerprint=fingerprint,
        response="پاسخ",
        sources=(),
        language=__import__("davos.modules.assistant.domain.enums.language", fromlist=["Language"]).Language.PERSIAN,
        created_at=created_at,
    )


async def test_the_purge_removes_only_entries_that_are_no_longer_being_served() -> None:
    clock = FixedClock()
    store = InMemorySemanticCache()
    digest = StaticKnowledgeDigest("d")
    fingerprint = AnswerFingerprint(rules_version="r", model="m")
    persona = StaticPersona("p")
    current = fingerprint.compute(knowledge_digest="d", persona="p")
    ten_days_ago, long_ago = clock.now() - timedelta(days=10), clock.now() - timedelta(days=120)

    fresh = entry(current, clock.now())  # current and fresh: stays
    just_made_elsewhere = entry("other", clock.now())  # another fingerprint but made today: stays until it goes stale
    abandoned = entry("other", ten_days_ago)  # another fingerprint and nobody was served it for a week: goes
    still_served = entry("other", ten_days_ago)  # another fingerprint but served yesterday: stays (see below)
    unused = entry(current, long_ago)  # not used for 120 days: goes
    awaiting_review = entry("other", long_ago)  # flagged for a person to look at: stays
    for stored in (fresh, just_made_elsewhere, abandoned, still_served, unused, awaiting_review):
        await store.store(stored)
    store.entries[3].last_used_at = clock.now() - timedelta(days=1)
    await store.flag_for_review(awaiting_review.entry_id, deactivate=True)

    removed = await PurgeSemanticCacheUseCase(
        cache=store, digest=digest, fingerprint=fingerprint, clock=clock, persona=persona
    ).execute()

    assert removed == 2
    kept = {s.entry.entry_id for s in store.entries}
    assert kept == {fresh.entry_id, just_made_elsewhere.entry_id, still_served.entry_id, awaiting_review.entry_id}


async def test_a_process_that_computes_the_wrong_fingerprint_cannot_purge_entries_still_in_use() -> None:
    """The worker runs the purge; if its persona file differs from the API's, its idea of the "current" fingerprint is
    wrong. It must then only be able to remove what nobody has been served for a week."""
    clock = FixedClock()
    store = InMemorySemanticCache()
    real = AnswerFingerprint(rules_version="r", model="m").compute(knowledge_digest="d", persona="the API's persona")
    await store.store(entry(real, clock.now() - timedelta(days=30)))
    store.entries[0].last_used_at = clock.now() - timedelta(hours=2)  # customers were served this two hours ago

    removed = await PurgeSemanticCacheUseCase(
        cache=store,
        digest=StaticKnowledgeDigest("d"),
        fingerprint=AnswerFingerprint(rules_version="r", model="m"),
        clock=clock,
        persona=StaticPersona("the worker's DIFFERENT persona"),
    ).execute()

    assert removed == 0
