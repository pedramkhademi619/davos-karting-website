from __future__ import annotations

import hashlib

_SEPARATOR = "\x1f"
_SCHEMA_VERSION = "1"  # bump when the cache logic changes in a way that makes old entries untrustworthy


class AnswerFingerprint:
    """A cached answer is only valid for the exact inputs that produced it: fixed rules, model, style notes, knowledge.

    When the owner edits a price or the persona, the fingerprint changes and every older entry stops matching, so a
    customer can never be served an answer that was true under yesterday's text.
    """

    def __init__(self, *, rules_version: str, model: str) -> None:
        self._rules_version = rules_version
        self._model = model

    def compute(self, *, knowledge_digest: str, persona: str) -> str:
        parts = (_SCHEMA_VERSION, self._rules_version, self._model, knowledge_digest, persona)
        return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()
