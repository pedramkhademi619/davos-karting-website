from dataclasses import dataclass

from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem


@dataclass(frozen=True)
class KnowledgeSyncReport:
    published: int
    drafts: int
    removed: int
    problems: tuple[KnowledgeDocumentProblem, ...]
