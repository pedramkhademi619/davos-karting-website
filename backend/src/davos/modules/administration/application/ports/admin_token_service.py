from abc import ABC, abstractmethod


class AdminTokenService(ABC):
    @abstractmethod
    def new_token(self) -> str:
        """A 256-bit random session token (only its digest is stored)."""

    @abstractmethod
    def digest(self, raw: str) -> str: ...
