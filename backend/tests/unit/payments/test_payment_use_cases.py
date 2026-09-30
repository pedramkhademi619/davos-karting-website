from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from davos.modules.payments.application.ports.gateway_rejected_error import GatewayRejectedError
from davos.modules.payments.application.ports.gateway_timeout_error import GatewayTimeoutError
from davos.modules.payments.application.ports.gateway_unavailable_error import GatewayUnavailableError
from davos.modules.payments.application.ports.settlement_outcome import SettlementOutcome
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
from davos.modules.payments.domain.events.payment_reversed import PaymentReversed
from davos.modules.payments.domain.events.payment_succeeded import PaymentSucceeded
from davos.shared_kernel.domain.errors.conflict_error import ConflictError
from davos.shared_kernel.domain.errors.validation_error import ValidationError
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
            callback_url="https://davoskarting.ir/api/v1/payments/mellat/callback",
            attempt_ttl=timedelta(minutes=30),
        )
        self.settlement = PaymentSettlementService(
            uow=self.uow, payments=self.repo, gateway=self.gateway, orders=self.quotes, clock=self.clock
        )
        self.callback = HandlePaymentCallbackUseCase(
            uow=self.uow, payments=self.repo, settlement=self.settlement, clock=self.clock
        )
        self.reconcile = ReconcilePaymentsUseCase(
            uow=self.uow,
            payments=self.repo,
            settlement=self.settlement,
            clock=self.clock,
            stuck_for_seconds=120,
            batch_size=50,
        )

    async def started(self, authority: str | None = None):
        if authority:
            self.gateway.authority = authority
        result = await self.start.execute(StartPaymentCommand("order-1", ME))
        return self.repo.items[result.payment_id]

    async def come_back(
        self,
        succeeded: bool = True,
        customer: uuid.UUID | None = ME,
        authority: str | None = None,
        gateway_order_id: int | None = None,
        reference: str | None = None,
    ):
        return await self.callback.execute(
            PaymentCallbackCommand(
                authority=authority or self.gateway.authority,
                succeeded=succeeded,
                customer_id=customer,
                gateway_order_id=gateway_order_id,
                provider_reference=reference,
            )
        )

    @property
    def success_events(self) -> int:
        return sum(isinstance(e, PaymentSucceeded) for e in self.uow.published_events)

    @property
    def reversed_events(self) -> list[PaymentReversed]:
        return [e for e in self.uow.published_events if isinstance(e, PaymentReversed)]

    def only(self):
        (payment,) = self.repo.items.values()
        return payment


# ---------------------------------------------------------------- starting


async def test_the_amount_comes_from_the_server_side_quote() -> None:
    h = Harness()
    payment = await h.started()
    assert payment.amount.irr == 250_000
    assert h.gateway.requests[0].amount.irr == 250_000 and payment.status is S.REDIRECTED
    assert payment.authority == h.gateway.authority and payment.gateway == "scripted"


async def test_every_attempt_gets_its_own_numeric_bank_order_id() -> None:
    h = Harness()
    first = await h.started()
    h.gateway.authority = "A-second"
    second = await h.start.execute(StartPaymentCommand("order-1", ME))
    ids = [first.gateway_order_id, h.repo.items[second.payment_id].gateway_order_id]
    assert all(isinstance(i, int) and i > 0 for i in ids) and ids[0] != ids[1]
    assert [r.gateway_order_id for r in h.gateway.requests] == ids


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


# ---------------------------------------------------------------- verification and settlement


async def test_successful_callback_verifies_settles_and_records_one_success() -> None:
    h = Harness()
    payment = await h.started()
    result = await h.come_back(gateway_order_id=payment.gateway_order_id, reference="123456789")
    assert result.status is S.PAID and result.order_ref == "order-1"
    verification = h.gateway.verifications[0]
    assert verification.amount.irr == 250_000  # from our database, not from the browser
    assert verification.gateway_order_id == payment.gateway_order_id and verification.provider_reference == "123456789"
    assert h.gateway.settlements == [verification]
    assert payment.reference_id == "777" and payment.settled_at is not None and h.success_events == 1
    assert h.quotes.acceptance_checks == ["order-1"]  # the order was asked before the money was taken


async def test_a_cancelled_payment_never_calls_the_bank() -> None:
    h = Harness()
    await h.started()
    result = await h.come_back(succeeded=False)
    assert result.status is S.FAILED and h.gateway.verifications == []


async def test_a_not_paid_callback_cannot_fail_an_attempt_the_bank_already_reported_as_paid() -> None:
    h = Harness()
    payment = await h.started()
    payment.record_provider_reference("555", h.clock.now())
    result = await h.come_back(succeeded=False)
    assert result.status is S.REDIRECTED and payment.status is S.REDIRECTED  # left for verification


async def test_success_in_the_callback_alone_is_not_success_when_the_bank_disagrees() -> None:
    h = Harness()
    h.gateway.verify_results = [VerificationResult(VerificationOutcome.REJECTED, provider_code=-51)]
    await h.started()
    result = await h.come_back()
    assert result.status is S.FAILED and h.success_events == 0 and h.gateway.settlements == []


async def test_refreshing_the_callback_page_does_not_pay_twice() -> None:
    h = Harness()
    await h.started()
    for _ in range(4):
        assert (await h.come_back()).status is S.PAID
    assert len(h.gateway.verifications) == 1 and len(h.gateway.settlements) == 1 and h.success_events == 1


async def test_a_second_concurrent_callback_sees_verifying_and_does_not_call_the_bank() -> None:
    h = Harness()
    payment = await h.started()
    payment.begin_verification(h.clock.now())  # another worker has claimed it
    result = await h.come_back()
    assert result.status is S.VERIFYING and h.gateway.verifications == []


async def test_already_verified_at_the_bank_counts_as_paid() -> None:
    h = Harness()
    h.gateway.verify_results = [
        VerificationResult(VerificationOutcome.ALREADY_VERIFIED, reference_id="777", provider_code=43)
    ]
    await h.started()
    assert (await h.come_back()).status is S.PAID


@pytest.mark.parametrize("error", [GatewayTimeoutError(), GatewayUnavailableError()])
async def test_verification_timeout_or_outage_is_unknown_not_failed(error) -> None:
    h = Harness()
    h.gateway.verify_results = [error]
    await h.started()
    result = await h.come_back()
    assert result.status is S.UNKNOWN and h.success_events == 0 and h.only().status is not S.FAILED


async def test_callbacks_cannot_be_pointed_at_another_attempt() -> None:
    h = Harness()
    payment = await h.started()
    with pytest.raises(PaymentNotFoundError):
        await h.come_back(customer=uuid.uuid4())
    with pytest.raises(PaymentNotFoundError):
        await h.come_back(authority="A-unknown")
    with pytest.raises(PaymentNotFoundError):
        await h.come_back(gateway_order_id=(payment.gateway_order_id or 0) + 1)  # RefId of one, order id of another
    assert h.gateway.verifications == []


@pytest.mark.parametrize("reference", ["abc", "۱۲۳۴", "1" * 65, " "])
async def test_a_malformed_bank_reference_is_refused(reference: str) -> None:
    h = Harness()
    await h.started()
    with pytest.raises(ValidationError):
        await h.come_back(reference=reference)
    assert h.gateway.verifications == []


# ---------------------------------------------------------------- money that must go back


async def test_money_for_an_order_that_no_longer_accepts_it_is_reversed_not_settled() -> None:
    h = Harness()
    await h.started()
    h.quotes.refusing.add("order-1")  # e.g. the reservation was cancelled while the customer was paying
    result = await h.come_back()
    payment = h.only()
    assert result.status is S.REVERSED and payment.status is S.REVERSED
    assert payment.failure_reason == "order_not_payable" and h.gateway.settlements == []
    assert len(h.gateway.reversals) == 1 and h.success_events == 0
    assert [e.was_paid for e in h.reversed_events] == [False]


async def test_an_order_paid_twice_in_two_tabs_keeps_one_payment_and_returns_the_other() -> None:
    h = Harness()
    first = await h.started(authority="A-first")
    second = await h.started(authority="A-second")
    assert (await h.come_back(authority="A-first")).status is S.PAID
    assert (await h.come_back(authority="A-second")).status is S.REVERSED
    assert first.status is S.PAID and second.status is S.REVERSED and second.failure_reason == "duplicate_payment"
    assert h.success_events == 1 and len(h.gateway.settlements) == 1 and len(h.gateway.reversals) == 1
    assert "order-1" in h.repo.locked_orders  # the duplicate check ran under the per-order lock


async def test_a_refused_reversal_stays_pending_and_is_retried() -> None:
    h = Harness()
    h.gateway.reverse_results = [False, True]
    await h.started()
    h.quotes.refusing.add("order-1")
    assert (await h.come_back()).status is S.REFUND_PENDING
    await h.reconcile.execute()
    assert h.only().status is S.REVERSED and len(h.gateway.reversals) == 2


async def test_a_failing_order_check_keeps_the_money_safe_as_unknown() -> None:
    h = Harness()

    async def broken(*_: object) -> bool:
        raise RuntimeError("database down")

    h.quotes.accepts_payment = broken  # type: ignore[method-assign]
    await h.started()
    assert (await h.come_back()).status is S.UNKNOWN
    assert h.gateway.settlements == [] and h.gateway.reversals == []


# ---------------------------------------------------------------- settlement retries


@pytest.mark.parametrize("problem", [GatewayTimeoutError(), SettlementOutcome.RETRY])
async def test_an_unconfirmed_settlement_is_retried_by_reconciliation(problem) -> None:
    h = Harness()
    h.gateway.settle_results = [problem, SettlementOutcome.SETTLED]
    await h.started()
    assert (await h.come_back()).status is S.PAID
    payment = h.only()
    assert payment.settled_at is None and payment.needs_settlement
    assert (await h.reconcile.execute()).examined == 0  # too recent
    h.clock.advance(minutes=3)
    await h.reconcile.execute()
    assert payment.settled_at is not None and len(h.gateway.settlements) == 2 and h.success_events == 1


async def test_a_payment_the_bank_reversed_before_settlement_is_undone() -> None:
    h = Harness()
    h.gateway.settle_results = [SettlementOutcome.REVERSED]
    await h.started()
    assert (await h.come_back()).status is S.REVERSED
    assert [e.was_paid for e in h.reversed_events] == [True]  # the order must be told it is no longer paid


# ---------------------------------------------------------------- reconciliation


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
    assert report.paid == 1 and h.only().status is S.PAID and h.success_events == 1


async def test_reconciliation_leaves_recent_unknowns_alone_and_keeps_failing_ones_unknown() -> None:
    h = Harness()
    h.gateway.verify_results = [GatewayTimeoutError()]
    await h.started()
    await h.come_back()
    assert (await h.reconcile.execute()).examined == 0  # too recent
    h.clock.advance(minutes=6)
    report = await h.reconcile.execute()
    assert report.still_unknown == 1 and h.only().status is S.UNKNOWN


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
    assert h.only().status is S.EXPIRED


async def test_an_attempt_the_bank_reported_back_on_never_expires_unverified() -> None:
    h = Harness()
    payment = await h.started()
    payment.record_provider_reference("999", h.clock.now())
    h.clock.advance(minutes=31)
    await h.reconcile.execute()
    assert payment.status is S.PAID and len(h.gateway.verifications) == 1
