from __future__ import annotations

from davos.modules.assistant.domain.services.party_facts_extractor import PartyFactsExtractor
from davos.modules.assistant.domain.services.sensitive_text_detector import SensitiveTextDetector
from davos.modules.assistant.domain.value_objects.resolved_query import ResolvedQuery


class CacheableQuestionDetector:
    """Says whether a question may be answered from, or added to, the answer cache.

    Only general questions ("what are your prices?", "how do I book?"): the answer must not depend on who is asking.
    Never cached, whatever the wording: a question that gives an age, a height, a weekday, an hour, a weight, a group
    size or "today" (the answer depends on those, and they are exactly what an embedding model ignores), a follow-up or
    a fragment that only makes sense after an earlier message, and anything that looks like personal data.
    """

    def __init__(
        self, extractor: PartyFactsExtractor | None = None, sensitive: SensitiveTextDetector | None = None
    ) -> None:
        self._extractor = extractor or PartyFactsExtractor()
        self._sensitive = sensitive or SensitiveTextDetector()

    def allows(self, query: ResolvedQuery) -> bool:
        if query.is_follow_up or query.needs_context:
            return False
        if self._sensitive.contains_sensitive(query.original) or self._sensitive.contains_sensitive(query.text):
            return False
        facts = self._extractor.extract(query.text)
        return not (
            facts.ages
            or facts.height_cm
            or facts.weekday is not None
            or facts.at
            or facts.weights_kg
            or facts.group_size
            or facts.mentions_today
        )
