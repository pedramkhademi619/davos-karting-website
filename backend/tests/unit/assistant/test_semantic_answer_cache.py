from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.modules.assistant.application.services.semantic_answer_cache import SemanticAnswerCache
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.resolved_query import ResolvedQuery
from davos.modules.assistant.domain.value_objects.semantic_cache_policy import SemanticCachePolicy
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.hashing_embedding import HashingEmbedding
from tests.fakes.immediate_background_runner import ImmediateBackgroundRunner
from tests.fakes.in_memory_semantic_cache import InMemorySemanticCache
from tests.fakes.passages import passage
from tests.fakes.static_knowledge_digest import StaticKnowledgeDigest
from tests.fakes.static_persona import StaticPersona

FAQ = KnowledgeSourceType.FAQ
# Word overlap decides similarity for the hashing embedding, so these tests pick their own threshold.
LOOSE = SemanticCachePolicy(similarity_threshold=0.5)


def resolved(text: str) -> ResolvedQuery:
    return ResolvedQuery(original=text, text=text, is_follow_up=False)


class Harness:
    def __init__(self, *, policy: SemanticCachePolicy | None = None, persona: str = "لحن گرم") -> None:
        self.clock = FixedClock()
        self.embedding = HashingEmbedding()
        self.store = InMemorySemanticCache()
        self.digest = StaticKnowledgeDigest()
        self.background = ImmediateBackgroundRunner()
        self.policy = policy or SemanticCachePolicy()
        self.cache = self.build(persona)

    def build(self, persona: str = "لحن گرم", *, rules: str = "r1", model: str = "m1") -> SemanticAnswerCache:
        return SemanticAnswerCache(
            embedding=self.embedding,
            cache=self.store,
            digest=self.digest,
            fingerprint=AnswerFingerprint(rules_version=rules, model=model),
            policy=self.policy,
            clock=self.clock,
            background=self.background,
            persona=StaticPersona(persona),
        )

    async def remember(
        self, question: str, answer: str = "پاسخ نمونه", *, cache: SemanticAnswerCache | None = None
    ) -> uuid.UUID | None:
        cache = cache or self.cache
        query = resolved(question)
        probe = await cache.probe(query)
        assert probe is not None
        entry_id = cache.schedule_store(probe, query=query, answer=answer, cited=[passage(source_type=FAQ)])
        await self.background.settle()
        return entry_id

    async def ask(self, question: str, *, cache: SemanticAnswerCache | None = None):
        cache = cache or self.cache
        probe = await cache.probe(resolved(question))
        return None if probe is None else await cache.lookup(probe)


async def test_a_question_asked_before_is_answered_from_the_cache_with_its_sources() -> None:
    h = Harness()
    entry_id = await h.remember("ساعت کاری شما چیه؟", "ساعت ۱۵ تا ۲۴")
    hit = await h.ask("ساعت کاری شما چیه؟")
    assert hit is not None
    assert (hit.entry_id, hit.text, hit.similarity) == (entry_id, "ساعت ۱۵ تا ۲۴", pytest.approx(1.0))
    assert [s.url for s in hit.sources] == ["/policies/cancellation"]


async def test_an_unrelated_question_misses() -> None:
    h = Harness()
    await h.remember("ساعت کاری شما چیه؟")
    assert await h.ask("شماره تماس رزرو چیه؟") is None


async def test_a_reworded_question_with_the_same_details_hits() -> None:
    h = Harness(policy=SemanticCachePolicy(similarity_threshold=0.8))
    await h.remember("ساعت کاری پنجشنبه")
    assert await h.ask("ساعت کاری پنجشنبه چیه") is not None  # similarity 0.87, same details


@pytest.mark.parametrize(
    ("stored", "asked"),
    [
        ("ساعت کاری پنجشنبه", "ساعت کاری شنبه"),
        ("قد ۱۴۰ است", "قد ۱۳۵ است"),
        ("قیمت روز عادی", "قیمت روز تعطیل"),
        ("قیمت خودرو تک نفره", "قیمت خودرو دو نفره"),
        ("می‌تونم بیام", "نمی‌تونم بیام"),
    ],
)
async def test_a_question_that_differs_in_a_deciding_detail_misses_however_similar_it_looks(
    stored: str, asked: str
) -> None:
    h = Harness(policy=LOOSE)
    await h.remember(stored)
    probe = await h.cache.probe(resolved(asked))
    assert probe is not None
    candidates = await h.store.find_candidates(
        probe.embedding, fingerprint=probe.fingerprint, not_before=h.clock.now() - timedelta(days=1), limit=5
    )
    assert candidates and candidates[0].similarity >= 0.5, "the two questions do look alike to the embedding"
    assert await h.cache.lookup(probe) is None


async def test_editing_the_knowledge_invalidates_every_cached_answer() -> None:
    h = Harness()
    await h.remember("ساعت کاری شما چیه؟")
    h.digest.value = "digest-2"  # the owner changed a knowledge file
    assert await h.ask("ساعت کاری شما چیه؟") is None


async def test_changing_the_style_notes_the_rules_or_the_model_invalidates_cached_answers() -> None:
    h = Harness()
    await h.remember("ساعت کاری شما چیه؟")
    assert await h.ask("ساعت کاری شما چیه؟") is not None
    for other in (h.build("لحن دیگر"), h.build(rules="r2"), h.build(model="m2")):
        assert await h.ask("ساعت کاری شما چیه؟", cache=other) is None


async def test_an_entry_older_than_the_maximum_age_is_not_served() -> None:
    h = Harness(policy=SemanticCachePolicy(max_age_days=30))
    await h.remember("ساعت کاری شما چیه؟")
    h.clock.advance(days=29)
    assert await h.ask("ساعت کاری شما چیه؟") is not None
    h.clock.advance(days=2)
    assert await h.ask("ساعت کاری شما چیه؟") is None


async def test_a_deactivated_entry_is_not_served() -> None:
    h = Harness()
    await h.remember("ساعت کاری شما چیه؟")
    h.store.entries[0].is_active = False
    assert await h.ask("ساعت کاری شما چیه؟") is None


async def test_answers_that_cite_a_policy_are_never_cached_by_default() -> None:
    h = Harness()
    query = resolved("آیا کودک ۱۰ ساله می‌تواند رانندگی کند؟")
    probe = await h.cache.probe(query)
    assert probe is not None
    stored = h.cache.schedule_store(
        probe, query=query, answer="نه", cited=[passage(source_type=KnowledgeSourceType.POLICY)]
    )
    await h.background.settle()
    assert stored is None and h.store.entries == []


async def test_an_answer_citing_one_policy_among_several_sources_is_not_cached_either() -> None:
    h = Harness()
    query = resolved("سوال")
    probe = await h.cache.probe(query)
    assert probe is not None
    cited = [passage(source_type=FAQ), passage(source_type=KnowledgeSourceType.POLICY)]
    assert h.cache.schedule_store(probe, query=query, answer="پاسخ", cited=cited) is None


async def test_the_excluded_kinds_come_from_the_policy() -> None:
    h = Harness(policy=SemanticCachePolicy(excluded_source_types=frozenset()))
    query = resolved("سوال")
    probe = await h.cache.probe(query)
    assert probe is not None
    assert h.cache.schedule_store(probe, query=query, answer="پاسخ", cited=[passage()]) is not None


@pytest.mark.parametrize(("answer", "cited"), [("", [passage(source_type=FAQ)]), ("پاسخ", [])])
async def test_an_empty_answer_or_one_without_sources_is_not_cached(answer: str, cited: list) -> None:
    h = Harness()
    query = resolved("سوال")
    probe = await h.cache.probe(query)
    assert probe is not None
    assert h.cache.schedule_store(probe, query=query, answer=answer, cited=cited) is None


@pytest.mark.parametrize(
    "text", ["شماره من 09123456789 است، رزرو دارید؟", "ایمیل من a@b.com هست", "کارت ۶۰۳۷۹۹۷۱۲۳۴۵۶۷۸۹"]
)
async def test_a_question_with_personal_data_never_touches_the_cache(text: str) -> None:
    h = Harness()
    assert await h.cache.probe(resolved(text)) is None
    assert h.embedding.calls == []


async def test_a_fragment_that_needs_context_it_does_not_have_never_touches_the_cache() -> None:
    """ "و برای روز تعطیل؟" as a first message: the model can only guess its subject, so the guess is not kept."""
    h = Harness()
    fragment = ResolvedQuery(
        original="و برای روز تعطیل؟", text="و برای روز تعطیل؟", is_follow_up=False, needs_context=True
    )
    assert await h.cache.probe(fragment) is None
    assert h.embedding.calls == []


async def test_a_fragment_joined_to_its_context_is_cached_as_the_stand_alone_question() -> None:
    h = Harness()
    joined = ResolvedQuery(
        original="و برای روز تعطیل؟",
        text="قیمت ماشین چقدره؟ — و برای روز تعطیل؟",
        is_follow_up=True,
        needs_context=True,
    )
    probe = await h.cache.probe(joined)
    assert probe is not None and "قیمت ماشین" in probe.text


async def test_a_follow_up_to_a_question_with_personal_data_never_touches_the_cache() -> None:
    """ "قیمتش؟" is harmless on its own, but joined to the earlier "شماره من 09..." it would be stored in the table."""
    h = Harness()
    follow_up = ResolvedQuery(
        original="قیمتش چنده؟", text="شماره من 09123456789 است، خودرو دونفره — قیمتش چنده؟", is_follow_up=True
    )
    assert await h.cache.probe(follow_up) is None
    assert h.embedding.calls == []


async def test_a_hit_is_counted_and_dated_after_the_answer_has_gone_out() -> None:
    h = Harness()
    await h.remember("ساعت کاری شما چیه؟")
    h.clock.advance(hours=3)
    assert await h.ask("ساعت کاری شما چیه؟") is not None
    assert h.store.entries[0].hit_count == 0, "recorded in the background, not on the customer's time"
    await h.background.settle()
    assert (h.store.entries[0].hit_count, h.store.entries[0].last_used_at) == (1, h.clock.now())


async def test_the_language_of_the_question_is_stored_with_the_entry() -> None:
    h = Harness()
    await h.remember("ساعت کاری شما چیه؟")
    await h.remember("What are your opening hours?")
    await h.remember("ما هي ساعات العمل؟ أريد أن أعرف")
    assert [s.entry.language.value for s in h.store.entries] == ["fa", "en", "ar"]


async def test_the_question_as_typed_and_the_normalised_one_are_both_kept() -> None:
    h = Harness()
    await h.remember("ساعت کاری، چطوره؟!")
    entry = h.store.entries[0].entry
    assert entry.original_query == "ساعت کاری، چطوره؟!"
    assert entry.resolved_query == "ساعت کاری چطوره"


async def test_when_the_model_is_not_loaded_the_cache_steps_aside() -> None:
    h = Harness()
    h.embedding.available = False
    assert await h.cache.probe(resolved("ساعت کاری")) is None


async def test_a_database_error_during_lookup_is_a_miss_not_an_error() -> None:
    h = Harness()
    await h.remember("ساعت کاری شما چیه؟")
    h.store.fail_on_find = True
    assert await h.ask("ساعت کاری شما چیه؟") is None


async def test_a_database_error_while_storing_never_reaches_the_caller() -> None:
    h = Harness()
    h.store.fail_on_store = True
    query = resolved("ساعت کاری شما چیه؟")
    probe = await h.cache.probe(query)
    assert probe is not None
    assert h.cache.schedule_store(probe, query=query, answer="پاسخ", cited=[passage(source_type=FAQ)]) is not None
    await h.background.settle()  # must not raise
    assert h.store.entries == []


async def test_flagging_an_entry_for_review_stops_it_being_served() -> None:
    h = Harness()
    entry_id = await h.remember("ساعت کاری شما چیه؟")
    assert entry_id is not None
    await h.cache.flag_for_review(entry_id)
    assert (h.store.entries[0].is_flagged, h.store.entries[0].is_active) == (True, False)
    assert await h.ask("ساعت کاری شما چیه؟") is None


async def test_flagging_an_entry_that_no_longer_exists_is_harmless() -> None:
    await Harness().cache.flag_for_review(uuid.uuid4())


async def test_a_long_question_is_cut_to_the_configured_length_before_embedding() -> None:
    h = Harness(policy=SemanticCachePolicy(max_embedding_text_chars=50))
    probe = await h.cache.probe(resolved("کلمه " * 100))
    assert probe is not None and len(probe.text) <= 50
