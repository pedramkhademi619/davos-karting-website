from dataclasses import replace
from datetime import time

from davos.modules.assistant.application.services.booking_facts_passage import BookingFactsPassage
from tests.fakes.standard_config import booking_facts

live = BookingFactsPassage()


def test_prices_are_said_the_persian_way() -> None:
    text = live.prices(booking_facts())
    assert "تک‌نفره ۷۹۰ هزار تومان" in text
    assert "دونفره یک میلیون تومان" in text
    assert "دونفره یک میلیون و ۲۰۰ هزار تومان" in text
    assert "پنجشنبه، جمعه و تعطیلات رسمی" in text


def test_capacity_follows_the_settings() -> None:
    text = live.capacity(booking_facts(singles_per_session=8, doubles_per_session=2))
    assert "۸ خودرو تک‌نفره و ۲ خودرو دونفره" in text
    assert "به ۱۲ نفر می‌رسد" in text


def test_booking_rules_follow_the_settings() -> None:
    assert "۲۰ دقیقه" in live.booking(booking_facts())
    assert "روزهای بدون رزرو: پنجشنبه، جمعه" in live.booking(booking_facts())
    closed = live.booking(booking_facts(online_booking_enabled=False, min_days_ahead=0, closed_weekdays=frozenset()))
    assert "فعلاً بسته" in closed and "همان روز هم" in closed and "بدون رزرو" not in closed


def test_the_grid_and_the_daily_cutoff_are_stated_and_the_phone_is_not() -> None:
    assert "از ساعت ۱۵:۰۰" in live.shifts(booking_facts()) and "هر ۱۰ دقیقه یک سانس" in live.shifts(booking_facts())
    text = live.booking(booking_facts())
    assert "هر روز فقط تا ساعت ۱۵:۰۰ باز است" in text and "حضوری به پیست مراجعه کند" in text
    assert "تلفن" not in text and not any(ch.isdigit() and ch in "0123456789" for ch in text)
    open_all_day = live.booking(booking_facts(online_booking_cutoff=None))
    assert "ساعتِ رزرو کردن" not in open_all_day


def test_a_closed_booking_sends_customers_to_the_venue_not_to_a_phone_number() -> None:
    text = live.booking(booking_facts(online_booking_enabled=False))
    assert "حضوری" in text and "تلفن" not in text


def test_the_passage_is_marked_as_computed() -> None:
    passage = live.passage(booking_facts())
    # capacity, prices, the wizard, the booking rules, shifts, under-15s
    assert passage.computed and passage.text.count("\n- ") == 5


def test_the_booking_wizard_is_explained_step_by_step() -> None:
    text = live.wizard(booking_facts())
    for step in ("۱) نفرات", "۲) روز", "۳) ساعت", "۴) پرداخت"):
        assert step in text
    assert "لانچ کنترل" in text and "پشت بزرگسال" in text and "davoskarting.ir" in text


def test_one_shift_or_two() -> None:
    evening = live.shifts(booking_facts(morning_shift=None))
    assert "فقط در یک شیفت" in evening and "تا ۰۱:۰۰ بامداد روز بعد" in evening
    assert "شیفت صبح: از ساعت ۱۰:۰۰ تا ۱۴:۰۰" in live.shifts(booking_facts())  # the owner's default
    both = live.shifts(booking_facts(morning_shift=(time(9, 0), time(13, 0))))
    assert "دو شیفت" in both and "شیفت صبح: از ساعت ۰۹:۰۰ تا ۱۳:۰۰" in both


def test_the_under_fifteen_hours_follow_the_settings() -> None:
    default = live.juniors(booking_facts())
    assert default is not None and "شنبه، یکشنبه، دوشنبه، سه‌شنبه، چهارشنبه" in default and "۱۵:۰۰" in default
    assert live.juniors(booking_facts(junior_weekdays=None)) is None
    drivers = booking_facts(junior_weekdays=frozenset({5, 6}), junior_from=time(10, 0), junior_until=time(12, 0))
    text = live.juniors(drivers)
    assert text is not None and "شنبه، یکشنبه" in text and "۱۰:۰۰" in text and "۱۲:۰۰" in text
    assert "همه‌ی روزها و ساعت‌ها می‌تواند بیاید" in text
    everyone = live.juniors(replace(drivers, junior_everyone=True))
    assert everyone is not None and "هیچ فرد زیر ۱۵ سالی" in everyone
    assert live.passage(booking_facts(junior_weekdays=None)).text.count("\n- ") == 4
    assert "لانچ کنترل" not in live.passage(booking_facts(online_booking_enabled=False)).text
