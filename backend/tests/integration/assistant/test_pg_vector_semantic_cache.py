"""The cache adapter against real PostgreSQL with the pgvector extension and its HNSW index."""

from __future__ import annotations

import math
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.persistence.pg_vector_semantic_cache import _FIND, PgVectorSemanticCache
from davos.modules.assistant.adapters.persistence.semantic_cache_entry_model import EMBEDDING_DIMENSIONS
from davos.modules.assistant.domain.enums.language import Language
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding
from tests.fakes.fixed_clock import FixedClock

pytestmark = pytest.mark.integration

MODEL = "test-model"
DEFAULT_SOURCES = (AnswerSource("ساعت کاری", "/contact"),)


def unit(weights: dict[int, float], *, model: str = MODEL, dimension: int = EMBEDDING_DIMENSIONS) -> QueryEmbedding:
    values = [0.0] * dimension
    for index, weight in weights.items():
        values[index] = weight
    norm = math.sqrt(sum(v * v for v in values))
    return QueryEmbedding(values=tuple(v / norm for v in values), model=model)


@pytest.fixture
def cache(container: ApplicationContainer) -> PgVectorSemanticCache:
    return PgVectorSemanticCache(container.session_factory)


def entry(
    clock: FixedClock,
    *,
    embedding: QueryEmbedding | None = None,
    fingerprint: str = "f" * 64,
    response: str = "پاسخ نمونه",
    created_at=None,
    sources: tuple[AnswerSource, ...] = DEFAULT_SOURCES,
) -> NewCacheEntry:
    return NewCacheEntry(
        entry_id=uuid.uuid4(),
        original_query="ساعت کاری شما چیه؟",
        resolved_query="ساعت کاری شما چیه",
        signature="",
        embedding=embedding or unit({0: 1.0}),
        fingerprint=fingerprint,
        response=response,
        sources=sources,
        language=Language.PERSIAN,
        created_at=created_at or clock.now(),
    )


async def find(cache: PgVectorSemanticCache, clock: FixedClock, embedding: QueryEmbedding, **kwargs):
    kwargs.setdefault("fingerprint", "f" * 64)
    kwargs.setdefault("not_before", clock.now() - timedelta(days=30))
    kwargs.setdefault("limit", 8)
    return await cache.find_candidates(embedding, **kwargs)


async def row(engine: AsyncEngine, entry_id: uuid.UUID):
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM assistant_semantic_cache WHERE id = :id"), {"id": entry_id})
        return result.mappings().one_or_none()


async def test_the_pgvector_extension_is_installed_at_the_version_the_adapter_needs(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        version = (
            await conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
        ).scalar_one()
    assert tuple(int(part) for part in version.split(".")[:2]) >= (0, 8), "iterative index scans need pgvector 0.8"


async def test_the_iterative_scan_setting_the_adapter_uses_is_understood_by_this_build(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SET LOCAL hnsw.iterative_scan = 'strict_order'"))
        await conn.execute(text("SELECT '[1,2,3]'::vector"))  # loads the library, which adopts the setting
        assert (await conn.execute(text("SHOW hnsw.iterative_scan"))).scalar_one() == "strict_order"


async def test_stored_entries_come_back_nearest_first_with_their_cosine_similarity(
    cache: PgVectorSemanticCache, clock: FixedClock
) -> None:
    same = entry(clock, embedding=unit({0: 1.0}))
    near = entry(clock, embedding=unit({0: 1.0, 1: 1.0}))
    far = entry(clock, embedding=unit({5: 1.0}))
    for stored in (far, near, same):
        await cache.store(stored)

    found = await find(cache, clock, unit({0: 1.0}))

    assert [c.entry_id for c in found] == [same.entry_id, near.entry_id, far.entry_id]
    assert found[0].similarity == pytest.approx(1.0, abs=1e-6)
    assert found[1].similarity == pytest.approx(1 / math.sqrt(2), abs=1e-6)
    assert found[2].similarity == pytest.approx(0.0, abs=1e-6)


async def test_persian_answers_and_their_sources_survive_the_round_trip(
    cache: PgVectorSemanticCache, clock: FixedClock
) -> None:
    stored = entry(
        clock,
        response="ساعت کاری: شنبه تا چهارشنبه ۱۵ تا ۲۴؛ «پنجشنبه» و جمعه ۱۵ تا ۱ بامداد.",
        sources=(AnswerSource("ساعت کاری", "/contact"), AnswerSource("رزرو نوبت", "/faq")),
    )
    await cache.store(stored)
    (found,) = await find(cache, clock, unit({0: 1.0}))
    assert found.response == stored.response
    assert found.sources == stored.sources
    assert found.signature == "" and found.resolved_query == "ساعت کاری شما چیه"


async def test_entries_of_another_fingerprint_model_or_age_are_never_candidates(
    cache: PgVectorSemanticCache, clock: FixedClock
) -> None:
    await cache.store(entry(clock, fingerprint="a" * 64))
    await cache.store(entry(clock, embedding=unit({0: 1.0}, model="another-model")))
    await cache.store(entry(clock, created_at=clock.now() - timedelta(days=31)))
    fresh = entry(clock)
    await cache.store(fresh)

    found = await find(cache, clock, unit({0: 1.0}))

    assert [c.entry_id for c in found] == [fresh.entry_id]


async def test_the_limit_is_honoured(cache: PgVectorSemanticCache, clock: FixedClock) -> None:
    for weight in range(1, 6):
        await cache.store(entry(clock, embedding=unit({0: 1.0, 1: float(weight)})))
    assert len(await find(cache, clock, unit({0: 1.0}), limit=3)) == 3


async def test_a_vector_of_the_wrong_size_is_rejected_by_the_database(
    cache: PgVectorSemanticCache, clock: FixedClock
) -> None:
    with pytest.raises(DBAPIError):
        await cache.store(entry(clock, embedding=unit({0: 1.0}, dimension=3)))


async def test_a_hit_is_counted_and_dated(cache: PgVectorSemanticCache, clock: FixedClock, engine: AsyncEngine) -> None:
    stored = entry(clock)
    await cache.store(stored)
    clock.advance(hours=2)
    await cache.record_hit(stored.entry_id, clock.now())
    await cache.record_hit(stored.entry_id, clock.now())
    data = await row(engine, stored.entry_id)
    assert data is not None and data["hit_count"] == 2 and data["last_used_at"] == clock.now()
    assert data["is_active"] is True and data["is_flagged_for_review"] is False


async def test_flagging_can_also_take_the_entry_out_of_service(
    cache: PgVectorSemanticCache, clock: FixedClock, engine: AsyncEngine
) -> None:
    kept, retired = entry(clock), entry(clock, embedding=unit({1: 1.0}))
    await cache.store(kept)
    await cache.store(retired)

    assert await cache.flag_for_review(kept.entry_id, deactivate=False) is True
    assert await cache.flag_for_review(retired.entry_id, deactivate=True) is True
    assert await cache.flag_for_review(uuid.uuid4(), deactivate=True) is False

    kept_row, retired_row = await row(engine, kept.entry_id), await row(engine, retired.entry_id)
    assert (kept_row["is_flagged_for_review"], kept_row["is_active"]) == (True, True)  # type: ignore[index]
    assert (retired_row["is_flagged_for_review"], retired_row["is_active"]) == (True, False)  # type: ignore[index]
    assert [c.entry_id for c in await find(cache, clock, unit({0: 1.0}))] == [kept.entry_id]


async def test_purge_removes_only_entries_that_are_no_longer_served_and_keeps_flagged_ones(
    cache: PgVectorSemanticCache, clock: FixedClock, engine: AsyncEngine
) -> None:
    ten_days_ago, long_ago = clock.now() - timedelta(days=10), clock.now() - timedelta(days=120)
    current = entry(clock)
    made_elsewhere_today = entry(clock, fingerprint="b" * 64, embedding=unit({1: 1.0}))
    abandoned = entry(clock, fingerprint="b" * 64, created_at=ten_days_ago, embedding=unit({2: 1.0}))
    still_served = entry(clock, fingerprint="b" * 64, created_at=ten_days_ago, embedding=unit({3: 1.0}))
    unused = entry(clock, created_at=long_ago, embedding=unit({4: 1.0}))
    flagged = entry(clock, fingerprint="b" * 64, created_at=long_ago, embedding=unit({5: 1.0}))
    for stored in (current, made_elsewhere_today, abandoned, still_served, unused, flagged):
        await cache.store(stored)
    await cache.record_hit(still_served.entry_id, clock.now() - timedelta(days=1))
    await cache.flag_for_review(flagged.entry_id, deactivate=True)

    removed = await cache.purge(
        keep_fingerprint="f" * 64,
        stale_before=clock.now() - timedelta(days=7),
        unused_before=clock.now() - timedelta(days=90),
    )

    assert removed == 2
    for kept in (current, made_elsewhere_today, still_served, flagged):
        assert await row(engine, kept.entry_id) is not None
    for gone in (abandoned, unused):
        assert await row(engine, gone.entry_id) is None


async def test_the_nearest_neighbour_query_can_use_the_hnsw_index(engine: AsyncEngine) -> None:
    literal = "[" + ",".join(["0.1"] * EMBEDDING_DIMENSIONS) + "]"
    async with engine.connect() as conn:
        await conn.execute(text("SET enable_seqscan = off"))
        plan = await conn.execute(
            text(
                "EXPLAIN SELECT id FROM assistant_semantic_cache "
                "ORDER BY embedding <=> CAST(CAST(:v AS text) AS vector) LIMIT 5"
            ),
            {"v": literal},
        )
        assert any("ix_assistant_semantic_cache_embedding_hnsw" in line[0] for line in plan)


async def test_the_index_uses_cosine_distance_with_the_documented_build_parameters(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        definition = (
            await conn.execute(
                text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_assistant_semantic_cache_embedding_hnsw'")
            )
        ).scalar_one()
    assert "USING hnsw" in definition and "vector_cosine_ops" in definition
    assert "m='16'" in definition and "ef_construction='64'" in definition


async def test_a_match_hidden_behind_many_stale_entries_is_still_found_through_the_index(
    cache: PgVectorSemanticCache, clock: FixedClock, engine: AsyncEngine
) -> None:
    """The HNSW index hands back its nearest rows first and the filters (active, model, fingerprint) apply
    afterwards, so 100 deactivated entries closer than the real match would leave the query empty without
    iterative scanning."""
    stale = []
    for weight in range(100):
        stale.append(entry(clock, embedding=unit({0: 1.0, 1: 0.001 * (weight + 1)})))
        await cache.store(stale[-1])
        await cache.flag_for_review(stale[-1].entry_id, deactivate=True)
    real = entry(clock, embedding=unit({0: 1.0, 1: 3.0}))  # farther from the query than any stale entry
    await cache.store(real)

    # With a table this small the planner would rather sort in memory; taking that option away leaves the HNSW index as
    # the only way to satisfy the ORDER BY, which is what a large production table does by itself.
    planner = ("enable_seqscan", "enable_sort", "enable_bitmapscan")
    async with engine.connect() as conn:
        for setting in planner:
            await conn.execute(text(f"ALTER DATABASE davos_test SET {setting} = off"))
        await conn.commit()
    try:
        async with engine.connect() as conn:
            plan = await conn.execute(
                text("EXPLAIN " + _FIND.text),
                {
                    "embedding": "[" + ",".join(["0.1"] * EMBEDDING_DIMENSIONS) + "]",
                    "fingerprint": "f" * 64,
                    "model": MODEL,
                    "not_before": clock.now() - timedelta(days=30),
                    "limit": 8,
                },
            )
            assert any("ix_assistant_semantic_cache_embedding_hnsw" in line[0] for line in plan), "not the index path"
        found = await find(cache, clock, unit({0: 1.0}))
    finally:
        async with engine.connect() as conn:
            for setting in planner:
                await conn.execute(text(f"ALTER DATABASE davos_test RESET {setting}"))
            await conn.commit()

    assert [c.entry_id for c in found] == [real.entry_id]
