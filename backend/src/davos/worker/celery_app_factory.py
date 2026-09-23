from __future__ import annotations

from celery import Celery
from celery.signals import setup_logging
from kombu import Exchange, Queue

from davos.platform.observability.logging_configurator import LoggingConfigurator
from davos.platform.settings.app_settings import AppSettings
from davos.worker.dispatcher_queues import DispatcherQueues


class CeleryAppFactory:
    @staticmethod
    def create(settings: AppSettings) -> Celery:
        app = Celery("davos", broker=settings.redis_url, include=["davos.worker.tasks"])
        app.conf.update(
            task_default_queue=DispatcherQueues.CRITICAL,
            task_queues=[Queue(q, Exchange(q), routing_key=q) for q in DispatcherQueues.ALL],
            task_routes={
                "davos.events.handle": {"queue": DispatcherQueues.CRITICAL},
                "davos.outbox.relay": {"queue": DispatcherQueues.CRITICAL},
                "davos.assistant.purge_interactions": {"queue": DispatcherQueues.AI},
            },
            # A task is acknowledged only after it finishes, so a crashed worker never loses work.
            task_acks_late=True,
            task_reject_on_worker_lost=True,
            worker_prefetch_multiplier=1,
            task_time_limit=120,
            task_soft_time_limit=100,
            broker_connection_retry_on_startup=True,
            worker_hijack_root_logger=False,
            timezone="UTC",
            enable_utc=True,
            # Exactly one scheduler container runs beat; these entries are its whole job list.
            beat_schedule={
                "outbox-relay": {"task": "davos.outbox.relay", "schedule": 5.0},
                "purge-assistant-interactions": {
                    "task": "davos.assistant.purge_interactions",
                    "schedule": 24 * 3600.0,
                },
            },
        )

        def configure_logging(**_: object) -> None:
            LoggingConfigurator.install(settings.log_level)

        # With any listener connected Celery skips its own handlers, so worker and beat share the API's masking handler.
        setup_logging.connect(configure_logging, weak=False, dispatch_uid="davos.worker.logging")
        return app
