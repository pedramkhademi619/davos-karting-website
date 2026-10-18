from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from davos.composition.status.background_jobs_probe import SCHEDULED_JOBS, BackgroundJobsProbe
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.sms_probe import SmsProbe
from davos.composition.status.status_level import StatusLevel
from davos.composition.status.system_status_service import SystemStatusService
from davos.modules.notifications.application.ports.sms_account_info import SmsAccountInfo
from davos.worker.celery_app_factory import CeleryAppFactory
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.standard_config import example_settings

NOW = datetime(2026, 1, 3, 12, 0, tzinfo=UTC)


class FakeRedis:
    def __init__(self, runs: dict[str, float]) -> None:
        self._runs = {k: str(v) for k, v in runs.items()}

    async def hgetall(self, _key: str) -> dict[str, str]:
        return self._runs


class StubProbe(ServiceProbe):
    group = "g"

    def __init__(self, key: str, behaviour: Any, cache_seconds: float = 0.0) -> None:
        self.key = key
        self.label = key
        self._behaviour = behaviour
        self.cache_seconds = cache_seconds
        self.calls = 0

    async def check(self) -> ProbeResult:
        self.calls += 1
        if isinstance(self._behaviour, BaseException):
            raise self._behaviour
        if callable(self._behaviour):
            return await self._behaviour()
        return ProbeResult(self._behaviour, "x")


def service(*probes: ServiceProbe) -> SystemStatusService:
    return SystemStatusService(probes, FixedClock(NOW))


async def test_one_broken_probe_is_reported_down_and_never_breaks_the_page() -> None:
    report = await service(StubProbe("a", StatusLevel.OK), StubProbe("b", RuntimeError("boom"))).report()
    levels = {s.key: s.level for s in report.services}
    assert levels == {"a": StatusLevel.OK, "b": StatusLevel.DOWN}
    assert report.overall is StatusLevel.DOWN


async def test_a_probe_that_hangs_is_reported_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("davos.composition.status.system_status_service._PROBE_TIMEOUT_SECONDS", 0.05)

    async def hang() -> ProbeResult:
        await asyncio.sleep(5)
        return ProbeResult(StatusLevel.OK, "never")

    report = await service(StubProbe("slow", hang)).report()
    assert report.services[0].level is StatusLevel.DOWN


async def test_overall_ignores_disabled_and_test_services_but_not_degraded_ones() -> None:
    ok = await service(
        StubProbe("a", StatusLevel.OK), StubProbe("b", StatusLevel.DISABLED), StubProbe("c", StatusLevel.TEST)
    ).report()
    assert ok.overall is StatusLevel.OK
    degraded = await service(StubProbe("a", StatusLevel.OK), StubProbe("b", StatusLevel.DEGRADED)).report()
    assert degraded.overall is StatusLevel.DEGRADED


async def test_calls_to_third_parties_are_cached_but_local_checks_are_not() -> None:
    external = StubProbe("sms", StatusLevel.OK, cache_seconds=60)
    local = StubProbe("db", StatusLevel.OK)
    both = service(external, local)
    await both.report()
    await both.report()
    assert (external.calls, local.calls) == (1, 2)


async def test_stale_critical_job_means_down_and_a_slow_minor_one_only_degraded() -> None:
    now = NOW.timestamp()
    fresh = {job.task: now - 2 for job in SCHEDULED_JOBS}
    probe = lambda runs: BackgroundJobsProbe(FakeRedis(runs), FixedClock(NOW))  # type: ignore[arg-type]  # noqa: E731
    assert (await probe(fresh).check()).level is StatusLevel.OK
    relay_stopped = {**fresh, "davos.outbox.relay": now - 120}
    assert (await probe(relay_stopped).check()).level is StatusLevel.DOWN
    holds_late = {**fresh, "davos.reservations.expire_holds": now - 600}
    assert (await probe(holds_late).check()).level is StatusLevel.DEGRADED
    nothing_yet = (await probe({}).check()).level
    assert nothing_yet is StatusLevel.DOWN  # the relay has never reported: the worker is not running


def test_every_scheduled_celery_job_is_watched_by_the_status_page() -> None:
    scheduled = {entry["task"] for entry in CeleryAppFactory.create(example_settings()).conf.beat_schedule.values()}
    assert scheduled == {job.task for job in SCHEDULED_JOBS}


async def test_sms_probe_reports_credit_and_test_mode() -> None:
    async def low() -> SmsAccountInfo:
        return SmsAccountInfo(remaining_credit_irr=100_000, expires_at=None, account_type="x")

    async def none() -> None:
        return None

    base = {"provider": "kavenegar"}
    assert (await SmsProbe(**base, is_test_gateway=True, account=none).check()).level is StatusLevel.TEST
    assert (await SmsProbe(**base, is_test_gateway=False, account=none).check()).level is StatusLevel.DOWN
    assert (await SmsProbe(**base, is_test_gateway=False, account=low).check()).level is StatusLevel.DEGRADED
