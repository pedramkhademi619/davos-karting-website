from abc import ABC, abstractmethod

from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


class EmbeddingPort(ABC):
    """Turns a question into a unit-length vector. Implementations run on this machine: no network call is allowed."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identity stored next to every cached vector, so vectors of another model are never compared."""

    @abstractmethod
    async def warm_up(self) -> None:
        """Loads the model (once). Never raises: a model that cannot load keeps the cache off."""

    @abstractmethod
    async def embed_query(self, text: str) -> QueryEmbedding:
        """Raises ``EmbeddingUnavailableError`` when the model cannot serve the request right now."""
