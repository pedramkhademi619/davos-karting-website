import pytest

from davos.modules.assistant.domain.errors.question_rejected_error import QuestionRejectedError
from davos.modules.assistant.domain.value_objects.question import Question


def test_whitespace_and_control_characters_are_cleaned() -> None:
    assert Question.create("  سلام\x00 \n  دنیا‮ ", max_chars=100).text == "سلام دنیا"


@pytest.mark.parametrize("raw", ["", "  ", "؟"[:0], "a"])
def test_too_short_questions_are_rejected(raw: str) -> None:
    with pytest.raises(QuestionRejectedError):
        Question.create(raw, max_chars=100)


def test_too_long_question_is_rejected_with_a_specific_code() -> None:
    with pytest.raises(QuestionRejectedError) as info:
        Question.create("الف" * 101, max_chars=100)
    assert info.value.code == "question_too_long"
