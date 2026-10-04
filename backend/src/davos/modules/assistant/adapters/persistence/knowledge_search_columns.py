from __future__ import annotations

from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer


def knowledge_search_columns(entry: KnowledgeEntry, normalizer: PersianTextNormalizer) -> dict[str, str]:
    """The two derived columns the keyword search reads: the normalised title and title plus text."""
    title_norm = normalizer.normalize(entry.title)
    return {"title_norm": title_norm, "search_text": f"{title_norm} {normalizer.normalize(entry.body)}"}
