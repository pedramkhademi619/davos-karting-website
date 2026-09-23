"""Sample knowledge passages for tests. The texts are placeholders, not real Davos Karting facts."""

from __future__ import annotations

import uuid

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage


def passage(
    title: str = "لغو رزرو (نمونه)",
    text: str = "متن نمونه درباره شرایط لغو رزرو.",
    url: str = "/policies/cancellation",
    score: float = 0.8,
    source_type: KnowledgeSourceType = KnowledgeSourceType.POLICY,
) -> RetrievedPassage:
    return RetrievedPassage(uuid.uuid4(), source_type, title, text, url, score)
