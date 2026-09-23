from abc import ABC, abstractmethod


class OtpHasher(ABC):
    @abstractmethod
    def digest(self, mobile: str, code: str) -> str:
        """Keyed, non-reversible digest bound to the mobile number."""
