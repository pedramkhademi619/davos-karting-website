from __future__ import annotations

import hashlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class StartupLock:
    """Lets exactly one of several API processes do the start-up work (knowledge sync, first admin account).

    The API runs several worker processes that start at the same moment; without this they would all write the same
    rows at once. It is a PostgreSQL session advisory lock taken without waiting: the process that gets it does the
    work, the others skip it (the work is idempotent, so a skipped run loses nothing).
    """

    def __init__(self, engine: AsyncEngine, name: str) -> None:
        self._engine = engine
        # Advisory locks take a 64-bit integer: derive a stable one from the name.
        self._key = int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:8], "big", signed=True)

    @asynccontextmanager
    async def acquired(self) -> AsyncIterator[bool]:
        """Yields True in the one process that holds the lock, False in the others."""
        async with self._engine.connect() as connection:
            result = await connection.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": self._key})
            got = bool(result.scalar())
            try:
                yield got
            finally:
                if got:
                    await connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": self._key})
