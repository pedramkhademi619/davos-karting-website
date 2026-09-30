"""Online reservations end to end: real PostgreSQL, the real reservation <-> payment bridge, a scripted bank."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, time

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.api.app_factory import create_app
from davos.composition.application_container import ApplicationContainer
from davos.composition.reservation_payment_events import ReservationPaymentEvents
from davos.modules.assistant.adapters.budget.in_memory_ai_budget import InMemoryAiBudget
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.modules.payments.application.use_cases.payment_callback_command import PaymentCallbackCommand
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.reservations.application.use_cases.hold_reservation_command import HoldReservationCommand
from davos.modules.reservations.application.use_cases.staff_reservation_command import StaffReservationCommand
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.errors.session_full_error import SessionFullError
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from davos.platform.settings.app_settings import AppSettings
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.scripted_ai_chat import ScriptedAiChat
from tests.fakes.scripted_payment_gateway import ScriptedPaymentGateway
from tests.integration.api.conftest import sign_in

pytestmark = pytest.mark.integration

SUNDAY = date(2026, 1, 4)
SIX_PM = time(18, 0)
FORM = {"Content-Type": "application/x-www-form-urlencoded"}


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 1, 3, 6, 0, tzinfo=UTC))  # Saturday 09:30 in Tehran: Sunday is bookable


@pytest.fixture
def reservations(
    test_settings: AppSettings,
    engine: AsyncEngine,
    clock: FixedClock,
    sms_gateway: RecordingSmsGateway,
    gateway: ScriptedPaymentGateway,
) -> ApplicationContainer:
    return ApplicationContainer(
        settings=test_settings,
        engine=engine,
        redis=None,
        clock=clock,
        rate_limiter=InMemoryRateLimiter(clock),
        sms_gateway=sms_gateway,
        ai_chat=ScriptedAiChat("پاسخ [1]"),
        ai_budget=InMemoryAiBudget(daily_limit=1_000_000, clock=clock),
        payment_gateway=gateway,
    )  # no order_quotes: the real reservation bridge is used


@pytest.fixture
async def site(reservations: ApplicationContainer, test_settings: AppSettings) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(
        app=create_app(test_settings, reservations), client=("203.0.113.5", 1), raise_app_exceptions=False
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def hold(customer: uuid.UUID, singles: int, doubles: int = 0, at: time = SIX_PM) -> HoldReservationCommand:
    return HoldReservationCommand(
        customer_id=customer,
        day=SUNDAY,
        session_time=at,
        single_count=singles,
        double_count=doubles,
        contact_name="مشتری",
        contact_mobile="09120000000",
    )


async def test_the_calendar_offers_tomorrow_with_prices_and_every_session(site: httpx.AsyncClient) -> None:
    calendar = (await site.get("/api/v1/reservations/calendar")).json()
    assert [d["date"] for d in calendar["days"]] == ["2026-01-04"]
    assert calendar["days"][0]["single_price_toman"] == 790_000 and calendar["days"][0]["weekday"] == "یکشنبه"
    day = (await site.get("/api/v1/reservations/availability", params={"date": "2026-01-04"})).json()
    assert len(day["sessions"]) == 40 and day["sessions"][0]["time"] == "15:00"
    assert all(s["bookable"] and s["singles_left"] == 6 and s["doubles_left"] == 1 for s in day["sessions"])
    assert day["date_jalali"] == "1404/10/14"


async def test_book_pay_and_get_a_confirmed_ticket_and_an_sms(
    site: httpx.AsyncClient,
    reservations: ApplicationContainer,
    sms_gateway: RecordingSmsGateway,
    gateway: ScriptedPaymentGateway,
    engine: AsyncEngine,
) -> None:
    customer = await sign_in(site, sms_gateway)
    created = await site.post(
        "/api/v1/reservations",
        json={"date": "2026-01-04", "time": "18:00", "single_count": 2, "double_count": 1, "contact_name": "سارا"},
        headers=customer.headers,
    )
    assert created.status_code == 201, created.text
    reservation = created.json()
    assert reservation["status"] == "held" and reservation["amount_toman"] == 2 * 790_000 + 1_000_000
    assert reservation["contact_mobile"] == "09123456789" and reservation["code"].startswith("DK-")

    paying = await site.post(f"/api/v1/reservations/{reservation['id']}/pay", headers=customer.headers)
    assert paying.status_code == 200 and gateway.requests[0].amount.irr == reservation["amount_toman"] * 10
    order_id = gateway.requests[0].gateway_order_id

    site.cookies.clear()  # the bank's form post arrives without the session cookie
    back = await site.post(
        "/api/v1/payments/mellat/callback",
        content=f"RefId={gateway.authority}&ResCode=0&SaleOrderId={order_id}&SaleReferenceId=112233",
        headers=FORM,
    )
    assert back.status_code == 303 and "payment=" in back.headers["location"]

    site.cookies.set("davos_session", customer.cookie)
    ticket = (await site.get(f"/api/v1/account/reservations/{reservation['id']}")).json()
    assert ticket["status"] == "confirmed" and ticket["confirmed_late"] is False
    left = (await site.get("/api/v1/reservations/availability", params={"date": "2026-01-04"})).json()
    six = next(s for s in left["sessions"] if s["time"] == "18:00")
    assert (six["singles_left"], six["doubles_left"]) == (4, 0)

    async with engine.connect() as conn:
        events = (await conn.execute(text("SELECT event_name, payload FROM outbox_messages ORDER BY created_at"))).all()
    names = [e[0] for e in events]
    assert "payments.PaymentSucceeded" in names and names.count("reservations.ReservationConfirmed") == 1

    confirmed = next(e[1] for e in events if e[0] == "reservations.ReservationConfirmed")
    await ReservationPaymentEvents(reservations).handle("reservations.ReservationConfirmed", confirmed)
    sms = [m for m in sms_gateway.sent if m.template_key == "reservation_confirmed"]
    assert len(sms) == 1 and sms[0].to_local_mobile == "09123456789" and sms[0].parameters["ticket"] == ticket["code"]
    async with engine.connect() as conn:
        logged = (await conn.execute(text("SELECT kind, recipient, status FROM notifications_sms_messages"))).all()
    assert [tuple(r) for r in logged] == [("transactional", "09123456789", "queued")]

    # The same event again (queue retry) confirms nothing twice.
    paid = next(e[1] for e in events if e[0] == "payments.PaymentSucceeded")
    await ReservationPaymentEvents(reservations).handle("payments.PaymentSucceeded", paid)
    async with engine.connect() as conn:
        count = (
            await conn.execute(text("SELECT count(*) FROM outbox_messages WHERE event_name LIKE 'reservations.%'"))
        ).scalar_one()
    assert count == 1


async def test_two_customers_racing_for_the_last_karts_never_both_get_them(reservations: ApplicationContainer) -> None:
    async def attempt(customer: uuid.UUID) -> bool:
        try:
            await reservations.hold_reservation().execute(hold(customer, 4))
        except SessionFullError:
            return False
        return True

    results = await asyncio.gather(*(attempt(uuid.uuid4()) for _ in range(5)))
    assert results.count(True) == 1
    day = await reservations.day_availability().execute(SUNDAY)
    assert next(s for s in day.sessions if s.session_time == SIX_PM).singles_left == 2


async def test_a_crowd_racing_for_the_same_sessions_never_oversells_any_of_them(
    reservations: ApplicationContainer,
) -> None:
    """50 customers on real PostgreSQL connections at once, 1-3 singles (sometimes + the double), in 3 sessions."""
    sessions = (time(18, 0), time(18, 15), time(18, 30))

    async def attempt(index: int) -> tuple[time, int, int] | None:
        at = sessions[index % 3]
        singles, doubles = 1 + index % 3, 1 if index % 7 == 0 else 0
        try:
            await reservations.hold_reservation().execute(hold(uuid.uuid4(), singles, doubles, at=at))
        except SessionFullError:
            return None
        return at, singles, doubles

    results = await asyncio.gather(*(attempt(i) for i in range(50)))
    won = [r for r in results if r is not None]
    assert won, "nobody got a kart"
    day = await reservations.day_availability().execute(SUNDAY)
    for at in sessions:
        singles = sum(r[1] for r in won if r[0] == at)
        doubles = sum(r[2] for r in won if r[0] == at)
        assert singles <= 6 and doubles <= 1, f"{at}: {singles} singles / {doubles} doubles sold"
        session = next(s for s in day.sessions if s.session_time == at)
        assert (session.singles_left, session.doubles_left) == (6 - singles, 1 - doubles)


async def test_a_payment_verified_in_the_last_seconds_keeps_its_karts_until_it_is_recorded(
    reservations: ApplicationContainer, clock: FixedClock, gateway: ScriptedPaymentGateway
) -> None:
    customer = uuid.uuid4()
    held = await reservations.hold_reservation().execute(hold(customer, 6))
    started = await pay(reservations, held.id, customer)
    clock.advance(minutes=19, seconds=59)
    result = await come_back(reservations, gateway, started)  # verified one second before the hold runs out
    assert result.status is PaymentStatus.PAID
    clock.advance(minutes=2)  # the original hold is over; the confirmation is still on its way
    with pytest.raises(SessionFullError):
        await reservations.hold_reservation().execute(hold(uuid.uuid4(), 1))
    await ReservationPaymentEvents(reservations).payment_succeeded(result.order_ref, str(result.payment_id))
    confirmed = await reservations.search_reservations().one(held.id)
    assert confirmed is not None and confirmed.status is ReservationStatus.CONFIRMED and not confirmed.confirmed_late


async def test_a_payment_recorded_after_its_karts_were_sold_is_cancelled_for_a_refund_never_overbooked(
    reservations: ApplicationContainer, clock: FixedClock, gateway: ScriptedPaymentGateway
) -> None:
    customer = uuid.uuid4()
    held = await reservations.hold_reservation().execute(hold(customer, 6))
    started = await pay(reservations, held.id, customer)
    clock.advance(minutes=19)
    result = await come_back(reservations, gateway, started)  # accepted: the karts are kept 10 more minutes
    clock.advance(minutes=11)  # ...but the confirmation never came in time (worker down)
    await reservations.hold_reservation().execute(hold(uuid.uuid4(), 6))  # someone else bought the session
    status = await ReservationPaymentEvents(reservations).payment_succeeded(result.order_ref, str(result.payment_id))
    assert status is ReservationStatus.CANCELLED
    refused = await reservations.search_reservations().one(held.id)
    assert refused is not None and "برگردانده" in refused.cancel_reason and refused.payment_ref
    day = await reservations.day_availability().execute(SUNDAY)
    assert next(s for s in day.sessions if s.session_time == SIX_PM).singles_left == 0  # 6 sold once, not 12


async def test_an_unpaid_hold_frees_its_karts_when_it_runs_out(
    reservations: ApplicationContainer, clock: FixedClock
) -> None:
    held = await reservations.hold_reservation().execute(hold(uuid.uuid4(), 6))
    with pytest.raises(SessionFullError):
        await reservations.hold_reservation().execute(hold(uuid.uuid4(), 1))
    clock.advance(minutes=21)
    await reservations.hold_reservation().execute(hold(uuid.uuid4(), 1))  # free again
    assert await reservations.expire_reservation_holds().execute() == 1
    assert (await reservations.search_reservations().one(held.id)).status is ReservationStatus.EXPIRED  # type: ignore[union-attr]


async def test_a_late_payment_is_kept_when_the_karts_are_still_free(
    reservations: ApplicationContainer, clock: FixedClock, gateway: ScriptedPaymentGateway
) -> None:
    customer = uuid.uuid4()
    held = await reservations.hold_reservation().execute(hold(customer, 2))
    started = await pay(reservations, held.id, customer)
    clock.advance(minutes=25)  # the hold ran out while the customer was on the bank page
    await reservations.expire_reservation_holds().execute()
    result = await come_back(reservations, gateway, started)
    assert result.status is PaymentStatus.PAID
    await ReservationPaymentEvents(reservations).payment_succeeded(result.order_ref, str(result.payment_id))
    confirmed = await reservations.search_reservations().one(held.id)
    assert confirmed is not None and confirmed.status is ReservationStatus.CONFIRMED and confirmed.confirmed_late


async def test_a_late_payment_for_karts_sold_meanwhile_is_given_back(
    reservations: ApplicationContainer, clock: FixedClock, gateway: ScriptedPaymentGateway
) -> None:
    customer = uuid.uuid4()
    held = await reservations.hold_reservation().execute(hold(customer, 6))
    started = await pay(reservations, held.id, customer)
    clock.advance(minutes=25)
    await reservations.hold_reservation().execute(hold(uuid.uuid4(), 6))  # someone else took the session
    result = await come_back(reservations, gateway, started)
    assert result.status is PaymentStatus.REVERSED and len(gateway.reversals) == 1 and gateway.settlements == []
    assert (await reservations.search_reservations().one(held.id)).status is ReservationStatus.HELD  # type: ignore[union-attr]


async def test_counter_sales_entered_by_staff_block_the_website(reservations: ApplicationContainer) -> None:
    await reservations.create_staff_reservation().execute(
        StaffReservationCommand(
            day=SUNDAY,
            session_time=SIX_PM,
            single_count=5,
            double_count=1,
            contact_name="حضوری",
            contact_mobile="",
            note="",
            amount_irr=0,
        )
    )
    with pytest.raises(SessionFullError):
        await reservations.hold_reservation().execute(hold(uuid.uuid4(), 2))
    await reservations.hold_reservation().execute(hold(uuid.uuid4(), 1))


async def test_customers_see_and_cancel_only_their_own_reservations(
    site: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    first = await sign_in(site, sms_gateway, "09121111111")
    mine = await site.post(
        "/api/v1/reservations",
        json={"date": "2026-01-04", "time": "19:00", "single_count": 1, "double_count": 0},
        headers=first.headers,
    )
    reservation_id = mine.json()["id"]
    site.cookies.clear()
    other = await sign_in(site, sms_gateway, "09122222222")
    assert (await site.get(f"/api/v1/account/reservations/{reservation_id}")).status_code == 404
    assert (await site.delete(f"/api/v1/reservations/{reservation_id}", headers=other.headers)).status_code == 404
    assert (await site.post(f"/api/v1/reservations/{reservation_id}/pay", headers=other.headers)).status_code == 404
    site.cookies.clear()
    site.cookies.set("davos_session", first.cookie)
    assert (await site.delete(f"/api/v1/reservations/{reservation_id}", headers=first.headers)).status_code == 204
    assert (await site.get("/api/v1/account/reservations")).json()[0]["status"] == "cancelled"


async def test_booking_a_closed_day_or_a_bad_time_is_refused(
    site: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    customer = await sign_in(site, sms_gateway)
    for day, at in (("2026-01-08", "18:00"), ("2026-01-03", "18:00"), ("2026-01-04", "18:07")):
        response = await site.post(
            "/api/v1/reservations",
            json={"date": day, "time": at, "single_count": 1, "double_count": 0},
            headers=customer.headers,
        )
        assert response.status_code == 422 and response.json()["code"] == "session_not_bookable"


async def pay(container: ApplicationContainer, reservation_id: uuid.UUID, customer: uuid.UUID):
    from davos.composition.adapters.reservation_order_quote_port import ReservationOrderQuotePort
    from davos.modules.payments.application.use_cases.start_payment_command import StartPaymentCommand

    return await container.start_payment().execute(
        StartPaymentCommand(ReservationOrderQuotePort.order_ref_for(reservation_id), customer)
    )


async def come_back(container: ApplicationContainer, gateway: ScriptedPaymentGateway, started):
    return await container.handle_payment_callback().execute(
        PaymentCallbackCommand(
            authority=gateway.authority,
            succeeded=True,
            gateway_order_id=gateway.requests[-1].gateway_order_id,
            provider_reference="445566",
        )
    )
