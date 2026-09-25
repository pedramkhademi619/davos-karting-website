from davos.modules.assistant.application.services.booking_facts_passage import BookingFactsPassage
from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts

live = BookingFactsPassage()


def test_prices_are_said_the_persian_way() -> None:
    text = live.prices(BookingFacts())
    assert "تک‌نفره ۷۹۰ هزار تومان" in text
    assert "دونفره یک میلیون تومان" in text
    assert "دونفره یک میلیون و ۲۰۰ هزار تومان" in text
    assert "پنجشنبه، جمعه و تعطیلات رسمی" in text


def test_capacity_follows_the_settings() -> None:
    text = live.capacity(BookingFacts(singles_per_session=8, doubles_per_session=2))
    assert "۸ خودرو تک‌نفره و ۲ خودرو دونفره" in text
    assert "به ۱۲ نفر می‌رسد" in text


def test_booking_rules_follow_the_settings() -> None:
    assert "۲۰ دقیقه" in live.booking(BookingFacts())
    assert "روزهای بدون رزرو: پنجشنبه، جمعه" in live.booking(BookingFacts())
    closed = live.booking(BookingFacts(online_booking_enabled=False, min_days_ahead=0, closed_weekdays=frozenset()))
    assert "فعلاً بسته" in closed and "همان روز هم" in closed and "بدون رزرو" not in closed


def test_the_passage_is_marked_as_computed() -> None:
    passage = live.passage(BookingFacts())
    assert passage.computed and passage.text.count("\n- ") == 2
