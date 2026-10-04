from __future__ import annotations

import pytest

from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem
from davos.modules.assistant.application.ports.knowledge_source_unavailable_error import KnowledgeSourceUnavailableError
from davos.modules.assistant.application.use_cases.seed_knowledge_from_documents_use_case import (
    DOCUMENT_REF_PREFIX,
    SeedKnowledgeFromDocumentsUseCase,
)
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_knowledge_index import InMemoryKnowledgeIndex
from tests.fakes.static_knowledge_documents import StaticKnowledgeDocuments, document


def _use_case(source: StaticKnowledgeDocuments, index: InMemoryKnowledgeIndex) -> SeedKnowledgeFromDocumentsUseCase:
    return SeedKnowledgeFromDocumentsUseCase(index=index, source=source, clock=FixedClock())


async def test_an_empty_knowledge_base_is_filled_from_the_published_documents() -> None:
    index = InMemoryKnowledgeIndex()
    report = await _use_case(StaticKnowledgeDocuments([document("booking"), document("club")]), index).execute()
    assert (report.imported, report.drafts, report.skipped_because_not_empty, report.problems) == (2, 0, False, ())
    assert index.refs == {f"{DOCUMENT_REF_PREFIX}booking", f"{DOCUMENT_REF_PREFIX}club"}


async def test_drafts_are_not_imported() -> None:
    index = InMemoryKnowledgeIndex()
    report = await _use_case(StaticKnowledgeDocuments([document("age", published=False)]), index).execute()
    assert (report.imported, report.drafts) == (0, 1)
    assert index.entries == {}


async def test_once_anything_exists_the_documents_are_never_read_again() -> None:
    """The staff panel is where the owner edits and deletes; the files must not bring any of that back."""
    index = InMemoryKnowledgeIndex()
    await index.upsert(
        KnowledgeEntry.create(
            source_type=KnowledgeSourceType.FAQ,
            source_ref="admin:1",
            title="t",
            body="b",
            url="/x",
            now=FixedClock().now(),
        )
    )
    report = await _use_case(StaticKnowledgeDocuments([document("a"), document("b")]), index).execute()
    assert report.skipped_because_not_empty and report.imported == 0
    assert index.refs == {"admin:1"}


async def test_running_it_twice_changes_nothing() -> None:
    index = InMemoryKnowledgeIndex()
    use_case = _use_case(StaticKnowledgeDocuments([document("booking")]), index)
    await use_case.execute()
    second = await use_case.execute()
    assert second.skipped_because_not_empty and index.refs == {f"{DOCUMENT_REF_PREFIX}booking"}


async def test_an_invalid_document_is_reported_and_does_not_block_the_rest() -> None:
    index = InMemoryKnowledgeIndex()
    bad_link = document("bad", url="https://evil.example")
    report = await _use_case(StaticKnowledgeDocuments([bad_link, document("good")]), index).execute()
    assert index.refs == {f"{DOCUMENT_REF_PREFIX}good"}
    assert [p.name for p in report.problems] == ["bad"]


async def test_problems_from_the_source_are_passed_through() -> None:
    problem = KnowledgeDocumentProblem("typo", "title is required")
    report = await _use_case(StaticKnowledgeDocuments([document("ok")], [problem]), InMemoryKnowledgeIndex()).execute()
    assert report.problems == (problem,) and report.imported == 1


async def test_an_unreachable_source_changes_nothing() -> None:
    index = InMemoryKnowledgeIndex()
    with pytest.raises(KnowledgeSourceUnavailableError):
        await _use_case(StaticKnowledgeDocuments(unavailable=True), index).execute()
    assert index.entries == {}
