from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

from davos.modules.assistant.application.ports.answer_cache_port import AnswerCachePort
from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.modules.assistant.domain.services.cache_hit_selector import CacheHitSelector
from davos.modules.assistant.domain.services.cacheable_question_detector import CacheableQuestionDetector
from davos.modules.assistant.domain.services.query_signature_builder import QuerySignatureBuilder
from davos.modules.assistant.domain.value_objects.answer_cache_policy import AnswerCachePolicy
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.cache_probe import CacheProbe
from davos.modules.assistant.domain.value_objects.cached_answer import CachedAnswer
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.resolved_query import ResolvedQuery
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.shared_kernel.application.clock import Clock

logger = logging.getLogger(__name__)


class SemanticAnswerCache:
    """Reuses a model's answer for a question that means the same thing as one answered before, however it is worded.

    ``probe`` (is the question cacheable? embed it, sign it, fingerprint the inputs), ``lookup`` (ask the store) and,
    after a model answer, ``store``. It never raises into the caller: whatever goes wrong (model not loaded, database
    error) the question simply goes on to the language model, as if there were no cache.

    A stored answer is served only when all of these hold: the question is a general one (CacheableQuestionDetector),
    the embedding similarity reaches the threshold, both questions have the same signature (same numbers and
    discriminator words), the answer was written from the same texts, style notes, rules and models (fingerprint) by
    the same embedding model, and nobody has retired it. Answers that cite the riding rules are never stored.
    """

    def __init__(
        self,
        *,
        embedding: EmbeddingPort,
        cache: AnswerCachePort,
        fingerprint: AnswerFingerprint,
        policy: AnswerCachePolicy,
        clock: Clock,
        normalizer: PersianTextNormalizer | None = None,
    ) -> None:
        self._embedding = embedding
        self._cache = cache
        self._fingerprint = fingerprint
        self._policy = policy
        self._clock = clock
        self._normalizer = normalizer or PersianTextNormalizer()
        self._cacheable = CacheableQuestionDetector()
        self._signatures = QuerySignatureBuilder(self._normalizer)
        self._selector = CacheHitSelector()

    async def probe(
        self, query: ResolvedQuery, passages: Sequence[RetrievedPassage], persona: str
    ) -> CacheProbe | None:
        """None when the cache must stay out of this question (not a general one, personal data, model not ready)."""
        if not self._cacheable.allows(query):
            return None
        text = self._normalizer.normalize(query.text)[-self._policy.max_text_chars :]
        if not text:
            return None
        try:
            embedding = await self._embedding.embed_query(text)
        except EmbeddingUnavailableError:
            logger.info("answer cache skipped: the embedding model is not ready")
            return None
        except Exception as exc:
            logger.warning("answer cache skipped: %s", type(exc).__name__)
            return None
        return CacheProbe(
            text=text,
            embedding=embedding,
            signature=self._signatures.build(text),
            fingerprint=self._fingerprint.compute(passages=passages, persona=persona),
        )

    async def lookup(self, probe: CacheProbe) -> CachedAnswer | None:
        try:
            candidates = await self._cache.find_candidates(
                probe.embedding,
                embedding_model=self._embedding.model_name,
                fingerprint=probe.fingerprint,
                limit=self._policy.candidate_limit,
            )
        except Exception as exc:
            logger.warning("answer cache lookup failed: %s", type(exc).__name__)
            return None
        hit = self._selector.select(candidates, signature=probe.signature, threshold=self._policy.similarity_threshold)
        if hit is None:
            return None
        try:
            await self._cache.record_hit(hit.entry_id, self._clock.now())
        except Exception as exc:  # the count is a statistic: the customer still gets the answer
            logger.warning("answer cache hit not recorded: %s", type(exc).__name__)
        return CachedAnswer(entry_id=hit.entry_id, text=hit.response, sources=hit.sources, similarity=hit.similarity)

    async def store(
        self, probe: CacheProbe, *, query: ResolvedQuery, answer: str, cited: Sequence[RetrievedPassage]
    ) -> uuid.UUID | None:
        """Keeps a grounded model answer for the next customer; the entry id, or None when it is not cacheable."""
        if not answer.strip() or not cited:
            return None
        if any(passage.source_type in self._policy.excluded_source_types for passage in cited):
            return None
        entry = NewCacheEntry(
            entry_id=uuid.uuid4(),
            original_query=query.original,
            resolved_query=probe.text,
            signature=probe.signature,
            embedding=probe.embedding,
            embedding_model=self._embedding.model_name,
            fingerprint=probe.fingerprint,
            response=answer,
            sources=tuple(AnswerSource(title=p.title, url=p.url) for p in cited if not p.computed),
            created_at=self._clock.now(),
        )
        try:
            await self._cache.store(entry)
        except Exception as exc:
            logger.warning("answer cache entry could not be stored: %s", type(exc).__name__)
            return None
        return entry.entry_id

    async def deactivate(self, entry_id: uuid.UUID) -> None:
        """A customer found the answer not helpful: stop serving it until a person has looked at it."""
        try:
            await self._cache.deactivate(entry_id)
        except Exception as exc:
            logger.warning("answer cache entry could not be retired: %s", type(exc).__name__)
