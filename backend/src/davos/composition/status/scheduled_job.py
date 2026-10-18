from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduledJob:
    task: str  # the Celery task name, as in worker/celery_app_factory.py
    label: str
    interval_seconds: float
    critical: bool = False  # the site cannot work without it (events, SMS and ticket confirmations go through it)
