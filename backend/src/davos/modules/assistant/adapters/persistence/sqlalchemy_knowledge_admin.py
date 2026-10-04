from __future__ import annotations

import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.adapters.persistence.knowledge_entry_model import KnowledgeEntryModel
from davos.modules.assistant.adapters.persistence.knowledge_search_columns import knowledge_search_columns
from davos.modules.assistant.application.ports.knowledge_admin_port import KnowledgeAdminPort
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer

_K = KnowledgeEntryModel


class SqlAlchemyKnowledgeAdmin(KnowledgeAdminPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], normalizer: PersianTextNormalizer) -> None:
        self._session_factory = session_factory
        self._normalizer = normalizer

    async def list_all(self) -> list[KnowledgeEntry]:
        async with self._session_factory() as session:
            rows = (await session.scalars(select(_K).order_by(_K.source_type, _K.title))).all()
        return [self._entry(row) for row in rows]

    async def get(self, entry_id: uuid.UUID) -> KnowledgeEntry | None:
        async with self._session_factory() as session:
            row = await session.get(_K, entry_id)
        return None if row is None else self._entry(row)

    async def add(self, entry: KnowledgeEntry) -> None:
        async with self._session_factory() as session, session.begin():
            session.add(
                _K(
                    id=entry.entry_id,
                    source_type=entry.source_type.value,
                    source_ref=entry.source_ref,
                    title=entry.title,
                    body=entry.body,
                    url=entry.url,
                    updated_at=entry.updated_at,
                    **knowledge_search_columns(entry, self._normalizer),
                )
            )

    async def save(self, entry: KnowledgeEntry) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(
                update(_K)
                .where(_K.id == entry.entry_id)
                .values(
                    source_type=entry.source_type.value,
                    title=entry.title,
                    body=entry.body,
                    url=entry.url,
                    updated_at=entry.updated_at,
                    **knowledge_search_columns(entry, self._normalizer),
                )
            )

    async def delete(self, entry_id: uuid.UUID) -> bool:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(delete(_K).where(_K.id == entry_id))
            return bool(result.rowcount)  # type: ignore[attr-defined]

    @staticmethod
    def _entry(row: KnowledgeEntryModel) -> KnowledgeEntry:
        return KnowledgeEntry(
            entry_id=row.id,
            source_type=KnowledgeSourceType(row.source_type),
            source_ref=row.source_ref,
            title=row.title,
            body=row.body,
            url=row.url,
            updated_at=row.updated_at,
        )
