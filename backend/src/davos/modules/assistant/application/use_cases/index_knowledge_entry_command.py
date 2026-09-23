from dataclasses import dataclass

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


@dataclass(frozen=True)
class IndexKnowledgeEntryCommand:
    source_type: KnowledgeSourceType
    source_ref: str
    title: str
    body: str
    url: str
    published: bool
