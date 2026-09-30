import logging

import pytest
from celery.signals import setup_logging

from davos.platform.observability.sensitive_data_filter import SensitiveDataFilter
from davos.worker.celery_app_factory import CeleryAppFactory
from davos.worker.celery_outbox_dispatcher import CeleryOutboxDispatcher
from davos.worker.dispatcher_queues import DispatcherQueues
from tests.fakes.standard_config import example_environment, example_settings
from tests.support.logging_state import preserved_logging_state


def make_app():
    return CeleryAppFactory.create(example_settings())


def test_sms_ai_export_and_critical_work_use_separate_queues() -> None:
    names = {q.name for q in make_app().conf.task_queues}
    assert names == {"critical", "sms", "ai", "export"} == set(DispatcherQueues.ALL)


def test_tasks_are_acknowledged_late_so_a_crash_never_loses_work() -> None:
    conf = make_app().conf
    assert conf.task_acks_late is True and conf.task_reject_on_worker_lost is True
    assert conf.worker_prefetch_multiplier == 1
    assert conf.task_time_limit > conf.task_soft_time_limit


def test_the_single_scheduler_owns_exactly_the_periodic_jobs() -> None:
    schedule = make_app().conf.beat_schedule
    assert {entry["task"] for entry in schedule.values()} == {
        "davos.outbox.relay",
        "davos.assistant.purge_interactions",
        "davos.payments.reconcile",
        "davos.reservations.expire_holds",
        "davos.notifications.refresh_sms_statuses",
    }


def test_open_payments_are_reconciled_every_two_minutes() -> None:
    schedule = make_app().conf.beat_schedule
    assert schedule["reconcile-payments"]["schedule"] <= 120


def test_events_are_routed_to_the_queue_of_their_concern() -> None:
    dispatcher = CeleryOutboxDispatcher(make_app())
    assert dispatcher.queue_for("notifications.SmsRequested") == "sms"
    assert dispatcher.queue_for("assistant.AnswerRecorded") == "ai"
    assert dispatcher.queue_for("identity.UserRegistered") == "critical"


def test_worker_logging_uses_the_masking_handler_instead_of_celerys_own() -> None:
    make_app()
    assert setup_logging.has_listeners(), "without a listener Celery installs its own unmasked log handler"
    with preserved_logging_state():
        setup_logging.send(sender=None)
        handlers = logging.getLogger().handlers
        assert len(handlers) == 1
        assert any(isinstance(f, SensitiveDataFilter) for f in handlers[0].filters)


def test_task_modules_import_without_touching_the_network(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in example_environment().items():  # the worker reads its settings on import, as in a container
        monkeypatch.setenv(name, value)
    import davos.worker.tasks as tasks

    assert tasks.handle_event.max_retries == 5
    assert tasks.handle_event.retry_backoff is True and tasks.handle_event.retry_jitter is True
