from __future__ import annotations

import pytest

from davos.modules.assistant.domain.enums.small_talk_kind import SmallTalkKind
from davos.modules.assistant.domain.services.small_talk_detector import SmallTalkDetector

detector = SmallTalkDetector()


@pytest.mark.parametrize(
    "text",
    [
        "سلام",
        "سلام!",
        "  سلام  ",
        "درود",
        "صبح بخیر",
        "سلام وقت بخیر",
        "سلام خسته نباشید",
        "سلام علیکم",
        "hello",
        "Hi!",
        "سلام ممنون",
        "سَلام",  # with a diacritic
        "سلام 🙂",
    ],
)
def test_a_bare_greeting_is_recognised(text: str) -> None:
    assert detector.detect(text) is SmallTalkKind.GREETING


@pytest.mark.parametrize(
    "text",
    [
        "ممنون",
        "مرسی",
        "مرسی!!",
        "خیلی ممنون",
        "ممنونم از راهنماییتون",
        "مرسی عالی بود",
        "دمت گرم مرسی",
        "thanks",
        "thank you",
    ],
)
def test_bare_thanks_is_recognised(text: str) -> None:
    assert detector.detect(text) is SmallTalkKind.THANKS


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "😀",
        "ساعت کاری چیه؟",
        "سلام ساعت کاری چیه؟",  # a real question that starts with a greeting must reach the normal flow
        "سلام، می‌خوام رزرو کنم",
        "مرسی ولی قیمت چنده؟",
        "ممنون، پس پنجشنبه رزرو نداریم؟",
        "hello I want to book a session",
        "خیلی",  # filler words alone are not small talk
        "ببخشید",
        "خوبم ولی قیمت چنده",
        "سلام سلام سلام سلام سلام سلام سلام",  # too long to be a plain greeting
    ],
)
def test_anything_else_is_not_small_talk(text: str) -> None:
    assert detector.detect(text) is None


@pytest.mark.parametrize("text", ["سلام خوبی؟", "سلام چطوری", "سلام خوبید؟", "hi خوبی"])
def test_a_greeting_with_how_are_you_is_recognised(text: str) -> None:
    assert detector.detect(text) is SmallTalkKind.GREETING_AND_HOW_ARE_YOU


@pytest.mark.parametrize("text", ["خوبی؟", "چطوری؟", "حالت چطوره", "چه خبر", "تو خوبی؟", "حال شما چطوره"])
def test_how_are_you_alone_is_recognised(text: str) -> None:
    assert detector.detect(text) is SmallTalkKind.HOW_ARE_YOU


@pytest.mark.parametrize("text", ["باشه", "اوکی", "ok", "متوجه شدم", "آها", "خوبم", "عالیه"])
def test_a_plain_acknowledgement_is_recognised(text: str) -> None:
    assert detector.detect(text) is SmallTalkKind.ACKNOWLEDGEMENT


@pytest.mark.parametrize("text", ["خداحافظ", "خدانگهدار", "فعلا", "bye", "مرسی خداحافظ", "بای"])
def test_a_goodbye_is_recognised(text: str) -> None:
    assert detector.detect(text) is SmallTalkKind.GOODBYE


@pytest.mark.parametrize(
    "text",
    ["تو کی هستی؟", "شما کی هستید", "اسمت چیه", "شما ربات هستید؟", "سلام تو کی هستی", "تو چه کاری میتونی انجام بدی"],
)
def test_who_are_you_is_recognised(text: str) -> None:
    assert detector.detect(text) is SmallTalkKind.IDENTITY


@pytest.mark.parametrize(
    "text",
    [
        "کی باز هستید",  # a real question about hours
        "کی هستی و ساعت کاری چیه",
        "باشه ولی پنجشنبه رزرو نداریم؟",
        "خداحافظ ولی قبلش قیمت چنده",
    ],
)
def test_chit_chat_words_inside_a_real_question_do_not_make_it_small_talk(text: str) -> None:
    assert detector.detect(text) is None
