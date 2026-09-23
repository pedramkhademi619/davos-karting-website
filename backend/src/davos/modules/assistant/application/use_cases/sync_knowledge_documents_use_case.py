from __future__ import annotations

from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem
from davos.modules.assistant.application.ports.knowledge_document_source_port import KnowledgeDocumentSourcePort
from davos.modules.assistant.application.ports.knowledge_index_port import KnowledgeIndexPort
from davos.modules.assistant.application.use_cases.knowledge_sync_report import KnowledgeSyncReport
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.errors.invalid_knowledge_entry_error import InvalidKnowledgeEntryError
from davos.shared_kernel.application.clock import Clock

# Everything synced from documents carries this prefix, so it can be reconciled without touching entries that come from
# other publishers (such as a future CMS).
DOCUMENT_REF_PREFIX = "file:"


class SyncKnowledgeDocumentsUseCase:
    """Makes the knowledge base match the documents: publishes what is published, drops what is a draft or gone.

    Idempotent, and one bad document never blocks the others: it is reported with the reason instead. It fails closed: a
    document that is not valid right now is not served, so the assistant never quotes something half-edited.
    """

    def __init__(self, *, index: KnowledgeIndexPort, source: KnowledgeDocumentSourcePort, clock: Clock) -> None:
        self._index = index
        self._source = source
        self._clock = clock

    async def execute(self) -> KnowledgeSyncReport:
        batch = self._source.read_all()
        problems = list(batch.problems)
        wanted: set[tuple[KnowledgeSourceType, str]] = set()
        drafts = 0
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
            wanted.add((entry.source_type, entry.source_ref))

        removed = 0
        for source_type, source_ref in await self._index.refs_with_prefix(DOCUMENT_REF_PREFIX):
            if (source_type, source_ref) not in wanted:
                await self._index.remove(source_type, source_ref)
                removed += 1
        return KnowledgeSyncReport(published=len(wanted), drafts=drafts, removed=removed, problems=tuple(problems))
