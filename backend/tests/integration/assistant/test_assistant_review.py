from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.persistence.pg_answer_cache import PgAnswerCache
from davos.modules.assistant.adapters.persistence.sqlalchemy_assistant_admin import SqlAlchemyAssistantAdmin
from davos.modules.assistant.adapters.persistence.sqlalchemy_interaction_log import SqlAlchemyInteractionLog
from davos.modules.assistant.domain.entities.assistant_interaction import AssistantInteraction
from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.errors.invalid_knowledge_entry_error import InvalidKnowledgeEntryError
from davos.modules.assistant.domain.value_objects.curated_answer import CURATED_FINGERPRINT
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery
from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError

pytestmark = pytest.mark.integration

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
_ZERO_VECTOR = "[" + ",".join("0" for _ in range(384)) + "]"


def _interaction(
    outcome: AnswerOutcome,
    *,
    days_ago: int = 0,
    question: str | None = None,
    tokens: int = 100,
    from_cache: bool = False,
) -> AssistantInteraction:
    return AssistantInteraction(
        interaction_id=uuid.uuid4(),
        occurred_at=NOW - timedelta(days=days_ago),
        outcome=outcome,
        usage=TokenUsage(prompt_tokens=tokens, completion_tokens=10),
        source_entry_ids=(),
        retention_until=NOW + timedelta(days=30),
        question_text=question,
        answer_text="پاسخ" if question else None,
        served_from_cache=from_cache,
    )


async def _cache_entry(engine: AsyncEngine, *, question: str, hits: int, active: bool = True) -> uuid.UUID:
    entry_id = uuid.uuid4()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO assistant_answer_cache (id, original_query, resolved_query, signature, embedding,"
                " embedding_model, fingerprint, response, sources, hit_count, is_active, created_at, last_used_at)"
                " VALUES (:id, :q, :q, '', CAST(:v AS vector), 'm', 'f', 'پاسخ ذخیره', '[]', :hits, :active, :t, :t)"
            ),
            {"id": entry_id, "q": question, "v": _ZERO_VECTOR, "hits": hits, "active": active, "t": NOW},
        )
    return entry_id


async def test_the_overview_counts_the_period_only(container: ApplicationContainer, engine: AsyncEngine) -> None:
    log = SqlAlchemyInteractionLog(container.session_factory)
    helpful_one = _interaction(AnswerOutcome.ANSWERED, tokens=200)
    for item in (
        helpful_one,
        _interaction(AnswerOutcome.ANSWERED, from_cache=True, tokens=0),
        _interaction(AnswerOutcome.INSUFFICIENT_INFORMATION),
        _interaction(AnswerOutcome.ANSWERED, days_ago=30),  # outside a 7 day window
    ):
        await log.record(item)
    await log.record_feedback(helpful_one.interaction_id, helpful=True)
    await _cache_entry(engine, question="قیمت؟", hits=3)
    await _cache_entry(engine, question="ساعت؟", hits=0, active=False)

    result = await SqlAlchemyAssistantAdmin(container.session_factory).overview(since=NOW - timedelta(days=7), days=7)

    assert result.questions == 3
    assert result.by_outcome == {"answered": 2, "insufficient_information": 1}
    assert result.served_from_cache == 1 and result.helpful_votes == 1 and result.not_helpful_votes == 0
    assert result.prompt_tokens == 300 and result.cached_answers_active == 1 and result.cached_answers_total == 2


async def test_the_review_list_filters_unanswered_questions_and_hides_texts_nobody_agreed_to_store(
    container: ApplicationContainer,
) -> None:
    log = SqlAlchemyInteractionLog(container.session_factory)
    await log.record(_interaction(AnswerOutcome.ANSWERED))
    await log.record(_interaction(AnswerOutcome.INSUFFICIENT_INFORMATION, question="آیا وای‌فای دارید؟"))
    review = container.assistant_review()

    unanswered = await review.interactions(
        outcomes=["insufficient_information"], helpful=None, with_text_only=False, offset=0, limit=10
    )
    assert unanswered.total == 1 and unanswered.items[0].question_text == "آیا وای‌فای دارید؟"
    everything = await review.interactions(outcomes=[], helpful=None, with_text_only=False, offset=0, limit=10)
    assert everything.total == 2 and sum(i.question_text is None for i in everything.items) == 1
    with_text = await review.interactions(outcomes=[], helpful=None, with_text_only=True, offset=0, limit=10)
    assert with_text.total == 1


async def test_a_stored_answer_can_be_retired_brought_back_and_deleted(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    entry_id = await _cache_entry(engine, question="قیمت چنده؟", hits=5)
    review = container.assistant_review()

    await review.set_cached_answer_active(entry_id, active=False)
    assert [r.is_active for r in (await review.cached_answers(active=None, offset=0, limit=10)).items] == [False]
    assert (await review.cached_answers(active=True, offset=0, limit=10)).total == 0
    await review.set_cached_answer_active(entry_id, active=True)
    assert (await review.cached_answers(active=True, offset=0, limit=10)).items[0].hit_count == 5

    await review.delete_cached_answer(entry_id)
    assert (await review.cached_answers(active=None, offset=0, limit=10)).total == 0
    with pytest.raises(NotFoundError):
        await review.delete_cached_answer(entry_id)
    with pytest.raises(NotFoundError):
        await review.set_cached_answer_active(entry_id, active=False)


async def test_the_most_used_stored_answers_come_first(container: ApplicationContainer, engine: AsyncEngine) -> None:
    await _cache_entry(engine, question="کم", hits=1)
    await _cache_entry(engine, question="زیاد", hits=9)
    page = await container.assistant_review().cached_answers(active=None, offset=0, limit=10)
    assert [r.question for r in page.items] == ["زیاد", "کم"]


async def test_knowledge_is_added_edited_and_deleted_in_the_database(container: ApplicationContainer) -> None:
    manage = container.manage_knowledge()
    first = await manage.add(
        source_type=KnowledgeSourceType.SERVICE, title="پارکینگ", body="پارکینگ رایگان داریم.", url="/contact"
    )
    assert first.source_ref.startswith("admin:")

    edited = await manage.update(
        first.entry_id,
        source_type=KnowledgeSourceType.CONTACT,
        title="پارکینگ و دسترسی",
        body="پارکینگ جلوی در است.",
        url="/contact",
    )
    catalog = await manage.catalog()
    assert [(e.title, e.source_type, e.body) for e in catalog.entries] == [
        ("پارکینگ و دسترسی", KnowledgeSourceType.CONTACT, "پارکینگ جلوی در است.")
    ]
    assert edited.entry_id == first.entry_id and catalog.entries[0].source_ref == first.source_ref

    await manage.delete(first.entry_id)
    assert (await manage.catalog()).entries == ()
    with pytest.raises(NotFoundError):
        await manage.delete(first.entry_id)
    with pytest.raises(NotFoundError):
        await manage.update(first.entry_id, source_type=KnowledgeSourceType.FAQ, title="t", body="b", url="/x")


async def test_an_edited_text_is_what_the_keyword_search_finds(container: ApplicationContainer) -> None:
    manage = container.manage_knowledge()
    entry = await manage.add(
        source_type=KnowledgeSourceType.FAQ, title="سوال", body="جواب قدیمی درباره کلاه", url="/faq"
    )
    await manage.update(
        entry.entry_id, source_type=KnowledgeSourceType.FAQ, title="سوال", body="جواب تازه درباره دستکش", url="/faq"
    )
    normalizer = PersianTextNormalizer()
    search = container.knowledge_search()
    assert await search.search(SearchQuery.from_text("کلاه", normalizer), limit=3) == []
    found = await search.search(SearchQuery.from_text("دستکش", normalizer), limit=3)
    assert [p.text for p in found] == ["جواب تازه درباره دستکش"]


async def test_the_catalog_says_whether_the_whole_base_still_fits_in_every_prompt(
    container: ApplicationContainer,
) -> None:
    manage = container.manage_knowledge()
    limit = container._assistant_policy.whole_knowledge_max_entries
    for index in range(limit):
        await manage.add(source_type=KnowledgeSourceType.FAQ, title=f"عنوان {index}", body="متن", url="/faq")
    assert (await manage.catalog()).sent_whole
    await manage.add(source_type=KnowledgeSourceType.FAQ, title="یکی بیشتر", body="متن", url="/faq")
    catalog = await manage.catalog()
    assert not catalog.sent_whole and catalog.max_entries == limit and len(catalog.entries) == limit + 1


@pytest.mark.parametrize(
    "url",
    ["https://evil.example", "//evil.example", "faq"],
)
async def test_a_knowledge_text_may_only_link_inside_the_site(container: ApplicationContainer, url: str) -> None:
    with pytest.raises(InvalidKnowledgeEntryError):
        await container.manage_knowledge().add(source_type=KnowledgeSourceType.FAQ, title="t", body="b", url=url)


async def test_a_stored_answer_written_by_hand_is_found_whatever_the_knowledge_says(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    """The nearest-answer query serves the owner's entries next to the ones made for the current knowledge."""
    entry_id = await _cache_entry(engine, question="کارت ملی لازمه؟", hits=0)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE assistant_answer_cache SET fingerprint = 'curated', embedding_model = 'm' WHERE id = :id"),
            {"id": entry_id},
        )
    cache = PgAnswerCache(container.session_factory)
    candidates = await cache.find_candidates(
        QueryEmbedding(tuple([1.0] + [0.0] * 383)), embedding_model="m", fingerprint="another-fingerprint", limit=5
    )
    assert [c.entry_id for c in candidates] == [entry_id]
    assert (await container.assistant_review().cached_answers(active=None, offset=0, limit=5)).items[0].is_curated


async def test_rewriting_a_stored_answer_replaces_its_text_and_keeps_its_count(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    entry_id = await _cache_entry(engine, question="قبلی", hits=7, active=False)
    cache = PgAnswerCache(container.session_factory)
    rewritten = await cache.rewrite(
        NewCacheEntry(
            entry_id=entry_id,
            original_query="جدید؟",
            resolved_query="جدید",
            signature="",
            embedding=QueryEmbedding(tuple([1.0] + [0.0] * 383)),
            embedding_model="m",
            fingerprint=CURATED_FINGERPRINT,
            response="پاسخ تازه",
            sources=(),
            created_at=NOW,
        )
    )
    assert rewritten
    record = (await container.assistant_review().cached_answers(active=None, offset=0, limit=5)).items[0]
    assert (record.question, record.answer, record.hit_count, record.is_active, record.is_curated) == (
        "جدید؟",
        "پاسخ تازه",
        7,
        True,
        True,
    )
    missing = NewCacheEntry(
        uuid.uuid4(), "q", "q", "", QueryEmbedding(tuple([1.0] + [0.0] * 383)), "m", "f", "a", (), NOW
    )
    assert not await cache.rewrite(missing)
