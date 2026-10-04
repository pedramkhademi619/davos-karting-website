from __future__ import annotations

from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem
from davos.modules.assistant.application.ports.knowledge_document_source_port import KnowledgeDocumentSourcePort
from davos.modules.assistant.application.ports.knowledge_index_port import KnowledgeIndexPort
from davos.modules.assistant.application.use_cases.knowledge_seed_report import KnowledgeSeedReport
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.errors.invalid_knowledge_entry_error import InvalidKnowledgeEntryError
from davos.shared_kernel.application.clock import Clock

# Entries imported from the documents carry this prefix (entries made in the staff panel carry "admin:").
DOCUMENT_REF_PREFIX = "file:"


class SeedKnowledgeFromDocumentsUseCase:
    """Fills an empty knowledge base from the published documents, once.

    The database is the source of truth: the owner edits it in the staff panel, so the documents must never overwrite
    or bring back what was edited or deleted there. They only start a fresh installation, which is why nothing happens
    once any entry exists. One bad document never blocks the others: it is reported with the reason instead.
    """

    def __init__(self, *, index: KnowledgeIndexPort, source: KnowledgeDocumentSourcePort, clock: Clock) -> None:
        self._index = index
        self._source = source
        self._clock = clock

    async def execute(self) -> KnowledgeSeedReport:
        if await self._index.count() > 0:
            return KnowledgeSeedReport(imported=0, drafts=0, skipped_because_not_empty=True, problems=())
        batch = self._source.read_all()
        problems = list(batch.problems)
        imported = drafts = 0
        for document in batch.documents:
            if not document.published:
                drafts += 1
                continue
            try:
                entry = KnowledgeEntry.create(
                    source_type=document.source_type,
                    source_ref=f"{DOCUMENT_REF_PREFIX}{document.ref}",
                    title=document.title,
                    body=document.body,
                    url=document.url,
                    now=self._clock.now(),
                )
            except InvalidKnowledgeEntryError as exc:
                problems.append(KnowledgeDocumentProblem(document.ref, str(exc)))
                continue
            await self._index.upsert(entry)
            imported += 1
        return KnowledgeSeedReport(
            imported=imported, drafts=drafts, skipped_because_not_empty=False, problems=tuple(problems)
        )
