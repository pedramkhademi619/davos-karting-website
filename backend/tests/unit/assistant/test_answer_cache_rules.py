"""The answer cache's small rules, one by one: which questions are cacheable, what makes two signatures equal, what the
fingerprint depends on, and how stored candidates are chosen."""

from __future__ import annotations

import uuid

import pytest

from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.services.cache_hit_selector import CacheHitSelector
from davos.modules.assistant.domain.services.cacheable_question_detector import CacheableQuestionDetector
from davos.modules.assistant.domain.services.query_resolver import QueryResolver
from davos.modules.assistant.domain.services.query_signature_builder import QuerySignatureBuilder
from davos.modules.assistant.domain.services.sensitive_text_detector import SensitiveTextDetector
from davos.modules.assistant.domain.value_objects.answer_cache_policy import AnswerCachePolicy
from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from tests.fakes.passages import passage


def allowed(question: str) -> bool:
    return CacheableQuestionDetector().allows(QueryResolver().resolve(question, ()))


@pytest.mark.parametrize(
    "question",
    [
        "قیمت هاتون چطوریه؟",
        "پرداخت با چه درگاهیه؟",
        "باشگاه مشتریان فعاله؟",
        "چطوری آنلاین نوبت بگیرم؟",
        "تا کی بازید؟",
    ],
)
def test_general_questions_may_use_the_cache(question: str) -> None:
    assert allowed(question)


@pytest.mark.parametrize(
    "question",
    [
        "پسرم ۱۲ ساله است، قیمت چنده؟",  # an age
        "قدش ۱۴۵ سانته، قیمت چنده؟",  # a height
        "شنبه قیمت چنده؟",  # a weekday
        "ساعت ۵ قیمت چنده؟",  # an hour
        "دو تا خانم ۶۵ کیلو هستیم، قیمت؟",  # weights
        "۹ نفریم، قیمت چنده؟",  # a group
        "امروز میشه رزرو کرد؟",  # today
        "و برای روز تعطیل؟",  # a fragment that needs an earlier message
        "شماره من 09123456789 است",  # personal data
        "ایمیلم a.b@example.com است، قیمت؟",
    ],
)
def test_questions_whose_answer_depends_on_the_asker_never_use_the_cache(question: str) -> None:
    assert not allowed(question)


def test_a_follow_up_joined_to_an_earlier_question_never_uses_the_cache() -> None:
    from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn

    history = (ConversationTurn(question="قیمت چنده؟", answer="۷۹۰ هزار تومان."),)
    follow_up = QueryResolver().resolve("هزینه‌ش چقدره؟", history)
    assert follow_up.is_follow_up and not CacheableQuestionDetector().allows(follow_up)


def sign(text: str) -> str:
    return QuerySignatureBuilder().build(text)


def test_questions_with_no_deciding_detail_share_the_empty_signature() -> None:
    assert sign("قیمتتون چیه؟") == sign("قیمت هاتون چطوریه؟") == ""


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("رزرو آنلاین چطوریه؟", "رزرو تلفنی چطوریه؟"),
        ("قیمت تک نفره روز عادی؟", "قیمت تک نفره روز تعطیل؟"),
        ("قیمت تک نفره؟", "قیمت دونفره؟"),
        ("بچه ها هم میتونن؟", "بزرگسالها هم میتونن؟"),
        ("میشه رزرو کرد؟", "نمیشه رزرو کرد؟"),
        ("Can I book online?", "Can I book by phone?"),
    ],
)
def test_a_deciding_word_makes_the_signatures_differ(first: str, second: str) -> None:
    assert sign(first) != sign(second)


def test_synonyms_do_not_make_the_signatures_differ() -> None:
    assert sign("چطوری آنلاین رزرو کنم؟") == sign("چجوری اینترنتی رزرو کنم؟")
    assert sign("کودک هم میتونه؟") == sign("بچه هم میتونه؟")


def test_a_phone_number_is_not_the_same_as_booking_by_phone() -> None:
    """ "تلفن" alone is a noun ("the phone number"); only "تلفنی" means by phone."""
    assert sign("شماره تلفن رزرو چنده؟") == sign("با چه شماره ای تماس بگیرم؟") == ""
    assert sign("رزرو تلفنی دارید؟") != ""


def test_numbers_count_whatever_script_they_are_written_in() -> None:
    assert sign("رزرو برای ۳ نفر") == sign("رزرو برای 3 نفر") != sign("رزرو برای ۴ نفر")


def fingerprint(**changes: str) -> str:
    base = {"rules_version": "r1", "answer_models": "gemma|", "embedding_model": "e1"}
    texts = [passage(title="الف", text="متن الف", url="/a"), passage(title="ب", text="متن ب", url="/b")]
    persona = changes.pop("persona", "لحن گرم")
    if "text" in changes:
        texts[1] = passage(title="ب", text=changes.pop("text"), url="/b")
    return AnswerFingerprint(**{**base, **changes}).compute(passages=texts, persona=persona)  # type: ignore[arg-type]


def test_the_fingerprint_is_stable_and_ignores_the_order_of_the_passages() -> None:
    texts = [passage(title="الف", text="متن الف", url="/a"), passage(title="ب", text="متن ب", url="/b")]
    maker = AnswerFingerprint(rules_version="r1", answer_models="m", embedding_model="e1")
    assert maker.compute(passages=texts, persona="p") == maker.compute(passages=texts[::-1], persona="p")
    assert fingerprint() == fingerprint()


@pytest.mark.parametrize(
    "change",
    [
        {"rules_version": "r2"},
        {"answer_models": "other|"},
        {"embedding_model": "e2"},
        {"persona": "لحن رسمی"},
        {"text": "متن تازه"},
    ],
)
def test_the_fingerprint_changes_with_anything_the_answer_was_written_from(change: dict[str, str]) -> None:
    assert fingerprint(**change) != fingerprint()


def candidate(similarity: float, signature: str = "", answer: str = "جواب") -> CacheCandidate:
    return CacheCandidate(uuid.uuid4(), "سوال", signature, answer, (), similarity)


def test_only_candidates_with_the_same_signature_are_considered_most_similar_first() -> None:
    low, high, other = candidate(0.7), candidate(0.9), candidate(0.99, signature="w:تعطیل")
    chosen = CacheHitSelector().matching([low, other, high], signature="")
    assert chosen == [high, low]


def test_no_candidate_with_the_same_signature_means_no_hit() -> None:
    assert CacheHitSelector().matching([candidate(1.0, signature="w:آنلاین")], signature="") == []


def test_the_policy_refuses_thresholds_that_make_no_sense() -> None:
    AnswerCachePolicy(similarity_threshold=0.99, verify_from_similarity=0.5, candidate_limit=8, max_text_chars=400)
    for bad in (
        {"similarity_threshold": 0.4, "verify_from_similarity": 0.4},  # too low to be a "same question" bar
        {"similarity_threshold": 0.9, "verify_from_similarity": 0.95},  # the check floor above the threshold
        {"similarity_threshold": 0.9, "verify_from_similarity": 0.2},  # below any similarity worth asking about
        {"similarity_threshold": 0.9, "verify_from_similarity": 0.5, "candidate_limit": 0},
    ):
        values = {"candidate_limit": 8, "max_text_chars": 400, **bad}
        with pytest.raises(ValueError, match="must be"):
            AnswerCachePolicy(**values)  # type: ignore[arg-type]


def test_the_riding_rules_are_never_cached_by_default() -> None:
    policy = AnswerCachePolicy(
        similarity_threshold=0.99, verify_from_similarity=0.5, candidate_limit=8, max_text_chars=4
    )
    assert KnowledgeSourceType.POLICY in policy.excluded_source_types


@pytest.mark.parametrize("text", ["09123456789", "۰۹۱۲۳۴۵۶۷۸۹", "کارتم 6037 9911 2233 4455", "me@example.com"])
def test_personal_data_is_recognised(text: str) -> None:
    assert SensitiveTextDetector().contains_sensitive(text)


def test_ordinary_numbers_are_not_personal_data() -> None:
    assert not SensitiveTextDetector().contains_sensitive("۹ نفر در ساعت ۱۶:۳۰ با ۷۹۰ هزار تومان")
