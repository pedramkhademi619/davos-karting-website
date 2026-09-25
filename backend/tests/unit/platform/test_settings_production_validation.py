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
        "public_base_url": "https://davoskarting.ir",
        "sms_provider": "kavenegar",
        "kavenegar_api_key": "kavenegar-key",
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
        ({"payment_provider": "zarinpal", "zarinpal_sandbox": True, "payments_enabled": True}, "sandbox"),
        ({"payments_enabled": True}, "MELLAT_TERMINAL_ID"),
        ({"payment_provider": "paypal"}, "PAYMENT_PROVIDER"),
        ({"sms_provider": "recording"}, "KAVENEGAR_API_KEY"),
        ({"kavenegar_api_key": ""}, "KAVENEGAR_API_KEY"),
        ({"public_base_url": "http://davoskarting.ir"}, "PUBLIC_BASE_URL"),
        ({"booking_base_url": "http://booking.davoskarting.ir"}, "BOOKING_BASE_URL"),
        (
            {
                "payments_enabled": True,
                "mellat_terminal_id": 1,
                "mellat_username": "u",
                "mellat_password": "p",
                "payment_callback_url": "http://davoskarting.ir/cb",
            },
            "callback URL",
        ),
    ],
)
def test_production_refuses_unsafe_configuration(overrides: dict[str, object], fragment: str) -> None:
    with pytest.raises(InsecureConfigurationError, match=fragment):
        production(**overrides).validate_for_environment()


def test_all_problems_are_reported_together() -> None:
    with pytest.raises(InsecureConfigurationError) as info:
        production(dev_sms_echo_enabled=True, cookie_secure=False).validate_for_environment()
    assert "DEV_SMS_ECHO_ENABLED" in str(info.value) and "COOKIE_SECURE" in str(info.value)


def test_mellat_payments_start_in_production_with_complete_credentials() -> None:
    production(
        payments_enabled=True, mellat_terminal_id=1234567, mellat_username="davos", mellat_password="secret"
    ).validate_for_environment()


def test_the_bank_returns_customers_to_the_booking_subdomain_when_there_is_one() -> None:
    split = production(booking_base_url="https://booking.davoskarting.ir/")
    assert split.booking_site_url == "https://booking.davoskarting.ir"
    assert split.effective_payment_callback_url == "https://booking.davoskarting.ir/api/v1/payments/mellat/callback"
    single = production()
    assert single.booking_site_url == "https://davoskarting.ir"  # no subdomain: everything on the main site


def test_the_sites_own_addresses_are_always_trusted_origins() -> None:
    settings = production(
        booking_base_url="https://booking.davoskarting.ir", cors_allowed_origins=["https://x.example"]
    )
    assert settings.trusted_origins == {
        "https://davoskarting.ir",
        "https://booking.davoskarting.ir",
        "https://x.example",
    }
    local = AppSettings(_env_file=None, public_base_url="http://localhost:8088", cors_allowed_origins=[])
    assert local.trusted_origins == {"http://localhost:8088"}
