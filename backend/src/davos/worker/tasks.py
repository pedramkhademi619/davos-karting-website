"""Celery task entry points. Tasks stay tiny: run one use case through WorkerRuntime and return."""

from __future__ import annotations

import logging
from typing import Any

from davos.composition.application_container import ApplicationContainer
from davos.composition.reservation_payment_events import ReservationPaymentEvents
from davos.platform.messaging.outbox_relay import OutboxRelay
from davos.worker.celery_app import celery_app
from davos.worker.celery_outbox_dispatcher import CeleryOutboxDispatcher
from davos.worker.worker_runtime import WorkerRuntime

logger = logging.getLogger(__name__)


@celery_app.task(name="davos.outbox.relay")
def relay_outbox() -> dict[str, int]:
    async def job(container: ApplicationContainer) -> dict[str, int]:
        relay = OutboxRelay(
            session_factory=container.session_factory,
            dispatcher=CeleryOutboxDispatcher(celery_app),
            clock=container.clock,
        )
        report = await relay.run_once()
        return {"dispatched": report.dispatched, "failed": report.failed, "dead_lettered": report.dead_lettered}

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.assistant.purge_interactions")
def purge_assistant_interactions() -> int:
    async def job(container: ApplicationContainer) -> int:
        return await container.purge_expired_interactions().execute()

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.payments.reconcile")
def reconcile_payments() -> dict[str, int]:
    """Verify, settle or reverse payments whose outcome is still open (the money must never stay in limbo)."""

    async def job(container: ApplicationContainer) -> dict[str, int]:
        report = await container.reconcile_payments().execute()
        return {
            "examined": report.examined,
            "paid": report.paid,
            "failed": report.failed,
            "still_unknown": report.still_unknown,
            "expired": report.expired,
        }

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.reservations.expire_holds")
def expire_reservation_holds() -> int:
    async def job(container: ApplicationContainer) -> int:
        return await container.expire_reservation_holds().execute()

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.notifications.refresh_sms_statuses")
def refresh_sms_statuses() -> int:
    async def job(container: ApplicationContainer) -> int:
        return await container.refresh_sms_statuses().execute()

    return WorkerRuntime.run(job)


@celery_app.task(
    name="davos.events.handle",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def handle_event(event_id: str, event_name: str, payload: dict[str, Any]) -> None:
    """Cross-module reactions: confirm a paid reservation, cancel a reversed one, text the confirmation."""
    logger.info("event received name=%s id=%s", event_name, event_id)

    async def job(container: ApplicationContainer) -> None:
        await ReservationPaymentEvents(container).handle(event_name, payload)

    WorkerRuntime.run(job)
