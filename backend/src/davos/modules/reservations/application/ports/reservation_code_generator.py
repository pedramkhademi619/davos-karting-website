from abc import ABC, abstractmethod


class ReservationCodeGenerator(ABC):
    @abstractmethod
    def new_code(self) -> str:
        """A short, unguessable ticket code that is easy to read out at the counter (for example DK-7F3K9Q)."""
