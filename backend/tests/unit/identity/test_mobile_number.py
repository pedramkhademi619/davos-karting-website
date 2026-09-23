import pytest

from davos.modules.identity.domain.errors.invalid_mobile_number_error import InvalidMobileNumberError
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber


@pytest.mark.parametrize(
    "raw",
    [
        "09123456789",
        "9123456789",
        "989123456789",
        "+989123456789",
        "00989123456789",
        "0912 345 6789",
        "0912-345-6789",
        "۰۹۱۲۳۴۵۶۷۸۹",  # Persian digits
        "٠٩١٢٣٤٥٦٧٨٩",  # Arabic-Indic digits
        "+98 (912) 345-6789",
    ],
)
def test_normalises_every_common_spelling_to_e164(raw: str) -> None:
    assert MobileNumber.parse(raw).e164 == "+989123456789"


@pytest.mark.parametrize(
    "raw",
    ["", "123", "0912345678", "091234567890", "08123456789", "+441234567890", "abcdefghijk", "09123456789x"],
)
def test_rejects_invalid_numbers(raw: str) -> None:
    with pytest.raises(InvalidMobileNumberError):
        MobileNumber.parse(raw)


def test_local_and_masked_forms() -> None:
    mobile = MobileNumber.parse("09123456789")
    assert mobile.local == "09123456789"
    assert mobile.masked() == "+98912***6789"
    assert "345" not in mobile.masked()
