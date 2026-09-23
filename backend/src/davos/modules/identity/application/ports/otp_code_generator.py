from abc import ABC, abstractmethod


class OtpCodeGenerator(ABC):
    @abstractmethod
    def generate(self, length: int) -> str:
        """Return a cryptographically random numeric code with leading zeros preserved."""
