from dataclasses import dataclass

from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem


@dataclass(frozen=True)
class KnowledgeSeedReport:
    imported: int
    drafts: int
    skipped_because_not_empty: bool
    problems: tuple[KnowledgeDocumentProblem, ...]
