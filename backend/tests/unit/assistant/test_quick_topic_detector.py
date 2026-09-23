from __future__ import annotations

import pytest

from davos.modules.assistant.domain.enums.quick_topic import QuickTopic
from davos.modules.assistant.domain.services.quick_topic_detector import QuickTopicDetector

detector = QuickTopicDetector()


@pytest.mark.parametrize(
    ("text", "topic"),
    [
        ("ساعت کاری چیه؟", QuickTopic.HOURS),
        ("ساعت کاری شما چیه", QuickTopic.HOURS),
        ("سلام ساعات کاری", QuickTopic.HOURS),
        ("تا چه ساعتی باز هستید؟", QuickTopic.HOURS),
        ("ساعت کاریتون چیه", QuickTopic.HOURS),
        ("چطور رزرو کنم؟", QuickTopic.BOOKING),
        ("چجوری نوبت بگیرم", QuickTopic.BOOKING),
        ("رزرو", QuickTopic.BOOKING),
        ("شماره تماس؟", QuickTopic.BOOKING),
        ("شماره تلفن شما چیه", QuickTopic.BOOKING),
        ("ظرفیت چقدره؟", QuickTopic.CAPACITY),
        ("چند نفر میتونن سوار بشن؟", QuickTopic.CAPACITY),
        ("چند تا ماشین دارید؟", QuickTopic.CAPACITY),
        ("قیمت ها چقدره؟", QuickTopic.PRICES),
        ("قیمت‌ها؟", QuickTopic.PRICES),
        ("هزینه چقدره", QuickTopic.PRICES),
        ("تعرفه", QuickTopic.PRICES),
        ("باشگاه مشتریان چیه؟", QuickTopic.CLUB),
        ("عضویت دارید؟", QuickTopic.CLUB),
    ],
)
def test_a_plain_question_about_one_topic_is_recognised(text: str, topic: QuickTopic) -> None:
    assert detector.detect(text) is topic


@pytest.mark.parametrize(
    "text",
    [
        "",
        "سلام",
        "پنجشنبه ساعت کاری چیه؟",  # a day changes the answer
        "ساعت ۱۰ باز هستید؟",  # an hour
        "قیمت دونفره چقدره؟",  # a car type
        "قیمت روز تعطیل چقدره",
        "برای چند نفر رزرو کنم؟",  # two topics
        "قیمت و ساعت کاری",  # two topics
        "میخوام برای فردا رزرو کنم",  # a detail
        "رزرو برای ۸ نفر",
        "شرایط سوار شدن دونفره چیه",  # not a quick topic
        "ساعت شروع سانس چنده",
        "یه پسر ۱۲ ساله میتونه رزرو کنه؟",
        "ساعت کاری " + "خیلی " * 10,  # too long
    ],
)
def test_anything_with_a_detail_or_two_topics_is_left_to_the_normal_flow(text: str) -> None:
    assert detector.detect(text) is None
