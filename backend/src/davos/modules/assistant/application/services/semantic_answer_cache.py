from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import timedelta

from davos.modules.assistant.application.ports.assistant_persona_port import AssistantPersonaPort
from davos.modules.assistant.application.ports.background_runner_port import BackgroundRunnerPort
from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.application.ports.knowledge_digest_port import KnowledgeDigestPort
from davos.modules.assistant.application.ports.semantic_cache_port import SemanticCachePort
from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.modules.assistant.domain.services.cache_hit_selector import CacheHitSelector
from davos.modules.assistant.domain.services.language_detector import LanguageDetector
from davos.modules.assistant.domain.services.query_signature_builder import QuerySignatureBuilder
from davos.modules.assistant.domain.services.sensitive_text_detector import SensitiveTextDetector
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.cache_probe import CacheProbe
from davos.modules.assistant.domain.value_objects.cached_answer import CachedAnswer
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.resolved_query import ResolvedQuery
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.modules.assistant.domain.value_objects.semantic_cache_policy import SemanticCachePolicy
from davos.shared_kernel.application.clock import Clock

logger = logging.getLogger(__name__)


class SemanticAnswerCache:
    """Reuses a model answer for a question that means the same thing as one answered before.

    Three steps, so the embedding is computed once per question: ``probe`` (embed, sign, fingerprint), ``lookup``
    (ask the vector store) and, after a model answer, ``schedule_store``. It never raises into the caller: whatever
    goes wrong (model not loaded, database error) the question simply continues to the model, as if there were no
    cache.

    A stored answer is served only when all of these hold: the embedding similarity reaches the threshold, the question
    has the same numbers and discriminator words as the stored one, the entry was made under the same knowledge, style
    notes, fixed rules and model, it is active, and it is not older than ``max_age_days``.

    TODO: Admin Panel Review System. Entries carry ``is_active`` and ``is_flagged_for_review``; a customer's "not
    helpful" already flags and deactivates the entry (see ``SubmitFeedbackUseCase``). The admin panel (SQLAdmin or
    custom endpoints) should list flagged and most-used entries, let a person edit the response, approve it (clear
    the flag), or deprecate it (``is_active = False``), and show the hit ratio from
    ``assistant_interactions.served_from_cache``.
    """

    def __init__(
        self,
        *,
        embedding: EmbeddingPort,
        cache: SemanticCachePort,
        digest: KnowledgeDigestPort,
        fingerprint: AnswerFingerprint,
        policy: SemanticCachePolicy,
        clock: Clock,
        background: BackgroundRunnerPort,
        persona: AssistantPersonaPort | None = None,
        normalizer: PersianTextNormalizer | None = None,
    ) -> None:
        self._embedding = embedding
        self._cache = cache
        self._digest = digest
        self._fingerprint = fingerprint
        self._policy = policy
        self._clock = clock
        self._background = background
        self._persona = persona
        self._normalizer = normalizer or PersianTextNormalizer()
        self._signatures = QuerySignatureBuilder(self._normalizer, policy.extra_discriminator_words)
        self._sensitive = SensitiveTextDetector()
        self._languages = LanguageDetector()
        self._selector = CacheHitSelector()

    async def probe(self, query: ResolvedQuery) -> CacheProbe | None:
        """Embeds and signs the question; None when the cache must stay out of it (personal data, model unavailable)."""
        # A fragment that only makes sense after an earlier question, with no earlier question to lean on ("و برای
        # روز تعطیل؟" as the first message): the model can only guess what it is about, and a cached guess would be
        # served to everybody who types the same words. The question is simply answered, never cached.
        if query.needs_context and not query.is_follow_up:
            return None
        # The resolved text includes the previous question of a follow-up, which may hold personal data the customer
        # typed one message earlier ("my number is 09..."), so the check covers all of it, not just the last message.
        if self._sensitive.contains_sensitive(query.text) or self._sensitive.contains_sensitive(query.original):
            return None
        text = self._normalizer.normalize(query.text)[-self._policy.max_embedding_text_chars :]
        if not text:
            return None
        try:
            embedding = await self._embedding.embed_query(text)
            digest = await self._digest.current()
        except EmbeddingUnavailableError:
            logger.info("semantic cache skipped: the embedding model is not ready")
            return None
        except Exception as exc:
            logger.warning("semantic cache skipped: %s", type(exc).__name__)
            return None
        persona = self._persona.text() if self._persona is not None else ""
        fingerprint = self._fingerprint.compute(knowledge_digest=digest, persona=persona)
        return CacheProbe(
            text=text, embedding=embedding, signature=self._signatures.build(text), fingerprint=fingerprint
        )

    async def lookup(self, probe: CacheProbe) -> CachedAnswer | None:
        now = self._clock.now()
        try:
            candidates = await self._cache.find_candidates(
                probe.embedding,
                fingerprint=probe.fingerprint,
                not_before=now - timedelta(days=self._policy.max_age_days),
                limit=self._policy.candidate_limit,
            )
        except Exception as exc:
            logger.warning("semantic cache lookup failed: %s", type(exc).__name__)
            return None
        hit = self._selector.select(candidates, signature=probe.signature, threshold=self._policy.similarity_threshold)
        if hit is None:
            return None
        self._background.run(self._cache.record_hit(hit.entry_id, now), name="semantic-cache-record-hit")
        return CachedAnswer(entry_id=hit.entry_id, text=hit.response, sources=hit.sources, similarity=hit.similarity)

    def schedule_store(
        self, probe: CacheProbe, *, query: ResolvedQuery, answer: str, cited: Sequence[RetrievedPassage]
    ) -> uuid.UUID | None:
        """Caches a grounded model answer in the background; returns the entry id (None when it is not cacheable)."""
        if len(answer.strip()) < self._policy.min_answer_chars or not cited:
            return None
        if any(passage.source_type in self._policy.excluded_source_types for passage in cited):
            return None
        entry = NewCacheEntry(
            entry_id=uuid.uuid4(),
            original_query=query.original,
            resolved_query=probe.text,
            signature=probe.signature,
            embedding=probe.embedding,
            fingerprint=probe.fingerprint,
            response=answer,
            sources=tuple(AnswerSource(title=p.title, url=p.url) for p in cited),
            language=self._languages.detect(query.original),
            created_at=self._clock.now(),
        )
        self._background.run(self._store(entry), name="semantic-cache-store")
        return entry.entry_id

    async def flag_for_review(self, entry_id: uuid.UUID) -> None:
        """A customer said the answer was not helpful: stop serving it until a person has looked at it."""
        try:
            await self._cache.flag_for_review(entry_id, deactivate=True)
        except Exception as exc:
            logger.warning("semantic cache entry could not be flagged: %s", type(exc).__name__)

    async def _store(self, entry: NewCacheEntry) -> None:
        try:
            await self._cache.store(entry)
        except Exception as exc:
            logger.warning("semantic cache entry could not be stored: %s", type(exc).__name__)
