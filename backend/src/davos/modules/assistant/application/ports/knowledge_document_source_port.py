from abc import ABC, abstractmethod

from davos.modules.assistant.application.ports.knowledge_document_batch import KnowledgeDocumentBatch


class KnowledgeDocumentSourcePort(ABC):
    @abstractmethod
    def read_all(self) -> KnowledgeDocumentBatch:
        """Every document the source currently holds, plus the ones that could not be read.

        Raises ``KnowledgeSourceUnavailableError`` when the source itself is unreachable, so a broken mount is never
        mistaken for "the owner deleted everything".
        """
