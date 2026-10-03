from datetime import time

import pytest

from davos.modules.assistant.domain.services.party_facts_extractor import PartyFactsExtractor

extract = PartyFactsExtractor().extract


def test_reads_age_height_day_and_hour_written_with_persian_digits() -> None:
    facts = extract("پسرم ۱۲ سالشه قدش ۱۵۰، شنبه ساعت ۱۹ میتونه تک نفره برونه؟")
    assert facts.ages == (12,)
    assert facts.height_cm == 150
    assert (facts.weekday, facts.weekday_name) == (5, "شنبه")
    assert facts.at == time(19, 0)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ساعت ۵", time(17, 0)),  # the track opens at 15:00, so a bare 5 is the afternoon
        ("ساعت ۵ عصر", time(17, 0)),
        ("ساعت ۱۷:۴۵", time(17, 45)),
        ("ساعت ۱۱ شب", time(23, 0)),
        ("ساعت ۱۲ شب", time(0, 0)),
        ("ساعت ۱ بامداد", time(1, 0)),
    ],
)
def test_hours_are_read_as_track_hours(text: str, expected: time) -> None:
    assert extract(text).at == expected


@pytest.mark.parametrize(
    ("text", "weekday"),
    [("شنبه", 5), ("یکشنبه", 6), ("یک شنبه", 6), ("سه‌شنبه", 1), ("پنجشنبه", 3), ("پنج شنبه", 3), ("جمعه", 4)],
)
def test_weekdays(text: str, weekday: int) -> None:
    assert extract(f"برای {text} میشه؟").weekday == weekday


def test_lists_of_ages_and_number_words() -> None:
    assert extract("دو تا بچه ۷ و ۹ ساله دارم").ages == (7, 9)
    assert extract("پسرم دوازده سالشه").ages == (12,)
    assert extract("من ۱۹ سالمه و دوستم هم ۱۹ سالشه").ages == (19, 19)


def test_weights_and_group_size() -> None:
    facts = extract("دو تا خانم ۶۵ و ۶۵ کیلو هستیم")
    assert facts.weights_kg == (65, 65)
    assert extract("۹ نفریم").group_size == 9
    assert extract("نه نفر هستیم").group_size == 9


def test_the_two_seater_is_not_a_group_of_two() -> None:
    facts = extract("میتونیم دو نفره سوار بشیم؟")
    assert facts.mentions_two_seater
    assert facts.group_size is None


def test_licence_yes_and_no() -> None:
    assert extract("گواهینامه دارم").has_licence is True
    assert extract("گواهینامه نداره").has_licence is False
    assert extract("سلام").has_licence is None


def test_nothing_is_invented_from_a_plain_question() -> None:
    assert extract("قیمت‌ها چقدره؟").is_empty
    assert extract("آدرس کجاست؟").is_empty


def test_asking_whether_the_track_is_open_is_recognised() -> None:
    extract = PartyFactsExtractor().extract
    assert extract("سه شنبه ساعت ۱۱ شب بازید؟").asks_if_open
    assert extract("ساعت ۱۰ باز هستین؟").asks_if_open
    assert not extract("پسرم ۱۴ سالشه ساعت ۱۷ بیام؟").asks_if_open
