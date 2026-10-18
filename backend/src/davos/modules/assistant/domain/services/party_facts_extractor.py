from __future__ import annotations

import re
from datetime import time

from davos.modules.assistant.domain.value_objects.party_facts import PartyFacts
from davos.shared_kernel.domain.digit_normalizer import DigitNormalizer

_NUMBER_WORDS = {
    "دو": 2,
    "سه": 3,
    "چهار": 4,
    "پنج": 5,
    "شش": 6,
    "هفت": 7,
    "هشت": 8,
    "نه": 9,
    "ده": 10,
    "یازده": 11,
    "دوازده": 12,
    "سیزده": 13,
    "چهارده": 14,
    "پانزده": 15,
    "شانزده": 16,
    "هفده": 17,
    "هجده": 18,
    "هیجده": 18,
    "نوزده": 19,
    "بیست": 20,
}
_WORD_BEFORE_UNIT = re.compile(
    r"(?<![\w])("
    + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))
    + r")(?=\s*(?:تا\s*)?(?:نفر|ساله|سالش|سالم|کیلو))"
)
_LIST = r"(?:\d{1,3}\s*(?:و|،|,|تا|یا)\s*)*\d{1,3}"
_AGE = re.compile(rf"({_LIST})\s*(?:ساله|سالشه|سالمه|سالمونه|سالشون|سالتون|سالش|سالم|سال)(?![ن\w])")
_AGE_WORD_FIRST = re.compile(r"(?<![\w])سن(?:ش|م|شون)?\s*(\d{1,2})")
_HEIGHT = re.compile(
    r"قد(?:ش|م|شون|تون)?\s*(?:هم\s*)?(?:دقیقا|دقیقاً|حدودا|حدود|تقریبا)?\s*(\d{2,3})|(\d{3})\s*(?:سانت|سانتی|cm)"
)
_WEIGHT = re.compile(rf"({_LIST})\s*(?:کیلو|کیلوگرم|kg)")
_TIME = re.compile(r"ساعت\s*(\d{1,2})(?:\s*[:٫.]\s*(\d{2}))?\s*(صبح|ظهر|عصر|شب|بعد\s*از\s*ظهر|بعدازظهر)?")
_WEEKDAY = re.compile(r"(?<![\w])(یک|دو|سه|چهار|پنج)?\s?شنبه|(?<![\w])جمعه")
_WEEKDAYS = {None: 5, "یک": 6, "دو": 0, "سه": 1, "چهار": 2, "پنج": 3}
_WEEKDAY_NAMES = {5: "شنبه", 6: "یکشنبه", 0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه", 3: "پنجشنبه", 4: "جمعه"}
_GROUP = re.compile(r"(\d{1,2})\s*(?:تا\s*)?نفر(یم|ید|ین|ن|ه)?(?![\w])")
_LETTERS = str.maketrans("يك‌", "یک ", "ـ")  # Arabic letters, zero-width joiner, kashida
_TWO_SEATER = re.compile(r"(?:دو|2)\s*نفره")
# "بازید؟", "باز هستید؟", "باز است؟", "کار می‌کنید؟": asking whether it is open at a given time
_OPEN = re.compile(r"(?<![\w])(?:باز(?:ید|ین)|باز\s+(?:هستید|هستین|است)|کار\s+می\s*کنید)(?![\w])")
_LICENCE_YES = re.compile(r"گواهینامه\s*(?:هم\s*)?(?:دار|داشت)")
_LICENCE_NO = re.compile(r"گواهینامه\s*(?:هم\s*)?ندار|بدون\s*گواهینامه|گواهینامه\s*(?:هم\s*)?نگرفت")


class PartyFactsExtractor:
    """Reads ages, height, day, hour, weights, group size and licence from a Persian (or mixed) message.

    Deliberately literal: it only picks up numbers written next to their unit ("۱۲ ساله", "قد ۱۵۰", "۶۰ کیلو",
    "ساعت ۱۷:۴۵", "۹ نفر"), so it never invents a fact. Whatever it cannot read is simply left out.
    """

    def extract(self, message: str) -> PartyFacts:
        text = self._normalize(message)
        ages = self._ages(text)
        weekday = self._weekday(text)
        return PartyFacts(
            ages=ages,
            height_cm=self._height(text),
            weekday=weekday,
            weekday_name=_WEEKDAY_NAMES.get(weekday, "") if weekday is not None else "",
            at=self._time(text),
            weights_kg=tuple(w for w in self._numbers(_WEIGHT, text) if 25 <= w <= 200),
            group_size=self._group(text),
            has_licence=False if _LICENCE_NO.search(text) else (True if _LICENCE_YES.search(text) else None),
            mentions_two_seater=bool(_TWO_SEATER.search(text)),
            mentions_rear_seat="عقب" in text,
            mentions_women="خانم" in text or re.search(r"(?<![\w])زن(?![\w])", text) is not None,
            mentions_today="امروز" in text,
            mentions_booking="رزرو" in text or "نوبت" in text,
            asks_if_open=bool(_OPEN.search(text)),
            adults_only="بزرگسال" in text and not any(a < 16 for a in ages) and "بچه" not in text,
        )

    @staticmethod
    def _normalize(message: str) -> str:
        text = DigitNormalizer.to_ascii(message)
        text = text.translate(_LETTERS)
        text = re.sub(r"\s+", " ", text)
        return _WORD_BEFORE_UNIT.sub(lambda m: str(_NUMBER_WORDS[m.group(1)]), text)

    @staticmethod
    def _numbers(pattern: re.Pattern[str], text: str) -> list[int]:
        found: list[int] = []
        for match in pattern.finditer(text):
            found.extend(int(n) for n in re.findall(r"\d{1,3}", match.group(1)))
        return found

    def _ages(self, text: str) -> tuple[int, ...]:
        ages = [a for a in self._numbers(_AGE, text) if 1 <= a <= 99]
        ages += [int(m.group(1)) for m in _AGE_WORD_FIRST.finditer(text) if 1 <= int(m.group(1)) <= 99]
        return tuple(ages)

    @staticmethod
    def _height(text: str) -> int | None:
        for match in _HEIGHT.finditer(text):
            value = int(match.group(1) or match.group(2))
            if 80 <= value <= 220:
                return value
        return None

    @staticmethod
    def _time(text: str) -> time | None:
        match = _TIME.search(text)
        if match is None:
            return None
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        part = (match.group(3) or "").replace(" ", "")
        if (part in {"عصر", "شب", "بعدازظهر"} and hour < 12) or (not part and 3 <= hour <= 11):
            hour += 12  # the track opens at 15:00, so "ساعت ۵" means 17:00
        if hour == 24 or (part == "شب" and hour == 12):
            hour = 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return time(hour, minute)

    @staticmethod
    def _weekday(text: str) -> int | None:
        match = _WEEKDAY.search(text)
        if match is None:
            return None
        if match.group(0).endswith("جمعه"):
            return 4
        return _WEEKDAYS[match.group(1)]

    @staticmethod
    def _group(text: str) -> int | None:
        for match in _GROUP.finditer(text):
            size = int(match.group(1))
            if match.group(2) == "ه" and size == 2:
                continue  # "دو نفره" is the two-seater, not a group of two
            if 2 <= size <= 60:
                return size
        return None
