import pytest

from davos.platform.resilience.circuit_breaker import CircuitBreaker
from davos.platform.resilience.circuit_open_error import CircuitOpenError
from davos.platform.resilience.circuit_state import CircuitState


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


async def _fail() -> None:
    raise ValueError("down")


async def _ok() -> str:
    return "fine"


def make(threshold: int = 3, recovery: float = 30.0, **kwargs):
    clock = Clock()
    return CircuitBreaker(failure_threshold=threshold, recovery_seconds=recovery, monotonic=clock, **kwargs), clock


async def trip(breaker: CircuitBreaker, times: int) -> None:
    for _ in range(times):
        with pytest.raises(ValueError, match="down"):
            await breaker.call(_fail)


async def test_opens_after_consecutive_failures_and_then_fails_fast() -> None:
    breaker, _ = make()
    await trip(breaker, 3)
    assert breaker.state is CircuitState.OPEN
    called = False

    async def probe() -> None:
        nonlocal called
        called = True

    with pytest.raises(CircuitOpenError):
        await breaker.call(probe)
    assert not called


async def test_success_resets_the_failure_streak() -> None:
    breaker, _ = make()
    await trip(breaker, 2)
    await breaker.call(_ok)
    await trip(breaker, 2)
    assert breaker.state is CircuitState.CLOSED


async def test_half_open_probe_closes_the_circuit_on_success() -> None:
    breaker, clock = make(recovery=30)
    await trip(breaker, 3)
    clock.t = 31
    assert breaker.state is CircuitState.HALF_OPEN
    assert await breaker.call(_ok) == "fine"
    assert breaker.state is CircuitState.CLOSED


async def test_half_open_probe_failure_reopens_immediately() -> None:
    breaker, clock = make(recovery=30)
    await trip(breaker, 3)
    clock.t = 31
    await trip(breaker, 1)
    assert breaker.state is CircuitState.OPEN
    clock.t = 40  # only 9s after re-opening
    with pytest.raises(CircuitOpenError):
        await breaker.call(_ok)


async def test_only_one_probe_is_allowed_while_half_open() -> None:
    import asyncio

    breaker, clock = make(recovery=30)
    await trip(breaker, 3)
    clock.t = 31
    gate = asyncio.Event()

    async def slow_probe() -> str:
        await gate.wait()
        return "ok"

    first = asyncio.create_task(breaker.call(slow_probe))
    await asyncio.sleep(0)
    with pytest.raises(CircuitOpenError):
        await breaker.call(_ok)
    gate.set()
    assert await first == "ok"


async def test_exceptions_that_are_not_failures_do_not_open_the_circuit() -> None:
    breaker, _ = make(threshold=1, is_failure=lambda e: not isinstance(e, KeyError))

    async def raises_key_error() -> None:
        raise KeyError("client mistake")

    for _ in range(5):
        with pytest.raises(KeyError):
            await breaker.call(raises_key_error)
    assert breaker.state is CircuitState.CLOSED
