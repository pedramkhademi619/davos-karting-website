from __future__ import annotations

import uuid
from datetime import time

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.modules.assistant.domain.value_objects.toman_text import TomanText

LIVE_ENTRY_ID = uuid.UUID("5a1e7c0d-0000-4000-8000-00000000b00c")
LIVE_TITLE = "تنظیمات فعلی رزرو، قیمت و ظرفیت"
LIVE_URL = "/booking"

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_WEEKDAY_NAMES = {5: "شنبه", 6: "یکشنبه", 0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه", 3: "پنجشنبه", 4: "جمعه"}
_WEEK_ORDER = (5, 6, 0, 1, 2, 3, 4)  # the Iranian week starts on Saturday


def _fa(value: object) -> str:
    return str(value).translate(_PERSIAN_DIGITS)


def _clock(value: time) -> str:
    return _fa(value.strftime("%H:%M"))


def _days(days: frozenset[int]) -> str:
    return "، ".join(_WEEKDAY_NAMES[d] for d in _WEEK_ORDER if d in days)


class BookingFactsPassage:
    """States the admin panel's booking settings in plain Persian, as a passage the model can cite and as the ready
    answers to "چند تا ماشین دارید؟" and "قیمت‌ها چنده؟". Prices and kart counts change in the admin panel, so they are
    never quoted from a knowledge file."""

    def capacity(self, facts: BookingFacts) -> str:
        singles, doubles = facts.singles_per_session, facts.doubles_per_session
        return (
            f"در هر سانس {_fa(singles)} خودرو تک‌نفره و {_fa(doubles)} خودرو دونفره داریم. بزرگسالان هر کدام با یک "
            f"تک‌نفره می‌روند، پس هر سانس {_fa(singles)} بزرگسال می‌برد؛ خودرو دونفره فقط وقتی دو نفر می‌برد که پشت "
            "یک بزرگسال گواهینامه‌دار، کودک ۴ تا ۱۵ ساله بنشیند (یا دو خانم سبک‌وزن با مجموع وزن زیر ۱۳۰ کیلوگرم)، و "
            f"آن‌وقت ظرفیت سانس به {_fa(singles + 2 * doubles)} نفر می‌رسد."
        )

    def prices(self, facts: BookingFacts) -> str:
        holidays = _days(facts.holiday_weekdays)
        holiday_days = f"{holidays} و تعطیلات رسمی" if holidays else "تعطیلات رسمی"
        return (
            f"روزهای عادی: خودرو تک‌نفره {TomanText.say(facts.normal_single_toman)} و خودرو دونفره "
            f"{TomanText.say(facts.normal_double_toman)}. روزهای تعطیل ({holiday_days}): خودرو تک‌نفره "
            f"{TomanText.say(facts.holiday_single_toman)} و خودرو دونفره {TomanText.say(facts.holiday_double_toman)}. "
            "قیمت هر خودرو برای یک سانس است."
        )

    def booking(self, facts: BookingFacts) -> str:
        if not facts.online_booking_enabled:
            online = "رزرو آنلاین از سایت فعلاً بسته است؛ برای رزرو حضوری به پیست مراجعه کنید."
        else:
            online = (
                f"رزرو آنلاین از صفحه «رزرو سانس» سایت باز است؛ سانس‌ها از ساعت {_clock(facts.first_session)} هر "
                f"{_fa(facts.interval_minutes)} دقیقه یک‌بار شروع می‌شوند و بعد از انتخاب سانس، خودروها "
                f"{_fa(facts.hold_minutes)} دقیقه برای پرداخت نگه داشته می‌شوند."
            )
            if facts.online_booking_cutoff is not None:
                cutoff = _clock(facts.online_booking_cutoff)
                online += (
                    f" رزرو آنلاین هر روز فقط تا ساعت {cutoff} باز است؛ این ساعتِ رزرو کردن است، نه ساعت سانس. "
                    f"هر کس بعد از ساعت {cutoff} بخواهد رزرو کند، برای هر روز و هر سانسی، "
                    "باید حضوری به پیست مراجعه کند."
                )
        ahead = (
            "برای همان روز هم می‌شود رزرو کرد."
            if facts.min_days_ahead == 0
            else "رزرو از روز قبل انجام می‌شود و برای همان روز ممکن نیست."
        )
        closed = _days(facts.closed_weekdays)
        return f"{online} {ahead}" + (f" روزهای بدون رزرو: {closed}." if closed else "")

    def passage(self, facts: BookingFacts) -> RetrievedPassage:
        text = "\n".join(f"- {line}" for line in (self.capacity(facts), self.prices(facts), self.booking(facts)))
        return RetrievedPassage(
            entry_id=LIVE_ENTRY_ID,
            source_type=KnowledgeSourceType.SERVICE,
            title=LIVE_TITLE,
            text=text,
            url=LIVE_URL,
            score=1.0,
            computed=True,
        )
