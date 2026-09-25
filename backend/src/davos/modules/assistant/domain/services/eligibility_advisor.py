from __future__ import annotations

from datetime import time

from davos.modules.assistant.domain.services.group_session_planner import GroupSessionPlanner
from davos.modules.assistant.domain.value_objects.eligibility_rules import EligibilityRules
from davos.modules.assistant.domain.value_objects.party_facts import PartyFacts

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_WEEKDAY_NAMES = {5: "شنبه", 6: "یکشنبه", 0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه", 3: "پنجشنبه", 4: "جمعه"}
_WEEK_ORDER = (5, 6, 0, 1, 2, 3, 4)  # the Iranian week starts on Saturday


def _fa(value: object) -> str:
    return str(value).translate(_PERSIAN_DIGITS)


def _clock(value: time) -> str:
    return _fa(value.strftime("%H:%M"))


class EligibilityAdvisor:
    """Applies the owner's rules to the facts of one message and states the results as plain sentences.

    The sentences are handed to the language model as a checked source, so numbers are compared by code ("۱۴۰ is not
    more than ۱۴۰", "۶۵ + ۶۵ = ۱۳۰ is not below ۱۳۰", "۱۸:۳۰ is outside ۱۵ to ۱۸") instead of by the model.
    """

    def __init__(self, rules: EligibilityRules | None = None) -> None:
        self._r = rules or EligibilityRules()
        self._planner = GroupSessionPlanner(self._r)

    def advise(self, facts: PartyFacts) -> list[str]:
        lines: list[str] = []
        for age in dict.fromkeys(facts.ages):
            lines.extend(self._age(age, facts))
        lines.extend(self._two_seater(facts))
        lines.extend(self._booking_day(facts))
        lines.extend(self._group(facts))
        return lines

    # ------------------------------------------------------------------ one person
    def _age(self, age: int, facts: PartyFacts) -> list[str]:
        r = self._r
        who = f"فرد {_fa(age)} ساله"
        if age < r.rear_seat_min_age:
            return [
                f"{who}: زیر {_fa(r.rear_seat_min_age)} سال است و به هیچ عنوان سوار هیچ خودرویی نمی‌شود "
                "(نه رانندگی، نه صندلی عقب)."
            ]
        if age < r.min_driving_age:
            return [
                f"{who}: نمی‌تواند رانندگی کند (زیر {_fa(r.min_driving_age)} سال). فقط می‌تواند روی صندلی عقب "
                f"خودرو دونفره بنشیند، پشت یک بزرگسال {_fa(r.front_seat_min_age)} سال به بالا که گواهینامه دارد."
            ]
        if age < r.unclear_age:
            return [
                self._junior(who, facts),
                f"{who}: اگر نتواند رانندگی کند، می‌تواند روی صندلی عقب خودرو دونفره بنشیند.",
            ]
        if age == r.unclear_age:
            return [
                f"{who}: برای رانندگی تک‌نفره شرط روشنی تعیین نشده و باید هنگام رزرو با مجموعه هماهنگ شود. "
                "می‌تواند روی صندلی عقب خودرو دونفره بنشیند."
            ]
        if age < r.front_seat_min_age:
            return [
                f"{who}: تک‌نفره: بله، بدون شرط قد، روز یا ساعت. پشت فرمان خودرو دونفره: نه (زیر "
                f"{_fa(r.front_seat_min_age)} سال). صندلی عقب دونفره: نه (فقط {_fa(r.rear_seat_min_age)} تا "
                f"{_fa(r.rear_seat_max_age)} ساله)."
            ]
        licence = {True: "دارد، پس بله", False: "ندارد، پس نه", None: "لازم است"}[facts.has_licence]
        return [
            f"{who}: تک‌نفره: بله، حتی بدون تجربه رانندگی. پشت فرمان خودرو دونفره: گواهینامه و توانایی رانندگی "
            f"{licence}. صندلی عقب دونفره: نه (فقط {_fa(r.rear_seat_min_age)} تا {_fa(r.rear_seat_max_age)} ساله)."
        ]

    def _junior(self, who: str, facts: PartyFacts) -> str:
        r = self._r
        checks: list[str] = []
        verdict: bool | None = True
        if facts.height_cm is None:
            checks.append(f"قد باید بیشتر از {_fa(r.junior_min_height_cm - 1)} سانتی‌متر باشد (قد گفته نشده)")
            verdict = None
        elif facts.height_cm >= r.junior_min_height_cm:
            checks.append(f"قد {_fa(facts.height_cm)} بیشتر از {_fa(r.junior_min_height_cm - 1)} است: درست")
        else:
            limit = _fa(r.junior_min_height_cm - 1)
            checks.append(f"قد {_fa(facts.height_cm)} بیشتر از {limit} نیست: شرط قد برقرار نیست")
            verdict = False
        if facts.weekday is None:
            checks.append("فقط شنبه تا چهارشنبه (روز گفته نشده)")
            verdict = None if verdict else verdict
        elif facts.weekday in r.junior_weekdays:
            checks.append(f"{facts.weekday_name} جزو شنبه تا چهارشنبه است: درست")
        else:
            checks.append(f"{facts.weekday_name} جزو شنبه تا چهارشنبه نیست: مجاز نیست")
            verdict = False
        window = f"{_clock(r.junior_from)} تا {_clock(r.junior_until)}"
        if facts.at is None:
            checks.append(f"فقط ساعت {window} (ساعت گفته نشده)")
            verdict = None if verdict else verdict
        elif r.junior_from <= facts.at <= r.junior_until:
            checks.append(f"ساعت {_clock(facts.at)} داخل بازه {window} است: درست")
        else:
            checks.append(f"ساعت {_clock(facts.at)} خارج از بازه {window} است: مجاز نیست")
            verdict = False
        result = {
            True: "نتیجه: بله، می‌تواند تک‌نفره براند.",
            False: "نتیجه: نه، نمی‌تواند تک‌نفره براند.",
            None: "نتیجه: به شرط‌های گفته‌نشده بستگی دارد.",
        }[verdict]
        return f"{who}: تک‌نفره فقط با همه این شرط‌ها: " + "؛ ".join(checks) + ". " + result

    # ------------------------------------------------------------------ the two-seater
    def _two_seater(self, facts: PartyFacts) -> list[str]:
        r = self._r
        lines: list[str] = []
        if len(facts.weights_kg) >= 2:
            a, b = facts.weights_kg[0], facts.weights_kg[1]
            total = a + b
            limit = _fa(r.light_pair_max_total_kg)
            verdict = (
                f"زیر {limit} است؛ پس با هم می‌توانند سوار دونفره شوند، به شرطی که نفر جلو "
                f"{_fa(r.front_seat_min_age)} سال یا بیشتر باشد و گواهینامه داشته باشد."
                if total < r.light_pair_max_total_kg
                else f"زیر {limit} نیست؛ پس استثنا شامل نمی‌شود و هر کدام باید تک‌نفره بروند."
            )
            lines.append(f"استثنای دو خانم سبک‌وزن: مجموع وزن {_fa(a)} + {_fa(b)} = {_fa(total)} کیلوگرم، که {verdict}")
        children = [a for a in facts.ages if r.rear_seat_min_age <= a <= r.rear_seat_max_age]
        adults = [a for a in facts.ages if a > r.rear_seat_max_age]
        two_adults = len(adults) >= 2 or facts.adults_only
        if facts.mentions_two_seater and not children and not facts.weights_kg and two_adults:
            lines.append(
                "نتیجه: نه. دو بزرگسال نمی‌توانند با هم سوار خودرو دونفره شوند، چون نفر عقب باید کودک "
                f"{_fa(r.rear_seat_min_age)} تا {_fa(r.rear_seat_max_age)} ساله باشد؛ "
                "تنها استثنا دو خانم سبک‌وزن با مجموع "
                f"وزن زیر {_fa(r.light_pair_max_total_kg)} کیلوگرم است. هر بزرگسال می‌تواند تک‌نفره برود."
            )
        return lines

    # ------------------------------------------------------------------ booking day
    def _booking_day(self, facts: PartyFacts) -> list[str]:
        r = self._r
        lines: list[str] = []
        if facts.mentions_today and facts.mentions_booking and not r.same_day_booking:
            lines.append("نتیجه: نه. رزرو برای همان روز ممکن نیست؛ رزرو هر روز برای روز بعد انجام می‌شود.")
        if facts.mentions_booking and facts.weekday in r.booking_closed_weekdays:
            closed = "، ".join(_WEEKDAY_NAMES[d] for d in _WEEK_ORDER if d in r.booking_closed_weekdays)
            lines.append(f"نتیجه: نه. برای {facts.weekday_name} رزرو نداریم (روزهای بدون رزرو: {closed}).")
        return lines

    # ------------------------------------------------------------------ groups
    def _group(self, facts: PartyFacts) -> list[str]:
        size = facts.group_size
        if size is None or size < 2:
            return []
        r = self._r
        rear = sum(1 for a in facts.ages if r.rear_seat_min_age <= a < r.min_driving_age)
        if facts.height_cm is not None and facts.height_cm < r.junior_min_height_cm:
            rear += sum(1 for a in facts.ages if r.min_driving_age <= a < r.unclear_age)
        rear = min(rear, size - 1)
        drivers = size - rear
        plan = self._planner.layout(drivers=drivers, rear_children=rear)
        parts = []
        for index, (driving, children) in enumerate(plan, start=1):
            text = f"سانس {_fa(index)}: {_fa(driving)} نفر رانندگی"
            if children:
                text += (
                    f" ({_fa(children)} نفرشان بزرگسال گواهینامه‌دار پشت فرمان دونفره) و {_fa(children)} کودک روی"
                    " صندلی عقب"
                )
            parts.append(text)
        who = f"{_fa(size)} نفر" + (f" با {_fa(rear)} کودک که فقط عقب دونفره می‌نشینند" if rear else "")
        verdict = "همه در ۱ سانس جا می‌شوند" if len(plan) == 1 else f"حداقل {_fa(len(plan))} سانس لازم است"
        singles, doubles = r.singles_per_session, r.doubles_per_session
        line = (
            f"گروه {who}: نتیجه: {verdict}. هر سانس {_fa(singles)} خودرو تک‌نفره و {_fa(doubles)} خودرو دونفره دارد؛ "
            f"بزرگسالان فقط با تک‌نفره می‌روند و هر دونفره فقط وقتی دو نفر می‌برد که کودکی عقبش بنشیند (یا دو خانم "
            f"سبک‌وزن)، پس ظرفیت هر سانس {_fa(singles)} نفر است و حداکثر به {_fa(singles + 2 * doubles)} نفر می‌رسد. "
            "چیدمان: " + "؛ ".join(parts) + "."
        )
        if rear > drivers:
            line += (
                " هر کودکِ صندلی عقب یک راننده ۱۸ سال به بالای گواهینامه‌دار لازم دارد؛ چون بزرگسال کمتر از کودکان است،"
                " یک بزرگسال باید در چند سانس رانندگی کند (هر بار جدا حساب می‌شود)."
            )
        if not facts.ages and not facts.adults_only:
            line += (
                " اگر کودک ۴ تا ۱۰ ساله یا دو خانم سبک‌وزن در گروه باشند، ممکن است سانس کمتری لازم شود؛ سن‌ها را بپرس."
            )
        return [line]
