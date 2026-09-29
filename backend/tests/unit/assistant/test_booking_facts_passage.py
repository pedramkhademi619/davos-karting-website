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


def test_the_passage_is_marked_as_computed() -> None:
    passage = live.passage(booking_facts())
    assert passage.computed and passage.text.count("\n- ") == 2
