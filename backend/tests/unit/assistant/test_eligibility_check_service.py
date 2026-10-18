from __future__ import annotations

from davos.modules.assistant.application.services.eligibility_check_service import EligibilityCheckService
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn
from tests.fakes.standard_config import booking_facts


def turn(question: str) -> ConversationTurn:
    return ConversationTurn(question=question, answer="...")


def text_of(question: str, history: tuple[ConversationTurn, ...] = ()) -> str:
    passage = EligibilityCheckService().passage(question, history, booking_facts())
    return passage.text if passage else ""


def test_a_question_with_no_details_of_its_own_is_checked_with_the_people_named_just_before() -> None:
    """ "و قیمتش چقدر میشه؟" after "۹ نفر بزرگسالیم" is the group's price, not a question about nothing."""
    assert "هزینه کل" in text_of("و قیمتش چقدر میشه؟", (turn("۹ نفر بزرگسالیم، چند سانس لازمه؟"),))


def test_without_a_previous_group_there_is_nothing_to_check() -> None:
    assert text_of("و قیمتش چقدر میشه؟", (turn("ساعت کاری شما چیه؟"),)) == ""
    assert text_of("و قیمتش چقدر میشه؟") == ""


def test_a_question_that_names_its_own_people_stands_alone() -> None:
    text = text_of("۳ نفر بزرگسالیم چقدر میشه؟", (turn("۹ نفر بزرگسالیم"),))
    assert "گروه ۳ نفر" in text and "گروه ۹ نفر" not in text
