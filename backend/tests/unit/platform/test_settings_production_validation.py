import pytest

from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.app_settings import AppSettings
from davos.platform.settings.insecure_configuration_error import InsecureConfigurationError

STRONG = "x" * 40


def production(**overrides: object) -> AppSettings:
    values: dict[str, object] = {
        "app_env": AppEnvironment.PRODUCTION,
        "otp_hmac_secret": STRONG,
        "session_csrf_secret": STRONG + "1",
        "booking_webhook_secret": STRONG + "2",
        "cors_allowed_origins": ["https://davoskarting.ir"],
    }
    return AppSettings(_env_file=None, **{**values, **overrides})  # type: ignore[arg-type]


def test_a_correct_production_configuration_starts() -> None:
    production().validate_for_environment()


def test_development_accepts_placeholders() -> None:
    AppSettings(_env_file=None).validate_for_environment()


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"otp_hmac_secret": "dev-only-insecure-secret-change-me-0123456789"}, "otp_hmac_secret"),
        ({"session_csrf_secret": "short"}, "session_csrf_secret"),
        ({"booking_webhook_secret": ""}, "booking_webhook_secret"),
        ({"dev_sms_echo_enabled": True}, "DEV_SMS_ECHO_ENABLED"),
        ({"cookie_secure": False}, "COOKIE_SECURE"),
        ({"cors_allowed_origins": ["*"]}, "CORS_ALLOWED_ORIGINS"),
        ({"ai_base_url": "http://ai.example.test/v1"}, "https"),
        ({"zarinpal_sandbox": True, "payments_enabled": True}, "sandbox"),
    ],
)
def test_production_refuses_unsafe_configuration(overrides: dict[str, object], fragment: str) -> None:
    with pytest.raises(InsecureConfigurationError, match=fragment):
        production(**overrides).validate_for_environment()


def test_all_problems_are_reported_together() -> None:
    with pytest.raises(InsecureConfigurationError) as info:
        production(dev_sms_echo_enabled=True, cookie_secure=False).validate_for_environment()
    assert "DEV_SMS_ECHO_ENABLED" in str(info.value) and "COOKIE_SECURE" in str(info.value)
