from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.adapters.persistence.knowledge_entry_model import KnowledgeEntryModel
from davos.modules.assistant.adapters.persistence.knowledge_search_columns import knowledge_search_columns
from davos.modules.assistant.application.ports.knowledge_index_port import KnowledgeIndexPort
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer


class SqlAlchemyKnowledgeIndex(KnowledgeIndexPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], normalizer: PersianTextNormalizer) -> None:
        self._session_factory = session_factory
        self._normalizer = normalizer

    async def upsert(self, entry: KnowledgeEntry) -> None:
        values = {
            "id": entry.entry_id,
            "source_type": entry.source_type.value,
            "source_ref": entry.source_ref,
            "title": entry.title,
            "body": entry.body,
            "url": entry.url,
            "updated_at": entry.updated_at,
            **knowledge_search_columns(entry, self._normalizer),
        }
        statement = insert(KnowledgeEntryModel).values(**values)
        statement = statement.on_conflict_do_update(
            constraint="uq_assistant_knowledge_source",
            set_={k: v for k, v in values.items() if k not in {"id", "source_type", "source_ref"}},
        )
        async with self._session_factory() as session, session.begin():
            await session.execute(statement)

    async def remove(self, source_type: KnowledgeSourceType, source_ref: str) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(
                delete(KnowledgeEntryModel).where(
                    KnowledgeEntryModel.source_type == source_type.value,
                    KnowledgeEntryModel.source_ref == source_ref,
                )
            )

    async def refs_with_prefix(self, prefix: str) -> list[tuple[KnowledgeSourceType, str]]:
        statement = select(KnowledgeEntryModel.source_type, KnowledgeEntryModel.source_ref).where(
            KnowledgeEntryModel.source_ref.startswith(prefix, autoescape=True)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()
        return [(KnowledgeSourceType(source_type), source_ref) for source_type, source_ref in rows]

    async def count(self) -> int:
        async with self._session_factory() as session:
            return int((await session.execute(select(func.count()).select_from(KnowledgeEntryModel))).scalar_one())
