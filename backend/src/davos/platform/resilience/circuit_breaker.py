from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from davos.platform.resilience.circuit_open_error import CircuitOpenError
from davos.platform.resilience.circuit_state import CircuitState

T = TypeVar("T")


class CircuitBreaker:
    """Per-process breaker: opens after consecutive failures, probes once after a cool-down.

    Being per-process is intentional: each replica protects itself without a shared lock.
    """

    def __init__(
        self,
        *,
        failure_threshold: int,
        recovery_seconds: float,
        is_failure: Callable[[BaseException], bool] = lambda _exc: True,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._threshold = failure_threshold
        self._recovery = recovery_seconds
        self._is_failure = is_failure
        self._monotonic = monotonic
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = 0.0
        self._probe_in_flight = False

    @property
    def state(self) -> CircuitState:
        if self._state is CircuitState.OPEN and self._monotonic() - self._opened_at >= self._recovery:
            return CircuitState.HALF_OPEN
        return self._state

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        state = self.state
        if state is CircuitState.OPEN:
            raise CircuitOpenError
        if state is CircuitState.HALF_OPEN:
            if self._probe_in_flight:
                raise CircuitOpenError
            self._probe_in_flight = True
        try:
            result = await operation()
        except BaseException as exc:
            if self._is_failure(exc):
                self._record_failure()
            elif state is CircuitState.HALF_OPEN:
                self._probe_in_flight = False
            raise
        self._record_success()
        return result

    def _record_success(self) -> None:
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._probe_in_flight = False

    def _record_failure(self) -> None:
        self._probe_in_flight = False
        self._consecutive_failures += 1
        if self._state is CircuitState.OPEN or self._consecutive_failures >= self._threshold:
            self._state = CircuitState.OPEN
            self._opened_at = self._monotonic()
