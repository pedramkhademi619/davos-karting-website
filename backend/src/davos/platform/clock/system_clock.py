from datetime import UTC, datetime

from davos.shared_kernel.application.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
