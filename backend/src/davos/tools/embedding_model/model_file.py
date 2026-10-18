from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelFile:
    """One file of the answer cache's embedding model, pinned so the bytes never change under us."""

    repository: str
    revision: str  # a commit
    path: str  # inside the repository
    name: str  # file name on disk
    sha256: str  # recorded at the first download, 2026-09-30
