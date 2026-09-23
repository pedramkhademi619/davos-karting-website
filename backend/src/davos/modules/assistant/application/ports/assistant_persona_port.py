from abc import ABC, abstractmethod


class AssistantPersonaPort(ABC):
    """Where the owner-written style notes of the assistant come from (a text file today, the admin panel later)."""

    @abstractmethod
    def text(self) -> str:
        """Notes about tone and phrasing, already cleaned and length-limited; empty when there are none.

        Style only: facts the assistant may rely on come from the knowledge base, never from here.
        """
