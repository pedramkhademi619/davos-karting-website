from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, stored: str) -> bool:
        """Constant-time check. Unknown or malformed hashes simply fail."""

    @abstractmethod
    def dummy_verify(self, password: str) -> None:
        """Spend the same time as a real check, so an unknown username cannot be told apart by timing."""
