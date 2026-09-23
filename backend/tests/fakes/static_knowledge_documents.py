from __future__ import annotations

from davos.modules.assistant.application.ports.knowledge_document_batch import KnowledgeDocumentBatch
from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem
from davos.modules.assistant.application.ports.knowledge_document_source_port import KnowledgeDocumentSourcePort
from davos.modules.assistant.application.ports.knowledge_source_unavailable_error import KnowledgeSourceUnavailableError
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.knowledge_document import KnowledgeDocument


def document(
    ref: str = "booking",
    title: str = "رزرو نوبت",
    url: str = "/faq",
    body: str = "متن نمونه.",
    published: bool = True,
    source_type: KnowledgeSourceType = KnowledgeSourceType.FAQ,
) -> KnowledgeDocument:
    return KnowledgeDocument(ref, source_type, title, url, body, published)


class StaticKnowledgeDocuments(KnowledgeDocumentSourcePort):
    def __init__(
        self,
        documents: list[KnowledgeDocument] | None = None,
        problems: list[KnowledgeDocumentProblem] | None = None,
        *,
        unavailable: bool = False,
    ) -> None:
        self.documents = documents or []
        self.problems = problems or []
        self.unavailable = unavailable

    def read_all(self) -> KnowledgeDocumentBatch:
        if self.unavailable:
            raise KnowledgeSourceUnavailableError("folder is not mounted")
        return KnowledgeDocumentBatch(tuple(self.documents), tuple(self.problems))
