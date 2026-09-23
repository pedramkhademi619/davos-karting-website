from __future__ import annotations

from davos.modules.assistant.domain.enums.small_talk_kind import SmallTalkKind
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


# The normalizer turns a half-space into a space, so «می‌تونی» is the two words «می تونی» here.
_GREETING_WORDS = _words("سلام درود بخیر علیکم hi hello hey salam های")
_HOW_ARE_YOU_WORDS = _words("خوبی خوبید خوبین چطوری چطورید چطورین چطوره حال حالت حالتون احوال احوالت احوالتون خبر خبرا")
_THANKS_WORDS = _words("مرسی ممنون ممنونم سپاس سپاسگزارم تشکر متشکرم مچکرم thanks thank thx")
_ACKNOWLEDGEMENT_WORDS = _words(
    "باشه باشد اوکی ok okay حله چشم متوجه شدم شد فهمیدم اها آها آهان اهان خب عالیه خوبم عالیم"
)
_GOODBYE_WORDS = _words("خداحافظ خدانگهدار بدرود فعلا بای bye goodbye")
# Words that may accompany the above but say nothing by themselves.
_FILLER_WORDS = _words(
    "صبح ظهر عصر شب وقت روز شما تو عزیز دوست خسته نباشید نباشین خیلی بسیار عالی بود بودید چه "
    "کردید کردین لطف لطفتون از بابت راهنمایی راهنماییتون راهنماییتان کمک کمکتون کمکتان زحمت زحماتتون پاسخ جواب "
    "دستتون درد نکنه دمت گرم و السلام علیک ورحمه الله you very much so a lot"
)
_CHAT_VOCABULARY = (
    _GREETING_WORDS | _HOW_ARE_YOU_WORDS | _THANKS_WORDS | _ACKNOWLEDGEMENT_WORDS | _GOODBYE_WORDS | _FILLER_WORDS
)

# «Who are you / what can you do?» is recognised only when it uses this small vocabulary and one of the anchors.
_IDENTITY_ANCHORS = _words("کی کیستی کیستید کیه اسمت اسمتون ربات انسان آدم هوش مصنوعی چیکار کاری بلدی بلدید")
_IDENTITY_VOCABULARY = (
    _IDENTITY_ANCHORS
    | _GREETING_WORDS
    | _words(
        "تو شما هستی هستید هستین چیه چیست چی چه اسم می میتونی تونی تونید میتونید میکنی کنی کنید برام برایم انجام "
        "بدی بدید بکنی بکنید اینجا رو را و ای یا"
    )
)
_MAX_WORDS = 6


class SmallTalkDetector:
    """Recognises a message that is only chit-chat (greeting, thanks, «how are you», goodbye, «who are you»).

    Deliberately strict: every word must come from the small fixed vocabularies above, so a real question that merely
    starts with a greeting ("سلام، ساعت کاری چیه؟") is not small talk and goes through the normal grounded flow.
    """

    def __init__(self, normalizer: PersianTextNormalizer | None = None) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()

    def detect(self, text: str) -> SmallTalkKind | None:
        words = self._normalizer.normalize(text).split()
        if not words or len(words) > _MAX_WORDS:
            return None
        if all(word in _IDENTITY_VOCABULARY for word in words) and any(word in _IDENTITY_ANCHORS for word in words):
            return SmallTalkKind.IDENTITY
        if any(word not in _CHAT_VOCABULARY for word in words):
            return None
        present = frozenset(words)
        if present & _GOODBYE_WORDS:
            return SmallTalkKind.GOODBYE
        greets = bool(present & _GREETING_WORDS)
        asks_how = bool(present & _HOW_ARE_YOU_WORDS)
        if greets and asks_how:
            return SmallTalkKind.GREETING_AND_HOW_ARE_YOU
        if asks_how:
            return SmallTalkKind.HOW_ARE_YOU
        if greets:
            return SmallTalkKind.GREETING
        if present & _THANKS_WORDS:
            return SmallTalkKind.THANKS
        if present & _ACKNOWLEDGEMENT_WORDS:
            return SmallTalkKind.ACKNOWLEDGEMENT
        return None
