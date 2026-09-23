from __future__ import annotations

import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.application.ports.knowledge_digest_port import KnowledgeDigestPort

_DIGEST = text(
    """
    SELECT coalesce(
        md5(string_agg(source_type || ':' || source_ref || ':' || md5(title || chr(31) || body || chr(31) || url), ','
                       ORDER BY source_type, source_ref)),
        '')
    FROM assistant_knowledge_entries
    """
)


class PgKnowledgeDigest(KnowledgeDigestPort):
    """One hash over every published knowledge entry, remembered for a few seconds so it is not recomputed per question.

    The knowledge table only holds published entries (drafts are removed when a file becomes a draft), so any edit,
    addition or removal changes the digest and with it the fingerprint of every cached answer.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], *, ttl_seconds: float = 5.0) -> None:
        self._session_factory = session_factory
        self._ttl = ttl_seconds
        self._value = ""
        self._expires = 0.0

    async def current(self) -> str:
        now = time.monotonic()
        if now < self._expires:
            return self._value
        async with self._session_factory() as session:
            result = await session.execute(_DIGEST)
            self._value = str(result.scalar_one())
        self._expires = now + self._ttl
        return self._value
