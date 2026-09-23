from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery

normalizer = PersianTextNormalizer()


def test_stopwords_are_removed_for_matching() -> None:
    query = SearchQuery.from_text("آیا قیمت بلیط چقدر است؟", normalizer)
    assert query.tokens == ("قیمت", "بلیط")
    assert query.match_text == "قیمت بلیط"


def test_query_of_only_stopwords_keeps_the_words_instead_of_becoming_empty() -> None:
    assert not SearchQuery.from_text("چه کسی", normalizer).is_empty


def test_blank_query_is_empty() -> None:
    assert SearchQuery.from_text("؟!  ", normalizer).is_empty


def test_arabic_letters_are_normalised_in_the_query() -> None:
    assert SearchQuery.from_text("كارتينگ", normalizer).normalized == "کارتینگ"
