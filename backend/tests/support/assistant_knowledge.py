"""Publishing knowledge entries in integration tests."""

from __future__ import annotations

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.application.use_cases.index_knowledge_entry_command import IndexKnowledgeEntryCommand
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


async def publish(
    container: ApplicationContainer, ref: str, title: str, body: str, url: str, *, kind: str = "faq"
) -> None:
    await container.index_knowledge_entry().execute(
        IndexKnowledgeEntryCommand(KnowledgeSourceType(kind), ref, title, body, url, True)
    )
