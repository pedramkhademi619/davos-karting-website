from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_result import VerificationResult
from davos.modules.payments.application.use_cases.payment_callback_command import PaymentCallbackCommand
from davos.modules.payments.application.use_cases.start_payment_command import StartPaymentCommand
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from tests.fakes.fixed_order_quotes import FixedOrderQuotes
from tests.fakes.scripted_payment_gateway import ScriptedPaymentGateway

pytestmark = pytest.mark.integration
ME = uuid.uuid4()


@pytest.fixture(autouse=True)
def order(quotes: FixedOrderQuotes) -> None:
    quotes.add("order-1", ME, 250_000)


async def test_full_flow_is_persisted_and_the_outbox_receives_one_success_event(
    container: ApplicationContainer, gateway: ScriptedPaymentGateway, engine: AsyncEngine
) -> None:
    started = await container.start_payment().execute(StartPaymentCommand("order-1", ME))
    result = await container.handle_payment_callback().execute(
        PaymentCallbackCommand(authority=gateway.authority, status_param="OK", customer_id=ME)
    )
    assert result.status is PaymentStatus.PAID

    async with engine.connect() as conn:
        row = (
            await conn.execute(text("SELECT status, amount_irr, reference_id, authority FROM payments_attempts"))
        ).one()
        events = (await conn.execute(text("SELECT event_name, payload FROM outbox_messages"))).all()
    assert (row.status, row.amount_irr, row.reference_id) == ("paid", 250_000, "777")
    assert [e[0] for e in events] == ["payments.PaymentSucceeded"]
    assert events[0][1]["payment_id"] == str(started.payment_id) and events[0][1]["amount_irr"] == 250_000


async def test_concurrent_callbacks_verify_once_and_record_one_success(
    container: ApplicationContainer, gateway: ScriptedPaymentGateway, engine: AsyncEngine
) -> None:
    gateway.verify_delay = 0.2  # widen the race window
    await container.start_payment().execute(StartPaymentCommand("order-1", ME))

    async def callback() -> PaymentStatus:
        return (
            await container.handle_payment_callback().execute(
                PaymentCallbackCommand(authority=gateway.authority, status_param="OK", customer_id=ME)
            )
        ).status

    statuses = await asyncio.gather(*(callback() for _ in range(10)))

    assert len(gateway.verifications) == 1  # the provider was asked exactly once
    assert PaymentStatus.PAID in statuses
    assert set(statuses) <= {PaymentStatus.PAID, PaymentStatus.VERIFYING}
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM outbox_messages"))).scalar_one() == 1
        assert (await conn.execute(text("SELECT status FROM payments_attempts"))).scalar_one() == "paid"


async def test_the_database_refuses_two_successful_payments_for_one_order(engine: AsyncEngine) -> None:
    insert = text(
        "INSERT INTO payments_attempts (id, order_ref, customer_id, amount_irr, status, reference_id, "
        "created_at, updated_at, expires_at) "
        "VALUES (gen_random_uuid(), 'order-9', gen_random_uuid(), 1000, :status, :ref, now(), now(), now())"
    )
    async with engine.begin() as conn:
        await conn.execute(insert, {"status": "paid", "ref": "1"})
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(insert, {"status": "paid", "ref": "2"})
    async with engine.begin() as conn:  # a failed attempt for the same order is fine
        await conn.execute(insert, {"status": "failed", "ref": None})


@pytest.mark.parametrize(
    "values",
    [
        {"amount": 0, "status": "created", "ref": None},
        {"amount": -5, "status": "created", "ref": None},
        {"amount": 100, "status": "settled", "ref": None},
        {"amount": 100, "status": "paid", "ref": None},
    ],
)
async def test_database_constraints_reject_impossible_payments(engine: AsyncEngine, values: dict) -> None:
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    "INSERT INTO payments_attempts (id, order_ref, customer_id, amount_irr, status, reference_id, "
                    "created_at, updated_at, expires_at) "
                    "VALUES (gen_random_uuid(), 'o', gen_random_uuid(), :amount, :status, :ref, now(), now(), now())"
                ),
                values,
            )


async def test_authority_is_unique_across_attempts(engine: AsyncEngine) -> None:
    insert = text(
        "INSERT INTO payments_attempts (id, order_ref, customer_id, amount_irr, status, authority, "
        "created_at, updated_at, expires_at) "
        "VALUES (gen_random_uuid(), :o, gen_random_uuid(), 1000, 'redirected', 'A-same', now(), now(), now())"
    )
    async with engine.begin() as conn:
        await conn.execute(insert, {"o": "one"})
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(insert, {"o": "two"})


async def test_reconciliation_finds_unknown_payments_in_the_database(
    container: ApplicationContainer, gateway: ScriptedPaymentGateway, clock
) -> None:
    from davos.modules.payments.application.ports.gateway_timeout_error import GatewayTimeoutError

    gateway.verify_results = [GatewayTimeoutError(), VerificationResult(VerificationOutcome.VERIFIED, reference_id="9")]
    await container.start_payment().execute(StartPaymentCommand("order-1", ME))
    first = await container.handle_payment_callback().execute(
        PaymentCallbackCommand(authority=gateway.authority, status_param="OK", customer_id=ME)
    )
    assert first.status is PaymentStatus.UNKNOWN

    clock.advance(minutes=6)
    report = await container.reconcile_payments().execute()
    assert report.paid == 1


async def test_a_customer_cannot_read_or_verify_someone_elses_payment(
    container: ApplicationContainer, gateway: ScriptedPaymentGateway
) -> None:
    from davos.modules.payments.domain.errors.payment_not_found_error import PaymentNotFoundError

    await container.start_payment().execute(StartPaymentCommand("order-1", ME))
    with pytest.raises(PaymentNotFoundError):
        await container.handle_payment_callback().execute(
            PaymentCallbackCommand(authority=gateway.authority, status_param="OK", customer_id=uuid.uuid4())
        )
    assert gateway.verifications == []
