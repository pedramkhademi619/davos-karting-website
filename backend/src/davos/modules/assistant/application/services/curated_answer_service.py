from __future__ import annotations

import uuid

from davos.modules.assistant.application.ports.answer_cache_port import AnswerCachePort
from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.domain.services.cacheable_question_detector import CacheableQuestionDetector
from davos.modules.assistant.domain.services.query_signature_builder import QuerySignatureBuilder
from davos.modules.assistant.domain.value_objects.answer_cache_policy import AnswerCachePolicy
from davos.modules.assistant.domain.value_objects.curated_answer import CURATED_FINGERPRINT
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.resolved_query import ResolvedQuery
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError
from davos.shared_kernel.domain.errors.validation_error import ValidationError

MAX_ANSWER_CHARS = 2000


class CuratedAnswerService:
    """Answers the owner writes or corrects in the staff panel, served for questions with the same meaning.

    The same safeguards as for a model answer apply when a question is matched (general question, same numbers and
    discriminator words, near-identical or confirmed by the model), but the entry is not tied to the knowledge texts:
    it stays until the owner changes or deletes it. Editing a stored model answer turns it into the owner's answer.
    """

    def __init__(
        self,
        *,
        embedding: EmbeddingPort,
        cache: AnswerCachePort,
        policy: AnswerCachePolicy,
        clock: Clock,
        normalizer: PersianTextNormalizer | None = None,
    ) -> None:
        self._embedding = embedding
        self._cache = cache
        self._policy = policy
        self._clock = clock
        self._normalizer = normalizer or PersianTextNormalizer()
        self._cacheable = CacheableQuestionDetector()
        self._signatures = QuerySignatureBuilder(self._normalizer)

    async def add(self, *, question: str, answer: str) -> uuid.UUID:
        entry = await self._entry(uuid.uuid4(), question, answer)
        await self._cache.store(entry)
        return entry.entry_id

    async def edit(self, entry_id: uuid.UUID, *, question: str, answer: str) -> None:
        if not await self._cache.rewrite(await self._entry(entry_id, question, answer)):
            raise NotFoundError("پاسخ ذخیره‌شده یافت نشد.")

    async def _entry(self, entry_id: uuid.UUID, question: str, answer: str) -> NewCacheEntry:
        question, answer = question.strip(), answer.strip()
        if not question or not answer:
            raise ValidationError("پرسش و پاسخ هر دو الزامی است.")
        if len(answer) > MAX_ANSWER_CHARS:
            raise ValidationError("پاسخ بیش از حد طولانی است.")
        if not self._cacheable.allows(ResolvedQuery(original=question, text=question, is_follow_up=False)):
            raise ValidationError(
                "این پرسش به سن، قد، روز، ساعت، وزن، تعداد نفرات یا اطلاعات شخصی بستگی دارد و هیچ‌وقت از پاسخ ذخیره‌شده "
                "جواب نمی‌گیرد؛ یک پرسش عمومی بنویسید."
            )
        text = self._normalizer.normalize(question)[-self._policy.max_text_chars :]
        try:
            embedding = await self._embedding.embed_query(text)
        except EmbeddingUnavailableError as exc:
            raise ValidationError("مدل معنایی هنوز آماده نیست؛ چند لحظه بعد دوباره امتحان کنید.") from exc
        return NewCacheEntry(
            entry_id=entry_id,
            original_query=question,
            resolved_query=text,
            signature=self._signatures.build(text),
            embedding=embedding,
            embedding_model=self._embedding.model_name,
            fingerprint=CURATED_FINGERPRINT,
            response=answer,
            sources=(),
            created_at=self._clock.now(),
        )
