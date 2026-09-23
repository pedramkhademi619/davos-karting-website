from __future__ import annotations

import pytest

from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem
from davos.modules.assistant.application.ports.knowledge_source_unavailable_error import KnowledgeSourceUnavailableError
from davos.modules.assistant.application.use_cases.sync_knowledge_documents_use_case import (
    DOCUMENT_REF_PREFIX,
    SyncKnowledgeDocumentsUseCase,
)
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_knowledge_index import InMemoryKnowledgeIndex
from tests.fakes.static_knowledge_documents import StaticKnowledgeDocuments, document


def _use_case(source: StaticKnowledgeDocuments, index: InMemoryKnowledgeIndex) -> SyncKnowledgeDocumentsUseCase:
    return SyncKnowledgeDocumentsUseCase(index=index, source=source, clock=FixedClock())


async def test_published_documents_are_indexed_under_a_file_prefix() -> None:
    index = InMemoryKnowledgeIndex()
    report = await _use_case(StaticKnowledgeDocuments([document("booking"), document("club")]), index).execute()
    assert (report.published, report.drafts, report.removed, report.problems) == (2, 0, 0, ())
    assert index.refs == {f"{DOCUMENT_REF_PREFIX}booking", f"{DOCUMENT_REF_PREFIX}club"}


async def test_drafts_stay_on_file_and_are_never_indexed() -> None:
    index = InMemoryKnowledgeIndex()
    report = await _use_case(StaticKnowledgeDocuments([document("age", published=False)]), index).execute()
    assert (report.published, report.drafts) == (0, 1)
    assert index.entries == {} and index.upserts == []


async def test_running_it_twice_changes_nothing() -> None:
    index = InMemoryKnowledgeIndex()
    use_case = _use_case(StaticKnowledgeDocuments([document("booking"), document("age", published=False)]), index)
    first, second = await use_case.execute(), await use_case.execute()
    assert first == second
    assert index.refs == {f"{DOCUMENT_REF_PREFIX}booking"}


async def test_a_deleted_or_drafted_document_disappears_from_the_assistant() -> None:
    index = InMemoryKnowledgeIndex()
    source = StaticKnowledgeDocuments([document("a"), document("b"), document("c")])
    use_case = _use_case(source, index)
    await use_case.execute()

    source.documents = [document("a"), document("b", published=False)]  # c deleted, b turned into a draft
    report = await use_case.execute()

    assert report.removed == 2 and report.drafts == 1
    assert index.refs == {f"{DOCUMENT_REF_PREFIX}a"}


async def test_an_edit_updates_the_entry_in_place() -> None:
    index = InMemoryKnowledgeIndex()
    source = StaticKnowledgeDocuments([document("a", body="قدیمی")])
    use_case = _use_case(source, index)
    await use_case.execute()
    source.documents = [document("a", body="جدید")]
    await use_case.execute()
    assert [e.body for e in index.entries.values()] == ["جدید"]


async def test_entries_from_other_publishers_are_never_touched() -> None:
    index = InMemoryKnowledgeIndex()
    await index.upsert(
        KnowledgeEntry.create(
            source_type=KnowledgeSourceType.FAQ,
            source_ref="cms-42",
            title="t",
            body="b",
            url="/x",
            now=FixedClock().now(),
        )
    )
    await _use_case(StaticKnowledgeDocuments([]), index).execute()
    assert index.refs == {"cms-42"}


async def test_an_invalid_document_is_reported_and_does_not_block_the_rest() -> None:
    index = InMemoryKnowledgeIndex()
    bad_link = document("bad", url="https://evil.example")
    report = await _use_case(StaticKnowledgeDocuments([bad_link, document("good")]), index).execute()
    assert index.refs == {f"{DOCUMENT_REF_PREFIX}good"}
    assert [p.name for p in report.problems] == ["bad"]


async def test_a_document_that_becomes_invalid_is_taken_down_rather_than_left_half_edited() -> None:
    index = InMemoryKnowledgeIndex()
    source = StaticKnowledgeDocuments([document("a")])
    use_case = _use_case(source, index)
    await use_case.execute()
    source.documents = [document("a", url="not-a-path")]
    report = await use_case.execute()
    assert index.entries == {} and report.removed == 1 and report.problems[0].name == "a"


async def test_problems_from_the_source_are_passed_through() -> None:
    problem = KnowledgeDocumentProblem("typo", "title is required")
    report = await _use_case(StaticKnowledgeDocuments([document("ok")], [problem]), InMemoryKnowledgeIndex()).execute()
    assert report.problems == (problem,) and report.published == 1


async def test_an_unreachable_source_leaves_the_knowledge_base_exactly_as_it_was() -> None:
    index = InMemoryKnowledgeIndex()
    use_case = _use_case(StaticKnowledgeDocuments([document("a")]), index)
    await use_case.execute()
    broken = _use_case(StaticKnowledgeDocuments(unavailable=True), index)
    with pytest.raises(KnowledgeSourceUnavailableError):
        await broken.execute()
    assert index.refs == {f"{DOCUMENT_REF_PREFIX}a"} and index.removed == []
