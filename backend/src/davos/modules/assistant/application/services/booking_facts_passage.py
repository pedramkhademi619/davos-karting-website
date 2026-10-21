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
            "یک بزرگسال گواهینامه‌دار، کودک ۴ تا ۱۴ ساله بنشیند (یا دو خانم سبک‌وزن با مجموع وزن زیر ۱۳۰ کیلوگرم)، و "
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

    def shifts(self, facts: BookingFacts) -> str:
        evening = f"شیفت عصر: سانس‌ها از ساعت {_clock(facts.first_session)}"
        if facts.last_session_before is not None:
            after_midnight = facts.last_session_before <= facts.first_session
            evening += f" تا {_clock(facts.last_session_before)}{' بامداد روز بعد' if after_midnight else ''}"
        evening += f"، هر {_fa(facts.interval_minutes)} دقیقه یک سانس."
        if facts.morning_shift is None:
            return "سانس‌ها فقط در یک شیفت است. " + evening
        start, end = facts.morning_shift
        return f"سانس‌ها در دو شیفت است. شیفت صبح: از ساعت {_clock(start)} تا {_clock(end)}. {evening}"

    def juniors(self, facts: BookingFacts) -> str | None:
        if facts.junior_weekdays is None or facts.junior_from is None or facts.junior_until is None:
            return None
        days = _days(facts.junior_weekdays)
        start, until = _clock(facts.junior_from), _clock(facts.junior_until)
        window = f"روزهای {days}، سانس‌هایی که از ساعت {start} تا پیش از {until} شروع می‌شوند"
        if facts.junior_everyone:
            return (
                f"ساعت حضور افراد زیر ۱۵ سال (هم نوجوان راننده و هم کودک روی صندلی عقب دونفره): فقط {window}. "
                "در روزها و ساعت‌های دیگر هیچ فرد زیر ۱۵ سالی سوار نمی‌شود."
            )
        return (
            f"رانندگی نوجوان ۱۱ تا ۱۴ ساله با خودرو تک‌نفره (با قد بیشتر از ۱۴۰ سانتی‌متر) فقط {window}. "
            "کودک یا نوجوانی که پشت یک بزرگسال گواهینامه‌دار روی صندلی عقب دونفره می‌نشیند، "
            "همه‌ی روزها و ساعت‌ها می‌تواند بیاید."
        )

    def wizard(self, facts: BookingFacts) -> str:
        """How the site's booking pages work, step by step (only meaningful while online booking is open)."""
        return (
            "رزرو آنلاین از سایت davoskarting.ir، صفحه «رزرو سانس»، چهار مرحله دارد: "
            "۱) نفرات: می‌گویید چه کسانی می‌آیند (بزرگسال با گواهینامه، ۱۵ سال یا بیشتر، نوجوان ۱۱ تا ۱۴ سال، "
            "کودک ۴ تا ۱۴ سال) و سایت خودش تعداد خودرو تک‌نفره و دونفره را طبق قوانین سن و قد و گواهینامه می‌چیند "
            "(اگر نوجوان داشته باشید، انتخاب می‌کنید خودش براند یا پشت یک بزرگسال بنشیند؛ "
            "کسی هم که تعداد خودرو را می‌داند می‌تواند مستقیم تعداد را بزند). "
            "۲) روز: روی هر روز مبلغ کل گروه نوشته شده است. "
            "۳) ساعت: سانس‌ها در فهرست ساعت‌ها نشان داده می‌شوند و جای خالی هر سانس زنده است؛ "
            "فقط سانس‌هایی که برای کل گروه جا دارند انتخاب می‌شوند. اگر روز یا سانسی به گروه نمی‌خورد "
            "(مثلاً برای رانندگی نوجوان‌ها)، با زدن رویش دلیل و راه‌حل نشان داده می‌شود، "
            "مثل نشستن نوجوان‌ها پشت بزرگسال یا تغییر نفرات. "
            "۴) پرداخت: با شماره موبایل و کد پیامکی وارد می‌شوید و دکمه‌ی «لانچ کنترل» را نگه می‌دارید "
            "تا چراغ‌ها خاموش شوند؛ "
            f"آن‌وقت خودروها {_fa(facts.hold_minutes)} دقیقه برای پرداخت نگه داشته می‌شوند و مبلغ را از درگاه بانک ملت "
            "می‌پردازید. بعد از پرداخت شماره بلیت پیامک می‌شود و در «حساب من» هم هست."
        )

    def booking(self, facts: BookingFacts) -> str:
        """The booking rules in force: open or closed, shifts that started, how far ahead, days without booking."""
        if not facts.online_booking_enabled:
            online = "رزرو آنلاین از سایت فعلاً بسته است؛ برای رزرو حضوری به پیست مراجعه کنید."
        else:
            online = (
                f"رزرو آنلاین از صفحه «رزرو سانس» سایت باز است و بعد از انتخاب سانس، خودروها "
                f"{_fa(facts.hold_minutes)} دقیقه برای پرداخت نگه داشته می‌شوند."
            )
            online += (
                " رزرو آنلاین هر سانس تا قبل از شروع شیفتش باز است؛ شیفت که شروع شد، همان شیفتِ همان روز را فقط "
                "حضوری می‌شود رزرو کرد، ولی شیفت‌های بعدی و روزهای بعد هنوز آنلاین باز هستند."
            )
        ahead = (
            "برای همان روز هم می‌شود رزرو کرد."
            if facts.min_days_ahead == 0
            else "رزرو از روز قبل انجام می‌شود و برای همان روز ممکن نیست."
        )
        closed = _days(facts.closed_weekdays)
        return f"{online} {ahead}" + (f" روزهای بدون رزرو: {closed}." if closed else "")

    def passage(self, facts: BookingFacts) -> RetrievedPassage:
        lines = [self.capacity(facts), self.prices(facts)]
        if facts.online_booking_enabled:
            lines.append(self.wizard(facts))
        lines += [self.booking(facts), self.shifts(facts)]
        juniors = self.juniors(facts)
        if juniors:
            lines.append(juniors)
        text = "\n".join(f"- {line}" for line in lines)
        return RetrievedPassage(
            entry_id=LIVE_ENTRY_ID,
            source_type=KnowledgeSourceType.SERVICE,
            title=LIVE_TITLE,
            text=text,
            url=LIVE_URL,
            score=1.0,
            computed=True,
        )
