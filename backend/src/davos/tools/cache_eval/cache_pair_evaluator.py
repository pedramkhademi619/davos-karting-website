from __future__ import annotations

from collections.abc import Sequence

from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.domain.services.cacheable_question_detector import CacheableQuestionDetector
from davos.modules.assistant.domain.services.query_resolver import QueryResolver
from davos.modules.assistant.domain.services.query_signature_builder import QuerySignatureBuilder
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.tools.cache_eval.cache_pair import CachePair
from davos.tools.cache_eval.cache_pair_result import CachePairResult


class CachePairEvaluator:
    """Applies the cache's own rules to each pair, with the real embedding model: is each question cacheable, do the
    two share a signature, and how similar are their meanings? The threshold is applied afterwards
    (``CachePairResult.would_hit``), so one run answers for every threshold."""

    def __init__(self, embedding: EmbeddingPort) -> None:
        self._embedding = embedding
        self._normalizer = PersianTextNormalizer()
        self._resolver = QueryResolver()
        self._cacheable = CacheableQuestionDetector()
        self._signatures = QuerySignatureBuilder(self._normalizer)

    async def evaluate(self, pairs: Sequence[CachePair]) -> list[CachePairResult]:
        await self._embedding.warm_up()
        return [await self._one(pair) for pair in pairs]

    async def _one(self, pair: CachePair) -> CachePairResult:
        first, second = self._normalizer.normalize(pair.first), self._normalizer.normalize(pair.second)
        vector_a = (await self._embedding.embed_query(first)).values
        vector_b = (await self._embedding.embed_query(second)).values
        return CachePairResult(
            pair=pair,
            similarity=sum(x * y for x, y in zip(vector_a, vector_b, strict=True)),
            cacheable_first=self._allowed(pair.first),
            cacheable_second=self._allowed(pair.second),
            same_signature=self._signatures.build(first) == self._signatures.build(second),
        )

    def _allowed(self, question: str) -> bool:
        return self._cacheable.allows(self._resolver.resolve(question, ()))
