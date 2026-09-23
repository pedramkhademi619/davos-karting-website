from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.application.use_cases.index_knowledge_entry_command import IndexKnowledgeEntryCommand
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery

pytestmark = pytest.mark.integration
normalizer = PersianTextNormalizer()


def q(text_: str) -> SearchQuery:
    return SearchQuery.from_text(text_, normalizer)


async def publish(
    container: ApplicationContainer,
    ref: str,
    title: str,
    body: str,
    url: str,
    source_type: KnowledgeSourceType = KnowledgeSourceType.FAQ,
    published: bool = True,
) -> None:
    await container.index_knowledge_entry().execute(
        IndexKnowledgeEntryCommand(
            source_type=source_type, source_ref=ref, title=title, body=body, url=url, published=published
        )
    )


async def seed(container: ApplicationContainer) -> None:
    await publish(
        container,
        "cancel",
        "لغو رزرو",
        "برای لغو رزرو باید حداقل ۲۴ ساعت قبل اقدام کنید. (متن نمونه)",
        "/policies/cancellation",
        KnowledgeSourceType.POLICY,
    )
    await publish(
        container, "age", "محدودیت سنی", "حداقل سن برای رانندگی در پیست ۱۲ سال است. (متن نمونه)", "/safety#age"
    )
    await publish(
        container,
        "hours",
        "ساعت کاری",
        "پیست هر روز از ساعت ۱۰ تا ۲۲ باز است. (متن نمونه)",
        "/contact#hours",
        KnowledgeSourceType.CONTACT,
    )


async def test_persian_trigram_support_is_available_in_this_database(container: ApplicationContainer) -> None:
    assert await container.knowledge_search().trigram_support_available()


async def test_finds_the_relevant_entry_and_ranks_it_first(container: ApplicationContainer) -> None:
    await seed(container)
    results = await container.knowledge_search().search(q("چطور رزرو را لغو کنم؟"), limit=3)
    assert results and results[0].url == "/policies/cancellation"
    assert results[0].score >= 0.3
    assert results == sorted(results, key=lambda r: r.score, reverse=True)


@pytest.mark.parametrize(
    "query",
    [
        "لغو رزرو",
        "لغو رزرو؟!",
        "ﻟﻐﻮ رزرو",  # presentation forms
        "ساعت كاري",  # Arabic kaf / yeh typed on an Arabic keyboard
    ],
)
async def test_letter_variants_and_punctuation_do_not_change_results(
    container: ApplicationContainer, query: str
) -> None:
    await seed(container)
    results = await container.knowledge_search().search(q(query), limit=1)
    assert results, f"no result for {query!r}"


async def test_arabic_letter_query_matches_persian_letter_document(container: ApplicationContainer) -> None:
    await seed(container)
    results = await container.knowledge_search().search(q("ساعت كاري پيست"), limit=1)
    assert results and results[0].url == "/contact#hours"


async def test_digit_scripts_are_interchangeable(container: ApplicationContainer) -> None:
    await seed(container)
    for query in ("حداقل سن ۱۲", "حداقل سن ١٢", "حداقل سن 12"):
        results = await container.knowledge_search().search(q(query), limit=1)
        assert results and results[0].url == "/safety#age", query


async def test_half_space_and_space_spellings_match(container: ApplicationContainer) -> None:
    await publish(container, "x", "می‌خواهم رزرو کنم", "راهنمای رزرو نوبت. (متن نمونه)", "/booking-help")
    for query in ("می‌خواهم رزرو کنم", "می خواهم رزرو کنم"):
        assert await container.knowledge_search().search(q(query), limit=1)


async def test_unrelated_questions_return_nothing_relevant(container: ApplicationContainer) -> None:
    await seed(container)
    results = await container.knowledge_search().search(q("قیمت بیت کوین امروز"), limit=3)
    assert all(r.score < 0.3 for r in results)


async def test_unpublished_content_is_removed_from_search(container: ApplicationContainer) -> None:
    await seed(container)
    await publish(container, "age", "محدودیت سنی", "متن", "/safety#age", published=False)
    results = await container.knowledge_search().search(q("محدودیت سنی"), limit=5)
    assert "/safety#age" not in [r.url for r in results]


async def test_a_draft_that_was_never_published_is_never_indexed(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    await publish(container, "draft", "پیش نویس محرمانه", "متن", "/draft", published=False)
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM assistant_knowledge_entries"))).scalar_one() == 0


async def test_reindexing_updates_in_place_and_is_idempotent(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    await publish(container, "age", "محدودیت سنی", "حداقل سن ۱۲ سال", "/safety#age")
    await publish(container, "age", "محدودیت سنی", "حداقل سن ۱۴ سال", "/safety#age")
    async with engine.connect() as conn:
        rows = (await conn.execute(text("SELECT body FROM assistant_knowledge_entries"))).all()
    assert [r[0] for r in rows] == ["حداقل سن ۱۴ سال"]


_INSERT_ENTRY = text(
    "INSERT INTO assistant_knowledge_entries "
    "(id, source_type, source_ref, title, body, url, title_norm, search_text, updated_at) "
    "VALUES (gen_random_uuid(), :source_type, 'x', 't', 'b', :url, 't', 'b', now())"
)


async def test_database_rejects_external_links_even_if_the_application_is_bypassed(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(_INSERT_ENTRY, {"source_type": "faq", "url": "https://evil.example"})


async def test_database_rejects_source_types_that_could_hold_private_data(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(_INSERT_ENTRY, {"source_type": "customer_note", "url": "/a"})


async def test_trigram_indexes_exist_for_search(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT indexdef FROM pg_indexes WHERE tablename = 'assistant_knowledge_entries'")
        )
        definitions = " ".join(r[0] for r in rows)
    assert "gin_trgm_ops" in definitions
