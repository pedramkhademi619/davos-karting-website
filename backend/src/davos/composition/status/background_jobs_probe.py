from __future__ import annotations

from redis.asyncio import Redis

from davos.composition.status.persian_text import duration
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.scheduled_job import ScheduledJob
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel
from davos.platform.messaging.task_heartbeat import TaskHeartbeat
from davos.shared_kernel.application.clock import Clock

SCHEDULED_JOBS = (
    ScheduledJob("davos.outbox.relay", "پخش رویدادها (پیامک و تایید رزرو)", 5, critical=True),
    ScheduledJob("davos.reservations.expire_holds", "آزادسازی رزروهای پرداخت‌نشده", 60),
    ScheduledJob("davos.payments.reconcile", "پیگیری پرداخت‌های نامشخص", 120),
    ScheduledJob("davos.notifications.refresh_sms_statuses", "به‌روزرسانی وضعیت تحویل پیامک", 300),
    ScheduledJob("davos.accounting.recognize_revenue", "شناسایی درآمد بلیت‌های سانس‌خورده (حسابداری)", 3_600),
    ScheduledJob("davos.assistant.purge_interactions", "پاک‌سازی پرسش‌های ذخیره‌شده دستیار", 86_400),
)


class BackgroundJobsProbe(ServiceProbe):
    key = "background_jobs"
    group = "زیرساخت"
    label = "کارگر و زمان‌بند پس‌زمینه (Celery)"

    def __init__(self, redis: Redis | None, clock: Clock) -> None:
        self._redis = redis
        self._clock = clock

    async def check(self) -> ProbeResult:
        if self._redis is None:
            return ProbeResult(StatusLevel.DISABLED, "بدون Redis، وضعیت کارها ثبت نمی‌شود.")
        runs = await TaskHeartbeat(self._redis).last_runs()
        now = self._clock.now().timestamp()
        parts: list[ServicePart] = []
        worst = StatusLevel.OK
        for job in SCHEDULED_JOBS:
            last = runs.get(job.task)
            stale_after = max(job.interval_seconds * 3, 30.0)
            if last is None:
                if job.interval_seconds >= 3600:
                    parts.append(ServicePart(job.label, StatusLevel.OK, "هنوز نوبت اجرایش نرسیده"))
                    continue
                level = StatusLevel.DOWN if job.critical else StatusLevel.DEGRADED
                parts.append(ServicePart(job.label, level, "هنوز اجرایی ثبت نشده"))
            elif now - last > stale_after:
                level = StatusLevel.DOWN if job.critical else StatusLevel.DEGRADED
                parts.append(
                    ServicePart(
                        job.label,
                        level,
                        f"آخرین اجرا {duration(now - last)} پیش (باید هر {duration(job.interval_seconds)} اجرا شود)",
                    )
                )
            else:
                level = StatusLevel.OK
                parts.append(ServicePart(job.label, level, f"آخرین اجرا {duration(now - last)} پیش"))
            if level is StatusLevel.DOWN or (level is StatusLevel.DEGRADED and worst is StatusLevel.OK):
                worst = level
        summary = {
            StatusLevel.OK: "کارگر و زمان‌بند کار می‌کنند.",
            StatusLevel.DEGRADED: "بعضی کارهای زمان‌بندی‌شده به‌موقع اجرا نشده‌اند.",
            StatusLevel.DOWN: "کارگر یا زمان‌بند متوقف است؛ پیامک و تایید رزرو انجام نمی‌شود.",
        }[worst]
        return ProbeResult(worst, summary, tuple(parts))
