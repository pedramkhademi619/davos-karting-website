from __future__ import annotations

import pytest

from davos.modules.assistant.domain.services.query_signature_builder import QuerySignatureBuilder

builder = QuerySignatureBuilder()


def test_a_question_without_details_has_an_empty_signature() -> None:
    assert builder.build("شماره رزرو چیه؟") == ""


def test_numbers_are_part_of_the_signature_whatever_digits_they_are_written_in() -> None:
    assert builder.build("دخترم ۱۲ ساله است و قدش ۱۴۰ است") == builder.build("دخترم 12 ساله است و قدش 140 است")
    assert "n:12,140" in builder.build("دخترم ۱۲ ساله است و قدش ۱۴۰ است")


def test_leading_zeros_do_not_make_two_numbers_different() -> None:
    assert builder.build("ساعت 07") == builder.build("ساعت 7")


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("ساعت کاری پنجشنبه چیه؟", "ساعت کاری شنبه چیه؟"),  # another day
        ("قیمت روز عادی چنده؟", "قیمت روز تعطیل چنده؟"),  # another kind of day
        ("قیمت ماشین تک نفره چنده؟", "قیمت ماشین دو نفره چنده؟"),  # another vehicle
        ("دخترم قدش ۱۴۰ است، می‌تواند بیاید؟", "دخترم قدش ۱۳۵ است، می‌تواند بیاید؟"),  # another height
        ("می‌توانم رزرو کنم؟", "نمی‌توانم رزرو کنم؟"),  # the opposite
        ("بچه ۷ ساله می‌تواند بیاید؟", "مادرم ۷ ساله می‌تواند بیاید؟"),  # another person
        ("Can I book on Thursday?", "Can I book on Friday?"),
    ],
)
def test_questions_whose_answers_differ_get_different_signatures(first: str, second: str) -> None:
    assert builder.build(first) != builder.build(second)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("ساعت کاری شما چیه؟", "ساعت کاری چطوره؟"),
        ("How do I book a session?", "how do i book a session"),
        ("شماره رزرو چیه", "شماره رزرو چیه؟!"),
    ],
)
def test_questions_that_differ_only_in_wording_share_a_signature(first: str, second: str) -> None:
    assert builder.build(first) == builder.build(second)


def test_word_order_and_repetition_do_not_matter() -> None:
    assert builder.build("پنجشنبه و جمعه رزرو دارید؟") == builder.build("جمعه و پنجشنبه پنجشنبه رزرو دارید؟")


def test_extra_words_from_settings_join_the_lexicon() -> None:
    plain = QuerySignatureBuilder()
    extended = QuerySignatureBuilder(extra_words=["اسکوتر"])
    assert plain.build("قیمت اسکوتر") == ""
    assert "اسکوتر" in extended.build("قیمت اسکوتر")
    assert extended.build("قیمت اسکوتر") != extended.build("قیمت")
