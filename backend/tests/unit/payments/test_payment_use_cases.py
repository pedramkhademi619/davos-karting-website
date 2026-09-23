from __future__ import annotations

import uuid

import pytest

from davos.modules.payments.application.ports.gateway_rejected_error import GatewayRejectedError
from davos.modules.payments.application.ports.gateway_timeout_error import GatewayTimeoutError
from davos.modules.payments.application.ports.gateway_unavailable_error import GatewayUnavailableError
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_result import VerificationResult
from davos.modules.payments.application.services.payment_settlement_service import PaymentSettlementService
from davos.modules.payments.application.use_cases.handle_payment_callback_use_case import HandlePaymentCallbackUseCase
from davos.modules.payments.application.use_cases.payment_callback_command import PaymentCallbackCommand
from davos.modules.payments.application.use_cases.reconcile_payments_use_case import ReconcilePaymentsUseCase
from davos.modules.payments.application.use_cases.start_payment_command import StartPaymentCommand
from davos.modules.payments.application.use_cases.start_payment_use_case import StartPaymentUseCase
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.payments.domain.errors.payment_not_found_error import PaymentNotFoundError
from davos.modules.payments.domain.errors.payments_disabled_error import PaymentsDisabledError
from davos.modules.payments.domain.events.payment_succeeded import PaymentSucceeded
from davos.shared_kernel.domain.errors.conflict_error import ConflictError
from tests.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.fixed_order_quotes import FixedOrderQuotes
from tests.fakes.in_memory_payment_repository import InMemoryPaymentRepository
from tests.fakes.scripted_payment_gateway import ScriptedPaymentGateway

S = PaymentStatus
ME = uuid.uuid4()


class Harness:
    def __init__(self, *, enabled: bool = True) -> None:
        self.clock = FixedClock()
        self.uow = FakeUnitOfWork()
        self.repo = InMemoryPaymentRepository()
        self.gateway = ScriptedPaymentGateway()
        self.quotes = FixedOrderQuotes()
        self.quotes.add("order-1", ME, 250_000)
        self.start = StartPaymentUseCase(
            enabled=enabled,
            uow=self.uow,
            payments=self.repo,
            quotes=self.quotes,
            gateway=self.gateway,
            clock=self.clock,
            callback_url="https://davoskarting.ir/payments/callback",
        )
        self.settlement = PaymentSettlementService(
            uow=self.uow, payments=self.repo, gateway=self.gateway, clock=self.clock
        )
        self.callback = HandlePaymentCallbackUseCase(
            uow=self.uow, payments=self.repo, settlement=self.settlement, clock=self.clock
        )
        self.reconcile = ReconcilePaymentsUseCase(
            uow=self.uow, payments=self.repo, settlement=self.settlement, clock=self.clock
        )

    async def started(self):
        result = await self.start.execute(StartPaymentCommand("order-1", ME))
        return self.repo.items[result.payment_id]

    async def come_back(self, status: str = "OK", customer: uuid.UUID = ME, authority: str | None = None):
        return await self.callback.execute(
            PaymentCallbackCommand(
                authority=authority or self.gateway.authority, status_param=status, customer_id=customer
            )
        )

    @property
    def success_events(self) -> int:
        return sum(isinstance(e, PaymentSucceeded) for e in self.uow.published_events)


async def test_the_amount_comes_from_the_server_side_quote() -> None:
    h = Harness()
    payment = await h.started()
    assert payment.amount.irr == 250_000
    assert h.gateway.requests[0].amount.irr == 250_000 and payment.status is S.REDIRECTED
    assert payment.authority == h.gateway.authority


async def test_payments_are_refused_while_the_feature_flag_is_off() -> None:
    h = Harness(enabled=False)
    with pytest.raises(PaymentsDisabledError):
        await h.start.execute(StartPaymentCommand("order-1", ME))
    assert h.gateway.requests == [] and h.repo.items == {}


async def test_unknown_or_foreign_orders_look_the_same() -> None:
    h = Harness()
    with pytest.raises(PaymentNotFoundError):
        await h.start.execute(StartPaymentCommand("order-1", uuid.uuid4()))  # someone else's order
    with pytest.raises(PaymentNotFoundError):
        await h.start.execute(StartPaymentCommand("no-such-order", ME))
    assert h.gateway.requests == []


async def test_gateway_rejection_marks_the_attempt_failed_and_hides_provider_details() -> None:
    h = Harness()
    h.gateway.request_error = GatewayRejectedError(-9)
    with pytest.raises(ConflictError) as info:
        await h.start.execute(StartPaymentCommand("order-1", ME))
    assert info.value.code == "payment_start_failed" and "-9" not in info.value.message
    assert [p.status for p in h.repo.items.values()] == [S.FAILED]


async def test_each_retry_is_a_new_attempt_with_its_own_id() -> None:
    h = Harness()
    h.gateway.request_error = GatewayUnavailableError()
    with pytest.raises(ConflictError):
        await h.start.execute(StartPaymentCommand("order-1", ME))
    h.gateway.request_error = None
    await h.start.execute(StartPaymentCommand("order-1", ME))
    assert len(h.repo.items) == 2 and len({p.id for p in h.repo.items.values()}) == 2


async def test_an_already_paid_order_cannot_be_paid_again() -> None:
    h = Harness()
    await h.started()
    await h.come_back()
    with pytest.raises(ConflictError) as info:
        await h.start.execute(StartPaymentCommand("order-1", ME))
    assert info.value.code == "order_already_paid"


async def test_successful_callback_verifies_with_the_stored_amount_and_records_one_success() -> None:
    h = Harness()
    await h.started()
    result = await h.come_back()
    assert result.status is S.PAID
    assert h.gateway.verifications[0].amount.irr == 250_000  # from our database, not from the browser
    payment = next(iter(h.repo.items.values()))
    assert payment.reference_id == "777" and h.success_events == 1


async def test_a_cancelled_payment_never_calls_the_provider() -> None:
    h = Harness()
    await h.started()
    result = await h.come_back(status="NOK")
    assert result.status is S.FAILED and h.gateway.verifications == []


async def test_status_ok_in_the_url_alone_is_not_success_when_the_provider_disagrees() -> None:
    h = Harness()
    h.gateway.verify_results = [VerificationResult(VerificationOutcome.REJECTED, provider_code=-51)]
    await h.started()
    result = await h.come_back(status="OK")
    assert result.status is S.FAILED and h.success_events == 0


async def test_refreshing_the_callback_page_does_not_pay_twice() -> None:
    h = Harness()
    await h.started()
    for _ in range(4):
        assert (await h.come_back()).status is S.PAID
    assert len(h.gateway.verifications) == 1 and h.success_events == 1


async def test_a_second_concurrent_callback_sees_verifying_and_does_not_call_the_provider() -> None:
    h = Harness()
    payment = await h.started()
    payment.begin_verification(h.clock.now())  # another worker has claimed it
    result = await h.come_back()
    assert result.status is S.VERIFYING and h.gateway.verifications == []


async def test_already_verified_at_the_provider_counts_as_paid() -> None:
    h = Harness()
    h.gateway.verify_results = [
        VerificationResult(VerificationOutcome.ALREADY_VERIFIED, reference_id="777", provider_code=101)
    ]
    await h.started()
    assert (await h.come_back()).status is S.PAID


@pytest.mark.parametrize("error", [GatewayTimeoutError(), GatewayUnavailableError()])
async def test_verification_timeout_or_outage_is_unknown_not_failed(error) -> None:
    h = Harness()
    h.gateway.verify_results = [error]
    await h.started()
    result = await h.come_back()
    assert result.status is S.UNKNOWN and h.success_events == 0
    assert next(iter(h.repo.items.values())).status is not S.FAILED


async def test_customers_cannot_verify_or_view_other_customers_payments() -> None:
    h = Harness()
    await h.started()
    with pytest.raises(PaymentNotFoundError):
        await h.come_back(customer=uuid.uuid4())
    with pytest.raises(PaymentNotFoundError):
        await h.come_back(authority="A-unknown")
    assert h.gateway.verifications == []


async def test_reconciliation_recovers_an_unknown_payment_that_was_actually_paid() -> None:
    h = Harness()
    h.gateway.verify_results = [
        GatewayTimeoutError(),
        VerificationResult(VerificationOutcome.VERIFIED, reference_id="888"),
    ]
    await h.started()
    assert (await h.come_back()).status is S.UNKNOWN
    h.clock.advance(minutes=6)
    report = await h.reconcile.execute()
    assert report.paid == 1 and next(iter(h.repo.items.values())).status is S.PAID and h.success_events == 1


async def test_reconciliation_leaves_recent_unknowns_alone_and_keeps_failing_ones_unknown() -> None:
    h = Harness()
    h.gateway.verify_results = [GatewayTimeoutError()]
    await h.started()
    await h.come_back()
    assert (await h.reconcile.execute()).examined == 0  # too recent
    h.clock.advance(minutes=6)
    report = await h.reconcile.execute()
    assert report.still_unknown == 1 and next(iter(h.repo.items.values())).status is S.UNKNOWN


async def test_reconciliation_recovers_a_verification_that_crashed_midway() -> None:
    h = Harness()
    payment = await h.started()
    payment.begin_verification(h.clock.now())  # worker died right after claiming
    h.clock.advance(minutes=6)
    report = await h.reconcile.execute()
    assert report.paid == 1 and payment.status is S.PAID


async def test_abandoned_attempts_expire_and_are_never_verified() -> None:
    h = Harness()
    await h.started()
    h.clock.advance(minutes=31)
    report = await h.reconcile.execute()
    assert report.expired == 1 and h.gateway.verifications == []
    assert next(iter(h.repo.items.values())).status is S.EXPIRED
