"""Celery task entry points. Tasks stay tiny: run one use case through WorkerRuntime and return."""

from __future__ import annotations

import logging
from typing import Any

from davos.composition.accounting_events import AccountingEvents
from davos.composition.application_container import ApplicationContainer
from davos.composition.reservation_payment_events import ReservationPaymentEvents
from davos.platform.messaging.outbox_relay import OutboxRelay
from davos.platform.messaging.task_heartbeat import TaskHeartbeat
from davos.worker.celery_app import celery_app
from davos.worker.celery_outbox_dispatcher import CeleryOutboxDispatcher
from davos.worker.worker_runtime import WorkerRuntime

logger = logging.getLogger(__name__)


async def _beat(container: ApplicationContainer, task: str) -> None:
    """Tell the admin status page this job just finished (a Redis hiccup must never fail the job)."""
    if container.redis is None:
        return
    try:
        await TaskHeartbeat(container.redis).beat(task, container.clock.now().timestamp())
    except Exception:
        logger.warning("could not record the heartbeat of %s", task)


@celery_app.task(name="davos.outbox.relay")
def relay_outbox() -> dict[str, int]:
    async def job(container: ApplicationContainer) -> dict[str, int]:
        relay = OutboxRelay(
            session_factory=container.session_factory,
            dispatcher=CeleryOutboxDispatcher(celery_app),
            clock=container.clock,
        )
        report = await relay.run_once()
        await _beat(container, "davos.outbox.relay")
        return {"dispatched": report.dispatched, "failed": report.failed, "dead_lettered": report.dead_lettered}

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.assistant.purge_interactions")
def purge_assistant_interactions() -> int:
    async def job(container: ApplicationContainer) -> int:
        purged = await container.purge_expired_interactions().execute()
        await _beat(container, "davos.assistant.purge_interactions")
        return purged

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.payments.reconcile")
def reconcile_payments() -> dict[str, int]:
    """Verify, settle or reverse payments whose outcome is still open (the money must never stay in limbo)."""

    async def job(container: ApplicationContainer) -> dict[str, int]:
        report = await container.reconcile_payments().execute()
        await _beat(container, "davos.payments.reconcile")
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
        expired = await container.expire_reservation_holds().execute()
        await _beat(container, "davos.reservations.expire_holds")
        return expired

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.notifications.refresh_sms_statuses")
def refresh_sms_statuses() -> int:
    async def job(container: ApplicationContainer) -> int:
        refreshed = await container.refresh_sms_statuses().execute()
        await _beat(container, "davos.notifications.refresh_sms_statuses")
        return refreshed

    return WorkerRuntime.run(job)


@celery_app.task(name="davos.accounting.recognize_revenue")
def recognize_ticket_revenue() -> int:
    """Moves paid-in-advance ticket money to revenue once the session day has come (accrual mode only)."""

    async def job(container: ApplicationContainer) -> int:
        done = await container.sales_posting().recognize_due()
        await _beat(container, "davos.accounting.recognize_revenue")
        return done

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
        await AccountingEvents(container).handle(event_name, payload)

    WorkerRuntime.run(job)
