from __future__ import annotations

from typing import Generic, TypeVar

IdT = TypeVar("IdT")


class Entity(Generic[IdT]):  # noqa: UP046 - kept explicit for readability
    """Identity-based domain object. Equality is by identity, never by attributes."""

    def __init__(self, entity_id: IdT) -> None:
        self._id = entity_id

    @property
    def id(self) -> IdT:
        return self._id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Entity) and type(self) is type(other) and self._id == other._id

    def __hash__(self) -> int:
        return hash((type(self), self._id))
