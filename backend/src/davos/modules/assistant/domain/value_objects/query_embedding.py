from dataclasses import dataclass


@dataclass(frozen=True)
class QueryEmbedding:
    """A unit-length vector and the model that produced it (vectors of different models are never comparable)."""

    values: tuple[float, ...]
    model: str
