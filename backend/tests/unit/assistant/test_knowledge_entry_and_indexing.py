from datetime import UTC, datetime

import pytest

from davos.modules.assistant.application.use_cases.index_knowledge_entry_command import IndexKnowledgeEntryCommand
from davos.modules.assistant.application.use_cases.index_knowledge_entry_use_case import IndexKnowledgeEntryUseCase
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.errors.invalid_knowledge_entry_error import InvalidKnowledgeEntryError
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_knowledge_index import InMemoryKnowledgeIndex

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _command(**overrides: object) -> IndexKnowledgeEntryCommand:
    values = {
        "source_type": KnowledgeSourceType.FAQ,
        "source_ref": "faq-1",
        "title": "عنوان",
        "body": "متن",
        "url": "/faq#1",
        "published": True,
    }
    return IndexKnowledgeEntryCommand(**{**values, **overrides})  # type: ignore[arg-type]


@pytest.mark.parametrize("url", ["https://evil.example", "//evil.example", "faq", "javascript:alert(1)", ""])
def test_only_internal_paths_are_allowed_as_source_links(url: str) -> None:
    with pytest.raises(InvalidKnowledgeEntryError):
        KnowledgeEntry.create(
            source_type=KnowledgeSourceType.FAQ, source_ref="x", title="t", body="b", url=url, now=NOW
        )


@pytest.mark.parametrize(("title", "body"), [("", "b"), ("t", ""), ("  ", "b"), ("t", "x" * 4001)])
def test_empty_or_oversized_content_is_rejected(title: str, body: str) -> None:
    with pytest.raises(InvalidKnowledgeEntryError):
        KnowledgeEntry.create(
            source_type=KnowledgeSourceType.FAQ, source_ref="x", title=title, body=body, url="/a", now=NOW
        )


async def test_published_content_is_indexed() -> None:
    index = InMemoryKnowledgeIndex()
    await IndexKnowledgeEntryUseCase(index=index, clock=FixedClock()).execute(_command())
    assert [e.source_ref for e in index.upserts] == ["faq-1"] and index.removed == []


async def test_unpublished_content_is_removed_and_never_indexed() -> None:
    index = InMemoryKnowledgeIndex()
    await IndexKnowledgeEntryUseCase(index=index, clock=FixedClock()).execute(_command(published=False))
    assert index.upserts == []
    assert index.removed == [(KnowledgeSourceType.FAQ, "faq-1")]


def test_knowledge_source_types_cannot_represent_private_data() -> None:
    assert {t.value for t in KnowledgeSourceType} == {"faq", "policy", "service", "pricing", "contact"}
