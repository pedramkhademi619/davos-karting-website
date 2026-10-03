import pytest

from davos.modules.assistant.domain.enums.grounding_kind import GroundingKind
from davos.modules.assistant.domain.services.answer_grounding_guard import AnswerGroundingGuard

guard = AnswerGroundingGuard(max_chars=200)
CANARY = "c4n4ry1234"
MARKERS = ("قوانین غیرقابل تغییر",)


def evaluate(raw: str, passage_count: int = 2):
    return guard.evaluate(raw, passage_count=passage_count, canary=CANARY, leak_markers=MARKERS)


def test_cited_answer_is_grounded_and_markers_are_stripped() -> None:
    result = evaluate("لغو تا ۲۴ ساعت قبل ممکن است [1]. جزئیات در بخش قوانین است [2].")
    assert result.kind is GroundingKind.GROUNDED
    assert result.cited_indices == (1, 2)
    assert "[" not in result.text


def test_answer_without_any_citation_is_ungrounded() -> None:
    assert evaluate("لغو ممکن است.").kind is GroundingKind.UNGROUNDED


def test_citation_to_a_nonexistent_passage_does_not_count() -> None:
    assert evaluate("لغو ممکن است [7].", passage_count=2).kind is GroundingKind.UNGROUNDED


@pytest.mark.parametrize("raw", ["NO_ANSWER", "  no_answer.", "", "   "])
def test_no_answer_marker_and_empty_output(raw: str) -> None:
    assert evaluate(raw).kind is GroundingKind.NO_ANSWER


def test_canary_leak_is_detected() -> None:
    assert evaluate(f"نشانه داخلی من {CANARY} است [1]").kind is GroundingKind.LEAK


def test_rule_text_leak_is_detected() -> None:
    assert evaluate("قوانین غیرقابل تغییر من این است [1]").kind is GroundingKind.LEAK


def test_urls_written_by_the_model_are_removed() -> None:
    result = evaluate("اینجا را ببینید https://evil.example/login و www.evil.example [1].")
    assert result.kind is GroundingKind.GROUNDED
    assert "evil" not in result.text


def test_markdown_links_collapse_to_their_label() -> None:
    result = evaluate("[قوانین](https://evil.example) را بخوانید [1].")
    assert "evil" not in result.text
    assert "قوانین" in result.text


def test_long_answers_are_truncated_at_a_sentence_boundary() -> None:
    long_answer = ("این یک جمله نمونه است. " * 30) + "[1]"
    result = evaluate(long_answer)
    assert len(result.text) <= 200
    assert result.text.endswith(".")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("روی دکمه کلیک کنید [1]. سپس ثبت کنید [1].", "روی دکمه کلیک کنید. سپس ثبت کنید."),
        ("امکان‌پذیر است [1] ، ولی [2] شرط دارد [2]؟", "امکان‌پذیر است، ولی شرط دارد؟"),
        ("شرایط: [1] گواهینامه [1]؛ سن [2]!", "شرایط: گواهینامه؛ سن!"),
    ],
)
def test_removing_citation_markers_does_not_leave_a_space_before_punctuation(raw: str, expected: str) -> None:
    result = AnswerGroundingGuard(max_chars=900).evaluate(raw, passage_count=2, canary="C", leak_markers=())
    assert result.kind is GroundingKind.GROUNDED and result.text == expected


def test_an_answer_broken_by_another_script_is_not_shown() -> None:
    assert evaluate("نه، نمی‌تواند. قدش符合要求 است [1].").kind is GroundingKind.UNGROUNDED


def test_a_copied_answer_label_is_removed() -> None:
    assert evaluate(": آره، می‌تونه [1].").text == "آره، می‌تونه."
    assert evaluate("پاسخ: آره، می‌تونه [1].").text == "آره، می‌تونه."


@pytest.mark.parametrize(
    ("raw", "cited", "shown"),
    [
        ("حداقل ۲ سانس لازمه [10, 11].", (10, 11), "حداقل ۲ سانس لازمه."),
        ("مجموع وزنتون ۱۳۰ کیلوگرمه [10، 11].", (10, 11), "مجموع وزنتون ۱۳۰ کیلوگرمه."),
        ("تا ساعت ۱ باز هستیم [۳].", (3,), "تا ساعت ۱ باز هستیم."),
        ("نفر عقب باید کودک باشد [۲ و ۴] و جلو گواهینامه [2-3]!", (2, 3, 4), "نفر عقب باید کودک باشد و جلو گواهینامه!"),
    ],
)
def test_grouped_and_persian_digit_citations_count_and_are_removed(
    raw: str, cited: tuple[int, ...], shown: str
) -> None:
    """gemma writes "[10, 11]" and "[۳]"; they are sources, and they never reach the customer."""
    result = evaluate(raw, passage_count=12)
    assert result.kind is GroundingKind.GROUNDED
    assert result.cited_indices == cited
    assert result.text == shown


def test_brackets_that_are_not_citations_are_left_alone() -> None:
    result = evaluate("کد رزرو شما [DV-7Q2K] است [1].")
    assert result.cited_indices == (1,)
    assert result.text == "کد رزرو شما [DV-7Q2K] است."


@pytest.mark.parametrize(
    ("raw", "shown"),
    [
        (">نه، متاسفانه نمی‌تونه [1].", "نه، متاسفانه نمی‌تونه."),
        ("> نه، متاسفانه نمی‌تونه [1].", "نه، متاسفانه نمی‌تونه."),
        ("، حداقل ۲ سانس لازم دارید [1].", "حداقل ۲ سانس لازم دارید."),
        ("- آره، می‌تونید [1].", "آره، می‌تونید."),
        ("• آره، می‌تونید [1].", "آره، می‌تونید."),
        ("پاسخ: > آره [1].", "آره."),
    ],
)
def test_marks_a_model_puts_before_its_first_word_are_removed(raw: str, shown: str) -> None:
    """gemma-3-27b-it starts some answers with ">" or a comma; a customer must not see that."""
    assert evaluate(raw).text == shown


def test_a_leading_number_is_not_mistaken_for_a_mark() -> None:
    assert evaluate("۷۹۰ هزار تومان [1].").text == "۷۹۰ هزار تومان."
