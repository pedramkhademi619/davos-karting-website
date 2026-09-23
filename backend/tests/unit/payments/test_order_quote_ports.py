import uuid

import pytest

from davos.composition.adapters.no_orders_quote_port import NoOrdersQuotePort
from davos.composition.adapters.sandbox_order_quote_port import SandboxOrderQuotePort
from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.app_settings import AppSettings
from davos.platform.settings.insecure_configuration_error import InsecureConfigurationError

ME = uuid.uuid4()


async def test_by_default_nothing_is_payable_so_no_fictional_debt_can_appear() -> None:
    assert await NoOrdersQuotePort().quote("sandbox-test-1", ME) is None
    assert await NoOrdersQuotePort().quote("anything", ME) is None


async def test_the_sandbox_path_only_prices_explicit_test_orders_with_a_fixed_small_amount() -> None:
    port = SandboxOrderQuotePort()
    quote = await port.quote("sandbox-test-42", ME)
    assert quote is not None and quote.amount.irr == 10_000 and "Sandbox" in quote.description
    for order in ("order-1", "sandbox-test-", "sandbox-test-abc", "xsandbox-test-1", "sandbox-test-1234567"):
        assert await port.quote(order, ME) is None


def test_the_sandbox_order_switch_is_refused_in_production() -> None:
    strong = "s" * 40
    settings = AppSettings(
        _env_file=None,
        app_env=AppEnvironment.PRODUCTION,
        otp_hmac_secret=strong,
        session_csrf_secret=strong + "1",
        booking_webhook_secret=strong + "2",
        cors_allowed_origins=["https://davoskarting.ir"],
        payments_sandbox_orders_enabled=True,
    )
    with pytest.raises(InsecureConfigurationError, match="PAYMENTS_SANDBOX_ORDERS_ENABLED"):
        settings.validate_for_environment()
