from __future__ import annotations

from datetime import timedelta

from davos.modules.assistant.application.ports.assistant_persona_port import AssistantPersonaPort
from davos.modules.assistant.application.ports.knowledge_digest_port import KnowledgeDigestPort
from davos.modules.assistant.application.ports.semantic_cache_port import SemanticCachePort
from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.shared_kernel.application.clock import Clock

_STALE_DAYS = 7  # an entry made under other knowledge, style notes, rules or model, and not served for this long
_UNUSED_DAYS = 90


class PurgeSemanticCacheUseCase:
    """Removes cached answers that can no longer be served: made under other knowledge, style notes, rules or model
    and not used for a week, or not used for 90 days. Entries flagged for review stay until a person decides."""

    def __init__(
        self,
        *,
        cache: SemanticCachePort,
        digest: KnowledgeDigestPort,
        fingerprint: AnswerFingerprint,
        clock: Clock,
        persona: AssistantPersonaPort | None = None,
    ) -> None:
        self._cache = cache
        self._digest = digest
        self._fingerprint = fingerprint
        self._clock = clock
        self._persona = persona

    async def execute(self) -> int:
        current = self._fingerprint.compute(
            knowledge_digest=await self._digest.current(),
            persona=self._persona.text() if self._persona is not None else "",
        )
        now = self._clock.now()
        return await self._cache.purge(
            keep_fingerprint=current,
            stale_before=now - timedelta(days=_STALE_DAYS),
            unused_before=now - timedelta(days=_UNUSED_DAYS),
        )
