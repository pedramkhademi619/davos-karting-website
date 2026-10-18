from __future__ import annotations

import hashlib
from collections.abc import Sequence

from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage

_SEPARATOR = "\x1f"
_SCHEMA_VERSION = "1"  # bump when the cache logic changes in a way that makes old entries untrustworthy


class AnswerFingerprint:
    """A stored answer is only valid for the inputs that produced it: the fixed prompt rules, the answering models, the
    owner's style notes, the embedding model, and every passage the answer was written from (the published knowledge,
    the live admin-panel prices and kart counts, the computed rule checks).

    Hashing the passages the new question would send, instead of asking the database for a digest, keeps this exact:
    when the owner edits a text or a price in the admin panel, the fingerprint changes and every older answer stops
    matching at once, so a customer is never served an answer that was true under yesterday's numbers.
    """

    def __init__(self, *, rules_version: str, answer_models: str, embedding_model: str) -> None:
        self._prefix = (_SCHEMA_VERSION, rules_version, answer_models, embedding_model)

    def compute(self, *, passages: Sequence[RetrievedPassage], persona: str) -> str:
        ordered = sorted(passages, key=lambda p: (p.title, p.text, p.url))
        parts = [*self._prefix, persona, *(f"{p.title}{_SEPARATOR}{p.text}{_SEPARATOR}{p.url}" for p in ordered)]
        return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()
