from __future__ import annotations

import pytest

from davos.modules.assistant.domain.services.follow_up_detector import FollowUpDetector
from davos.modules.assistant.domain.services.query_resolver import QueryResolver
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn

detector = FollowUpDetector()
resolver = QueryResolver()
HISTORY = (ConversationTurn(question="خودرو دونفره چیه؟", answer="یک خودرو با دو صندلی."),)


@pytest.mark.parametrize(
    "text",
    [
        "هزینه‌ش چقدره؟",  # a clitic attached with a half-space
        "قیمتش چنده؟",  # the same, typed without one
        "شرایطشون چیه؟",
        "و پنجشنبه؟",  # starts with "and"
        "پس جمعه چطور؟",
        "پنجشنبه چطوره؟",  # nothing but a detail
        "۱۲ ساله؟",
        "اونم همین‌طوره؟",  # a pointer word
        "what about its price?",
        "and on Friday?",
    ],
)
def test_short_messages_that_lean_on_the_previous_one_are_follow_ups(text: str) -> None:
    assert detector.is_follow_up(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "ساعت کاری چیه؟",
        "دو نفره چیه؟",  # short, but a whole question of its own
        "شماره رزرو چیه؟",
        "چطور رزرو کنم؟",
        "how do I book a session?",
        "می‌خواهم برای آخر هفته یک نوبت بگیرم و بدانم چطور باید اقدام کنم؟",  # long enough to stand alone
        "",
    ],
)
def test_self_contained_questions_are_not_follow_ups(text: str) -> None:
    assert detector.is_follow_up(text) is False


def test_without_history_nothing_is_rewritten_but_the_fragment_is_reported_as_needing_context() -> None:
    resolved = resolver.resolve("هزینه‌ش چقدره؟", ())
    assert resolved.text == "هزینه‌ش چقدره؟" and resolved.original == resolved.text and not resolved.is_follow_up
    assert resolved.needs_context is True, "a fragment with nothing to lean on must not be cached by anyone"


def test_a_self_contained_question_needs_no_context_with_or_without_history() -> None:
    assert not resolver.resolve("ساعت کاری چیه؟", ()).needs_context
    assert not resolver.resolve("ساعت کاری چیه؟", HISTORY).needs_context


def test_a_follow_up_with_history_is_both_joined_and_marked() -> None:
    resolved = resolver.resolve("هزینه‌ش چقدره؟", HISTORY)
    assert resolved.is_follow_up and resolved.needs_context


def test_a_follow_up_is_joined_to_the_previous_subject() -> None:
    resolved = resolver.resolve("هزینه‌ش چقدره؟", HISTORY)
    assert resolved.is_follow_up is True
    assert resolved.original == "هزینه‌ش چقدره؟"
    assert resolved.text.startswith("خودرو دونفره چیه؟") and resolved.text.endswith("هزینه‌ش چقدره؟")


def test_a_fresh_question_after_history_is_left_as_it_is() -> None:
    resolved = resolver.resolve("ساعت کاری چیه؟", HISTORY)
    assert resolved.text == "ساعت کاری چیه؟" and resolved.is_follow_up is False


def test_only_the_tail_of_a_long_previous_question_is_carried_over() -> None:
    long_history = (ConversationTurn(question="الف " * 300, answer="پاسخ"),)
    resolved = resolver.resolve("و پنجشنبه؟", long_history)
    assert len(resolved.text) < 260 and resolved.text.endswith("و پنجشنبه؟")
