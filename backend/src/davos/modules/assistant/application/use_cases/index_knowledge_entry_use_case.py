from __future__ import annotations

from davos.modules.assistant.application.ports.knowledge_index_port import KnowledgeIndexPort
from davos.modules.assistant.application.use_cases.index_knowledge_entry_command import IndexKnowledgeEntryCommand
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.shared_kernel.application.clock import Clock


class IndexKnowledgeEntryUseCase:
    """Keeps the knowledge base in sync with content publication.

    Only published content is indexed; unpublishing (or a draft edit) removes the entry, so a
    draft can never be quoted by the assistant.
    """

    def __init__(self, *, index: KnowledgeIndexPort, clock: Clock) -> None:
        self._index = index
        self._clock = clock

    async def execute(self, command: IndexKnowledgeEntryCommand) -> None:
        if not command.published:
            await self._index.remove(command.source_type, command.source_ref)
            return
        entry = KnowledgeEntry.create(
            source_type=command.source_type,
            source_ref=command.source_ref,
            title=command.title,
            body=command.body,
            url=command.url,
            now=self._clock.now(),
        )
        await self._index.upsert(entry)
