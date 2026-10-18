from __future__ import annotations

import uuid

from davos.modules.assistant.application.ports.knowledge_admin_port import KnowledgeAdminPort
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.assistant_policy import AssistantPolicy
from davos.modules.assistant.domain.value_objects.knowledge_catalog import KnowledgeCatalog
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError

# Entries made in the panel carry this prefix; the ones imported from files at the first start carry "file:".
ADMIN_REF_PREFIX = "admin:"


class ManageKnowledgeUseCase:
    """Adding, editing and deleting what the assistant may answer from. A change is live at once, and every stored
    answer written from the old texts stops being served on its own (the fingerprint covers the texts)."""

    def __init__(self, *, admin: KnowledgeAdminPort, policy: AssistantPolicy, clock: Clock) -> None:
        self._admin = admin
        self._policy = policy
        self._clock = clock

    async def catalog(self) -> KnowledgeCatalog:
        return KnowledgeCatalog(
            entries=tuple(await self._admin.list_all()),
            max_entries=self._policy.whole_knowledge_max_entries,
            max_chars=self._policy.whole_knowledge_max_chars,
        )

    async def add(self, *, source_type: KnowledgeSourceType, title: str, body: str, url: str) -> KnowledgeEntry:
        entry = KnowledgeEntry.create(
            source_type=source_type,
            source_ref=f"{ADMIN_REF_PREFIX}{uuid.uuid4()}",
            title=title,
            body=body,
            url=url,
            now=self._clock.now(),
        )
        await self._admin.add(entry)
        return entry

    async def update(
        self, entry_id: uuid.UUID, *, source_type: KnowledgeSourceType, title: str, body: str, url: str
    ) -> KnowledgeEntry:
        existing = await self._admin.get(entry_id)
        if existing is None:
            raise NotFoundError("متن دانش یافت نشد.")
        revised = existing.revise(source_type=source_type, title=title, body=body, url=url, now=self._clock.now())
        await self._admin.save(revised)
        return revised

    async def delete(self, entry_id: uuid.UUID) -> None:
        if not await self._admin.delete(entry_id):
            raise NotFoundError("متن دانش یافت نشد.")
