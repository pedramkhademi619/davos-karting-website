from abc import ABC, abstractmethod


class KnowledgeDigestPort(ABC):
    @abstractmethod
    async def current(self) -> str:
        """A short string that changes whenever any published knowledge entry is added, edited or removed."""
