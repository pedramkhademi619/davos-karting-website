import logging

import pytest

from davos.platform.observability.sensitive_data_filter import SensitiveDataFilter, redact


@pytest.mark.parametrize(
    ("raw", "must_not_contain"),
    [
        ("otp sent to 09123456789", "09123456789"),
        ("user +989123456789 logged in", "989123456789"),
        ("Authorization: Bearer abc.def-123_xyz", "abc.def-123_xyz"),
        ("using key sk-abcdefgh12345678", "abcdefgh12345678"),
        ("code=123456 rejected", "123456"),
        ("password: hunter2 supplied", "hunter2"),
        ("GET /x?mobile=09123456789&token=abcdef123456 HTTP/1.1", "abcdef123456"),
        (
            "GET /pay/callback?Authority=A00000000000000000000000000012345678&Status=OK",
            "A00000000000000000000000000012345678",
        ),
        ("client secret=hunter2hunter2 supplied", "hunter2hunter2"),
    ],
)
def test_redacts_sensitive_values(raw: str, must_not_contain: str) -> None:
    assert must_not_contain not in redact(raw)


def test_a_long_number_that_merely_contains_a_mobile_shaped_run_is_left_alone() -> None:
    timing = "Task succeeded in 1.5309123456789012s"
    assert redact(timing) == timing


@pytest.mark.parametrize("raw", ["call (09123456789)", "mobile=09123456789.", "+989123456789,", "(00989123456789)"])
def test_mobile_numbers_are_still_masked_next_to_punctuation(raw: str) -> None:
    assert "9123456789" not in redact(raw)


def test_filter_masks_values_that_arrive_through_log_arguments(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("redaction-test")
    logger.addFilter(SensitiveDataFilter())
    with caplog.at_level(logging.INFO, logger="redaction-test"):
        logger.info("login for %s", "09123456789")
    assert "09123456789" not in caplog.text
