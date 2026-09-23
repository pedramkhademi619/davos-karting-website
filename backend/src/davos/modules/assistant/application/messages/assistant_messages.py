"""User-facing texts of the assistant (Persian). Kept together so support can review the tone."""

from davos.modules.assistant.domain.enums.quick_topic import QuickTopic
from davos.modules.assistant.domain.enums.small_talk_kind import SmallTalkKind

# Answered without the model, so they name no facts (prices, hours, rules) that could go stale.
SMALL_TALK_REPLIES = {
    SmallTalkKind.GREETING: "سلام! خوش اومدید. هر سؤالی درباره رزرو، ساعت کاری یا شرایط سوار شدن دارید بپرسید.",
    SmallTalkKind.GREETING_AND_HOW_ARE_YOU: (
        "سلام! ممنونم، خوبم. شما چطورید؟ هر سؤالی درباره رزرو، ساعت کاری یا شرایط سوار شدن دارید بپرسید."
    ),
    SmallTalkKind.HOW_ARE_YOU: "ممنونم، خوبم! شما چطورید؟ هر سؤالی درباره کارتینگ داوس دارید بپرسید.",
    SmallTalkKind.THANKS: "خواهش می‌کنم! اگه سؤال دیگه‌ای داشتید، در خدمتم.",
    SmallTalkKind.ACKNOWLEDGEMENT: "باشه! اگه سؤال دیگه‌ای داشتید، در خدمتم.",
    SmallTalkKind.GOODBYE: "خدانگهدار! هر وقت سؤالی داشتید، من اینجام.",
    SmallTalkKind.IDENTITY: (
        "من دستیار هوشمند داوس کارتینگ هستم. درباره رزرو، ساعت کاری، قیمت‌ها و شرایط سوار شدن از روی اطلاعات "
        "تاییدشدهٔ همین سایت جواب می‌دهم."
    ),
}

# The title of the published knowledge entry that answers each quick topic completely. If the owner renames the entry
# (or it is a draft), the topic silently falls back to the normal flow; a test checks these titles against knowledge/.
QUICK_TOPIC_TITLES = {
    QuickTopic.HOURS: "ساعت کاری",
    QuickTopic.BOOKING: "نحوه رزرو نوبت",
    QuickTopic.CAPACITY: "خودروها و ظرفیت هر سانس",
    QuickTopic.PRICES: "قیمت‌ها",
    QuickTopic.CLUB: "باشگاه مشتریان داوس",
}

DEFAULT_PERSONA = (
    "لحن گرم، محترمانه و حرفه‌ای داشته باش و با «شما» صحبت کن.\n"
    "ساده و روشن بنویس و از زبان اداری و پیچیده دوری کن.\n"
    "اگر کاربر درباره رزرو پرسید، روش رزرو را فقط از منابع بگو."
)

CONTEXT_RESET_REPLY = "باشه، بی‌خیالش! سؤال جدیدتون رو بپرسید."

INSUFFICIENT_INFORMATION = (
    "برای این پرسش اطلاعات تاییدشده‌ای در سایت ندارم و نمی‌خواهم حدس بزنم. لطفا سوال خود را از بخش «تماس با ما» بپرسید."
)
REFUSED_UNSAFE_INPUT = (
    "این درخواست قابل پردازش نیست. لطفا پرسش خود را درباره خدمات، قوانین و اطلاعات کارتینگ داوس مطرح کنید."
)
FALLBACK_PROVIDER_UNAVAILABLE = (
    "دستیار در حال حاضر در دسترس نیست. مطالب مرتبط زیر ممکن است کمک کند؛ "
    "در غیر این صورت از بخش «تماس با ما» اقدام کنید."
)
FALLBACK_BUDGET_EXHAUSTED = (
    "ظرفیت پاسخ‌گویی خودکار دستیار برای امروز تکمیل شده است. "
    "مطالب مرتبط زیر را ببینید یا از بخش «تماس با ما» اقدام کنید."
)
