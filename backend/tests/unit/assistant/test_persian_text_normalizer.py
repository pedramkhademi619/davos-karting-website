import pytest

from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer

normalizer = PersianTextNormalizer()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("كارتينگ", "کارتینگ"),  # Arabic kaf and yeh -> Persian
        ("علي", "علی"),
        ("مى‌خواهم", "می خواهم"),  # alef maqsura + ZWNJ
        ("ساعت ۱۰ تا ١٢", "ساعت 10 تا 12"),  # Persian and Arabic-Indic digits
        ("قِیمَت", "قیمت"),  # diacritics
        ("ســلام", "سلام"),  # tatweel
        ("  چند   فاصله  ", "چند فاصله"),
        ("قیمت؟! بلیط...", "قیمت بلیط"),
        ("Karting PRICE", "karting price"),
        ("", ""),
    ],
)
def test_normalisation(raw: str, expected: str) -> None:
    assert normalizer.normalize(raw) == expected


def test_variants_of_the_same_word_normalise_identically() -> None:
    assert normalizer.normalize("پیست کارتینگ") == normalizer.normalize("پيست كارتينگ")


def test_is_idempotent() -> None:
    once = normalizer.normalize("كارتينگ ۱۲۳ می‌خواهم")
    assert normalizer.normalize(once) == once
