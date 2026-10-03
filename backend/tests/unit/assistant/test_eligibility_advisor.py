"""The rule checks must agree with the owner's rules in backend/knowledge, number for number."""

from __future__ import annotations

from pathlib import Path

import pytest

from davos.modules.assistant.domain.services.eligibility_advisor import EligibilityAdvisor
from davos.modules.assistant.domain.services.group_session_planner import GroupSessionPlanner
from davos.modules.assistant.domain.services.party_facts_extractor import PartyFactsExtractor
from davos.modules.assistant.domain.value_objects.eligibility_rules import EligibilityRules
from tests.fakes.standard_config import booking_facts

KNOWLEDGE = Path(__file__).resolve().parents[3] / "knowledge"
_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def advise(text: str) -> str:
    """With the admin panel's initial booking settings, as in production."""
    rules = EligibilityRules().for_booking(booking_facts())
    return "\n".join(EligibilityAdvisor(rules).advise(PartyFactsExtractor().extract(text)))


def test_junior_with_every_condition_met_may_drive() -> None:
    assert "نتیجه: بله" in advise("پسرم ۱۴ سالشه قدش ۱۴۱، چهارشنبه ساعت ۱۷:۴۵ میتونه برونه؟")


@pytest.mark.parametrize(
    "text",
    [
        "دخترم ۱۳ سالشه و قدش دقیقا ۱۴۰ سانته، یکشنبه ساعت ۱۶",  # 140 is not MORE than 140
        "پسرم ۱۲ سالشه قدش ۱۵۰، شنبه ساعت ۱۹",  # after 18:00
        "پسرم ۱۲ سالشه قدش ۱۵۰، پنجشنبه ساعت ۱۶",  # not Saturday to Wednesday
    ],
)
def test_junior_failing_one_condition_may_not_drive(text: str) -> None:
    result = advise(text)
    assert "نتیجه: نه" in result
    assert "صندلی عقب" in result  # and is offered the rear seat instead


def test_junior_without_all_details_depends_on_them() -> None:
    assert "بستگی دارد" in advise("پسرم ۱۲ سالشه میتونه برونه؟")


def test_children_under_eleven_and_under_four() -> None:
    assert "نمی‌تواند رانندگی کند" in advise("پسرم ۱۰ سالشه قدش ۱۶۰")
    assert "به هیچ عنوان سوار هیچ خودرویی نمی‌شود" in advise("بچه ۳ ساله")


def test_two_light_women_are_compared_strictly_below_the_limit() -> None:
    assert "= ۱۳۰ کیلوگرم، که زیر ۱۳۰ نیست" in advise("دو تا خانم ۶۵ و ۶۵ کیلو دونفره")
    assert "= ۱۲۹ کیلوگرم، که زیر ۱۳۰ است" in advise("دو تا خانم ۶۴ و ۶۵ کیلو دونفره")


def test_two_adults_cannot_share_the_two_seater() -> None:
    result = advise("من ۱۹ سالمه گواهینامه دارم، با دوستم که اونم ۱۹ سالشه میتونیم دونفره بریم؟")
    assert "دو بزرگسال نمی‌توانند با هم سوار خودرو دونفره شوند" in result


def test_the_front_seat_needs_a_licence() -> None:
    assert "ندارد، پس نه" in advise("مامانم ۵۰ سالشه گواهینامه نداره، میتونه دونفره رو برونه؟")


def test_booking_days() -> None:
    assert "پنجشنبه رزرو نداریم" in advise("برای پنجشنبه میشه رزرو کرد؟")
    assert "برای همان روز ممکن نیست" in advise("برای امروز رزرو دارید؟")


@pytest.mark.parametrize(
    ("drivers", "rear", "sessions"),
    [(6, 0, 1), (7, 0, 2), (12, 0, 2), (13, 0, 3), (7, 1, 1), (8, 1, 2), (14, 2, 2), (5, 2, 2)],
)
def test_group_sessions(drivers: int, rear: int, sessions: int) -> None:
    planner = GroupSessionPlanner(singles_per_session=6, doubles_per_session=1)
    assert planner.sessions_needed(drivers=drivers, rear_children=rear) == sessions
    plan = planner.layout(drivers=drivers, rear_children=rear)
    assert len(plan) == sessions
    assert sum(d for d, _ in plan) == drivers and sum(c for _, c in plan) == rear
    assert all(d <= 7 and c <= 1 for d, c in plan)


def test_without_the_live_settings_no_kart_count_or_booking_day_is_made_up() -> None:
    unknown = EligibilityAdvisor(EligibilityRules())  # the admin settings could not be read
    lines = " ".join(unknown.advise(PartyFactsExtractor().extract("۹ نفر بزرگسالیم، برای پنجشنبه میشه رزرو کرد؟")))
    assert "سانس" not in lines and "رزرو نداریم" not in lines


def test_a_group_of_eight_with_one_child_fits_one_session() -> None:
    assert "همه در ۱ سانس جا می‌شوند" in advise("۸ نفریم، یکیمون بچه ۱۰ ساله است و بقیه بزرگسال با گواهینامه")


def test_kart_counts_and_booking_days_come_from_the_admin_settings() -> None:

    booking = booking_facts(singles_per_session=8, doubles_per_session=2, closed_weekdays=frozenset({4}))
    rules = EligibilityRules().for_booking(booking)

    def run(text: str) -> str:
        return " ".join(EligibilityAdvisor(rules).advise(PartyFactsExtractor().extract(text)))

    assert "همه در ۱ سانس جا می‌شوند" in run("۸ نفر بزرگسالیم")
    assert "حداقل ۲ سانس" in run("۹ نفر بزرگسالیم")
    assert "۸ خودرو تک‌نفره و ۲ خودرو دونفره" in run("۹ نفر بزرگسالیم")
    assert "رزرو نداریم" not in run("برای پنجشنبه میشه رزرو کرد؟")
    assert "رزرو نداریم" in run("برای جمعه میشه رزرو کرد؟")


@pytest.mark.parametrize(
    ("singles", "doubles", "drivers", "rear", "sessions"),
    [(8, 2, 10, 2, 1), (8, 2, 11, 2, 2), (4, 1, 9, 0, 3), (6, 2, 6, 3, 2), (6, 0, 7, 0, 2)],
)
def test_group_sessions_follow_any_kart_count(
    singles: int, doubles: int, drivers: int, rear: int, sessions: int
) -> None:

    plan = GroupSessionPlanner(singles_per_session=singles, doubles_per_session=doubles).layout(
        drivers=drivers, rear_children=rear
    )
    assert len(plan) == sessions
    assert sum(d for d, _ in plan) == drivers and sum(c for _, c in plan) == rear
    assert all(c <= doubles and d <= singles + c for d, c in plan)


def test_the_rules_match_the_published_knowledge() -> None:
    rules = EligibilityRules()
    single = (KNOWLEDGE / "single-seater.txt").read_text(encoding="utf-8")
    double = (KNOWLEDGE / "two-seater.txt").read_text(encoding="utf-8")
    fa = lambda n: str(n).translate(_FA)  # noqa: E731
    assert f"زیر {fa(rules.min_driving_age)} سال" in single
    assert f"بیشتر از {fa(rules.junior_min_height_cm - 1)} سانتی‌متر" in single
    assert f"از ساعت {fa(rules.junior_from.hour)} تا {fa(rules.junior_until.hour)}" in single
    assert f"دقیقاً {fa(rules.unclear_age)} ساله" in single
    assert f"بین {fa(rules.rear_seat_min_age)} تا {fa(rules.rear_seat_max_age)} سال" in double
    assert f"{fa(rules.front_seat_min_age)} سال یا بیشتر" in double
    assert f"زیر {fa(rules.light_pair_max_total_kg)} کیلوگرم" in double


def test_a_group_plan_states_its_total_price_computed_by_code() -> None:
    """The model once said 4,950,000 for nine adults; nine single-seaters are 9 x 790,000 = 7,110,000."""
    text = advise("۹ نفر بزرگسالیم، چند سانس لازمه و چقدر میشه؟")
    assert "۹ خودرو تک‌نفره" in text
    assert "در روز عادی ۷ میلیون و ۱۱۰ هزار تومان" in text
    assert "در روز تعطیل ۸ میلیون و ۴۶۰ هزار تومان" in text  # 9 x 940,000


def test_the_price_follows_the_day_asked_about() -> None:
    text = advise("۹ نفر بزرگسالیم، یکشنبه چقدر میشه؟")
    assert "در روز عادی (یکشنبه): ۷ میلیون و ۱۱۰ هزار تومان" in text and "تعطیل" not in text.split("هزینه کل")[1]
    assert "در روز تعطیل (جمعه): ۸ میلیون و ۴۶۰ هزار تومان" in advise("۹ نفر بزرگسالیم، جمعه چقدر میشه؟")


def test_a_group_with_a_child_pays_for_the_two_seater_the_child_rides_in() -> None:
    # 8 people with one 10 year old: 7 drive, one of them in front of the child -> 6 single-seaters + 1 two-seater
    text = advise("۸ نفریم، یکیمون بچه ۱۰ ساله است و بقیه بزرگسال با گواهینامه")
    assert "۶ خودرو تک‌نفره و ۱ خودرو دونفره" in text
    assert "۵ میلیون و ۷۴۰ هزار تومان" in text  # 6 x 790,000 + 1,000,000


def test_without_the_live_prices_no_total_is_made_up() -> None:
    text = " ".join(
        EligibilityAdvisor(EligibilityRules(singles_per_session=6, doubles_per_session=1)).advise(
            PartyFactsExtractor().extract("۹ نفر بزرگسالیم")
        )
    )
    assert "سانس" in text and "هزینه کل" not in text


def test_an_adult_with_a_child_may_share_the_two_seater() -> None:
    text = advise("من ۳۵ سالمه گواهینامه دارم، میتونم با پسر ۸ سالم دونفره سوار بشیم؟")
    assert "نتیجه: بله، با هم می‌توانند سوار خودرو دونفره شوند" in text
    assert "به شرط داشتن گواهینامه" not in text.split("نتیجه: بله، با هم")[1].split(":")[0]


def test_an_adult_without_a_licence_may_not_drive_the_two_seater_with_a_child() -> None:
    assert "نتیجه: نه" in advise("من ۳۵ سالمه گواهینامه ندارم، میتونم با پسر ۸ سالم دونفره سوار بشیم؟")


def test_an_adult_with_a_child_and_an_unknown_licence_is_asked_for_it() -> None:
    assert "به شرط داشتن گواهینامه" in advise("من ۳۵ سالمه با پسر ۸ سالم دونفره سوار بشیم؟")


def test_a_fifteen_year_old_gets_an_undecided_verdict_not_a_yes() -> None:
    text = advise("۱۵ سالمه میتونم تک نفره برم؟")
    assert "نتیجه: قطعی نیست" in text and "نتیجه: بله" not in text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("سه شنبه ساعت ۱۱ شب بازید؟", "نتیجه: بله"),
        ("چهارشنبه ساعت ۱۴ بازید؟", "نتیجه: نه"),
        ("سه شنبه ساعت ۱۲:۳۰ شب بازید؟", "نتیجه: نه"),  # after midnight only Thursday, Friday and holidays
        ("پنجشنبه ساعت ۱۲:۳۰ شب بازید؟", "نتیجه: بله"),
        ("ساعت ۱۲:۳۰ شب بازید؟", "فقط در پنجشنبه، جمعه و روزهای تعطیل"),
        ("ساعت ۱۱ صبح باز هستید؟", "نتیجه: نه"),
    ],
)
def test_opening_hours_are_compared_by_code(text: str, expected: str) -> None:
    assert expected in advise(text)


def test_a_question_about_the_hour_without_asking_if_open_adds_no_opening_verdict() -> None:
    assert "بامداد" not in advise("پسرم ۱۴ سالشه قدش ۱۴۱، چهارشنبه ساعت ۱۷ میتونه برونه؟")


def test_the_opening_hours_match_the_published_knowledge() -> None:
    rules = EligibilityRules()
    text = (KNOWLEDGE / "working-hours.txt").read_text(encoding="utf-8")
    fa = lambda n: str(n).translate(_FA)  # noqa: E731
    assert f"ساعت کاری {fa(rules.opens_at.hour)} تا ۲۴" in text
    assert f"{fa(rules.opens_at.hour)} تا {fa(rules.late_closes_at.hour)} بامداد" in text
    assert "پنجشنبه، جمعه" in text and rules.late_closing_weekdays == {3, 4}
