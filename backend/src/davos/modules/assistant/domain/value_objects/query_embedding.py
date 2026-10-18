from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryEmbedding:
    """A question's meaning as a unit-length vector: questions that mean the same point the same way."""

    values: tuple[float, ...]
