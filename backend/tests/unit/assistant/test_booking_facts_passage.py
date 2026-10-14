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
    text = live.booking(booking_facts())
    assert "از ساعت ۱۵:۰۰ هر ۱۰ دقیقه یک‌بار" in text
    assert "هر روز فقط تا ساعت ۱۵:۰۰ باز است" in text and "حضوری به پیست مراجعه کند" in text
    assert "تلفن" not in text and not any(ch.isdigit() and ch in "0123456789" for ch in text)
    open_all_day = live.booking(booking_facts(online_booking_cutoff=None))
    assert "ساعتِ رزرو کردن" not in open_all_day


def test_a_closed_booking_sends_customers_to_the_venue_not_to_a_phone_number() -> None:
    text = live.booking(booking_facts(online_booking_enabled=False))
    assert "حضوری" in text and "تلفن" not in text


def test_the_passage_is_marked_as_computed() -> None:
    passage = live.passage(booking_facts())
    assert passage.computed and passage.text.count("\n- ") == 2
