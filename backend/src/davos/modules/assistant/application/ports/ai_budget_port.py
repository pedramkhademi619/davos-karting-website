from abc import ABC, abstractmethod


class AiBudgetPort(ABC):
    """Daily token budget shared by all replicas (a runaway loop must not become a bill)."""

    @abstractmethod
    async def try_reserve(self, tokens: int) -> bool:
        """Atomically reserve tokens for one call; False when the day's budget is exhausted."""

    @abstractmethod
    async def settle(self, reserved: int, actual: int) -> None:
        """Replace the reservation with the real usage."""

    @abstractmethod
    async def release(self, reserved: int) -> None:
        """Give back a reservation for a call that produced no usage."""
