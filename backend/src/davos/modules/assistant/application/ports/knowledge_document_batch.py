from dataclasses import dataclass

from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem
from davos.modules.assistant.domain.value_objects.knowledge_document import KnowledgeDocument


@dataclass(frozen=True)
class KnowledgeDocumentBatch:
    documents: tuple[KnowledgeDocument, ...]
    problems: tuple[KnowledgeDocumentProblem, ...]
