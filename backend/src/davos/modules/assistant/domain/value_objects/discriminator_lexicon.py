"""Words that change the *answer* while barely changing the *embedding*.

Dense embeddings rate "hours on Thursday" and "hours on Saturday" as near-identical questions, and so are
"a 12-year-old of 140 cm" and "of 135 cm", "single-seater" and "two-seater", "can" and "cannot". Their answers
differ, so a cached answer may
only be reused when the question carries exactly the same words from this list (see ``QuerySignatureBuilder``).

All entries are in the form produced by ``PersianTextNormalizer`` (Persian letters, ASCII digits, no punctuation).
"""


def word_set(text: str) -> frozenset[str]:
    """A set of words written in one string (easier to read and to review than a long list of quoted strings)."""
    return frozenset(text.split())


NUMBER_WORDS = word_set(
    "سه چهار پنج شش هفت هشت ده یازده دوازده سیزده چهارده پانزده شانزده هفده هجده نوزده بیست سی چهل پنجاه"
)
WEEKDAYS = word_set(
    "شنبه یکشنبه دوشنبه سهشنبه چهارشنبه پنجشنبه جمعه آدینه "
    "saturday sunday monday tuesday wednesday thursday friday "
    "السبت الاحد الاثنین الثلاثاء الاربعاء الخمیس الجمعه"
)
DAY_KINDS = word_set("عادی تعطیل تعطیلی تعطیلات امروز فردا دیروز holiday holidays weekday weekend today tomorrow")
VEHICLES = word_set("تک دو دونفره تکنفره single double two seater")
PEOPLE = word_set(
    "کودک بچه پسر دختر مادر پدر نوجوان بزرگسال خانم آقا زن مرد child kid boy girl mother father adult woman man"
)
NEGATIONS = word_set(
    "نه نمی نمیشه نیست نباید ندارم ندارد نداره ندارید نداریم بدون هیچ هرگز "
    "not no without never cannot cant dont doesnt don't doesn't can't"
)
QUALIFIERS = word_set("گواهینامه تجربه لباس وزن قد سن مجموع")
UNITS = word_set("ساله سال سانت سانتی متر کیلو کیلوگرم گرم")  # they travel with numbers ("12 ساله", "140 سانت")

DISCRIMINATOR_WORDS = NUMBER_WORDS | WEEKDAYS | DAY_KINDS | VEHICLES | PEOPLE | NEGATIONS | QUALIFIERS | UNITS
