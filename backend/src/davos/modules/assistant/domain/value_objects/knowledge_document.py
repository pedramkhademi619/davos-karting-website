from dataclasses import dataclass

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


@dataclass(frozen=True)
class KnowledgeDocument:
    """A piece of knowledge as written by a person (for example in a text file), before it is checked and indexed.

    ``published=False`` keeps a draft on file without letting the assistant quote it.
    """

    ref: str
    source_type: KnowledgeSourceType
    title: str
    url: str
    body: str
    published: bool
