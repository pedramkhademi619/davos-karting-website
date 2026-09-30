import uuid

import pytest

from davos.composition.adapters.reservation_order_quote_port import ReservationOrderQuotePort
from davos.composition.adapters.sandbox_order_quote_port import SandboxOrderQuotePort
from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.insecure_configuration_error import InsecureConfigurationError
from davos.shared_kernel.domain.money import Money
from tests.fakes.standard_config import example_settings

ME = uuid.uuid4()


def test_reservation_order_refs_round_trip_and_nothing_else_parses() -> None:
    reservation_id = uuid.uuid4()
    ref = ReservationOrderQuotePort.order_ref_for(reservation_id)
    assert ref == f"reservation:{reservation_id}"
    assert ReservationOrderQuotePort.reservation_id_of(ref) == reservation_id
    for other in ("sandbox-test-1", "reservation:", "reservation:not-a-uuid", f"x{ref}", str(reservation_id)):
        assert ReservationOrderQuotePort.reservation_id_of(other) is None


async def test_only_reservation_orders_are_payable_on_the_site() -> None:
    def unused():  # the order refs below never reach the reservation module
        raise AssertionError("should not be called")

    port = ReservationOrderQuotePort(unused, unused)  # type: ignore[arg-type]
    assert await port.quote("sandbox-test-1", ME) is None
    assert await port.quote("anything", ME) is None
    assert await port.accepts_payment("anything", ME, Money(1)) is False


async def test_the_sandbox_path_only_prices_explicit_test_orders_with_a_fixed_small_amount() -> None:
    port = SandboxOrderQuotePort()
    quote = await port.quote("sandbox-test-42", ME)
    assert quote is not None and quote.amount.irr == 10_000 and "Sandbox" in quote.description
    for order in ("order-1", "sandbox-test-", "sandbox-test-abc", "xsandbox-test-1", "sandbox-test-1234567"):
        assert await port.quote(order, ME) is None
    assert await port.accepts_payment("sandbox-test-42", ME, Money(10_000)) is True
    assert await port.accepts_payment("sandbox-test-42", ME, Money(10_001)) is False


def test_the_sandbox_order_switch_is_refused_in_production() -> None:
    strong = "s" * 40
    settings = example_settings(
        app_env=AppEnvironment.PRODUCTION,
        otp_hmac_secret=strong,
        session_csrf_secret=strong + "1",
        booking_webhook_secret=strong + "2",
        cors_allowed_origins=["https://davoskarting.ir"],
        payments_sandbox_orders_enabled=True,
    )
    with pytest.raises(InsecureConfigurationError, match="PAYMENTS_SANDBOX_ORDERS_ENABLED"):
        settings.validate_for_environment()
