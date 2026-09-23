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
