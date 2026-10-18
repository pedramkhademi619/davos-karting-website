"""Knowledge files on disk seed an empty database -> the real ask flow, with only the AI provider scripted."""

from __future__ import annotations

from pathlib import Path

import pytest

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.persistence.sqlalchemy_knowledge_index import SqlAlchemyKnowledgeIndex
from davos.modules.assistant.application.use_cases.ask_assistant_command import AskAssistantCommand
from davos.modules.assistant.application.use_cases.index_knowledge_entry_command import IndexKnowledgeEntryCommand
from davos.modules.assistant.application.use_cases.seed_knowledge_from_documents_use_case import (
    SeedKnowledgeFromDocumentsUseCase,
)
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery
from tests.fakes.scripted_ai_chat import ScriptedAiChat

pytestmark = pytest.mark.integration

BOOKING = "title: چطور نوبت رزرو کنم؟\nurl: /\ntype: service\n\nرزرو نوبت آنلاین از دکمه «رزرو نوبت» سایت انجام می‌شود."
AGE_DRAFT = "title: محدودیت سنی و قد\nurl: /faq\nstatus: draft\n\nحداقل سن مجاز دوازده سال است."


def _seed_use_case(container: ApplicationContainer, folder: Path) -> SeedKnowledgeFromDocumentsUseCase:
    container.settings = container.settings.model_copy(update={"assistant_knowledge_dir": str(folder)})
    use_case = container.seed_knowledge_from_documents()
    assert use_case is not None
    return use_case


async def _ask(container: ApplicationContainer, text: str):
    return await container.ask_assistant().execute(AskAssistantCommand(text=text, client_ip="203.0.113.5"))


async def test_files_on_disk_become_answerable_with_a_source_and_drafts_never_reach_the_model(
    container: ApplicationContainer, ai_chat: ScriptedAiChat, tmp_path: Path
) -> None:
    (tmp_path / "booking.txt").write_text(BOOKING, encoding="utf-8")
    (tmp_path / "age.txt").write_text(AGE_DRAFT, encoding="utf-8")

    report = await _seed_use_case(container, tmp_path).execute()
    assert (report.imported, report.drafts, report.problems) == (1, 1, ())

    answer = await _ask(container, "چطور نوبت رزرو کنم؟")
    assert answer.outcome is AnswerOutcome.ANSWERED
    assert [(s.title, s.url) for s in answer.sources] == [("چطور نوبت رزرو کنم؟", "/")]
    sent = ai_chat.system_prompt + ai_chat.user_prompt
    assert "«رزرو نوبت»" in ai_chat.system_prompt
    assert "دوازده" not in sent, "a draft must never be sent to the model"
    assert "<style>" in ai_chat.system_prompt, "the default style notes are part of the prompt"

    ai_chat.reply = "NO_ANSWER"  # what a well-behaved model says when the published text does not cover the question
    declined = await _ask(container, "محدودیت سنی و قد برای رانندگی چقدر است؟")
    assert declined.outcome is AnswerOutcome.INSUFFICIENT_INFORMATION and declined.suggest_ticket
    assert "دوازده" not in ai_chat.system_prompt + ai_chat.user_prompt, (
        "the draft is not in the prompt even when the whole base is sent"
    )


async def test_edits_and_deletions_made_in_the_panel_survive_a_restart(
    container: ApplicationContainer, tmp_path: Path
) -> None:
    """The files only start a fresh installation: running the seed again must not undo the owner's work."""
    file = tmp_path / "booking.txt"
    file.write_text(BOOKING, encoding="utf-8")
    await _seed_use_case(container, tmp_path).execute()
    manage = container.manage_knowledge()
    entry = (await manage.catalog()).entries[0]
    await manage.update(entry.entry_id, source_type=entry.source_type, title=entry.title, body="متن تازه", url="/")

    file.write_text(BOOKING.replace("آنلاین", "تلفنی"), encoding="utf-8")
    report = await _seed_use_case(container, tmp_path).execute()

    assert report.skipped_because_not_empty
    assert [e.body for e in (await manage.catalog()).entries] == ["متن تازه"]
    await manage.delete(entry.entry_id)
    assert (await manage.catalog()).entries == ()


async def test_any_existing_entry_stops_the_files_from_being_read(
    container: ApplicationContainer, tmp_path: Path
) -> None:
    await container.index_knowledge_entry().execute(
        IndexKnowledgeEntryCommand(
            source_type=KnowledgeSourceType.POLICY,
            source_ref="cms-42",
            title="لغو رزرو",
            body="برای لغو رزرو با پشتیبانی تماس بگیرید.",
            url="/policies/cancellation",
            published=True,
        )
    )
    (tmp_path / "booking.txt").write_text(BOOKING, encoding="utf-8")
    await _seed_use_case(container, tmp_path).execute()
    index = SqlAlchemyKnowledgeIndex(container.session_factory, PersianTextNormalizer())
    assert await index.refs_with_prefix("cms-") == [(KnowledgeSourceType.POLICY, "cms-42")]
    assert await index.refs_with_prefix("file:") == []  # the booking file was not imported


async def test_the_prefix_lookup_treats_sql_wildcards_literally(container: ApplicationContainer) -> None:
    index = SqlAlchemyKnowledgeIndex(container.session_factory, PersianTextNormalizer())
    now = container.clock.now()
    for ref in ("file:a_b", "file:axb", "file:100%"):
        await index.upsert(
            KnowledgeEntry.create(
                source_type=KnowledgeSourceType.FAQ, source_ref=ref, title="t", body="b", url="/x", now=now
            )
        )
    assert [ref for _, ref in await index.refs_with_prefix("file:a_")] == ["file:a_b"]
    assert [ref for _, ref in await index.refs_with_prefix("file:1")] == ["file:100%"]
    assert await index.refs_with_prefix("file:%") == []


HOURS = "title: ساعت کاری\nurl: /contact\ntype: contact\n\nساعت کاری از ۱۵ تا ۲۴ است."


async def test_a_small_knowledge_base_answers_casual_questions_that_a_keyword_gate_would_miss(
    container: ApplicationContainer, ai_chat: ScriptedAiChat, tmp_path: Path
) -> None:
    (tmp_path / "booking.txt").write_text(BOOKING, encoding="utf-8")
    (tmp_path / "hours.txt").write_text(HOURS, encoding="utf-8")
    await _seed_use_case(container, tmp_path).execute()

    # In real life this phrasing scores about 0.21 against the booking entry, below the 0.3 gate.
    answer = await _ask(container, "می‌خوام برای آخر هفته یه نوبت بگیرم، از کجا شروع کنم؟")

    assert answer.outcome is AnswerOutcome.ANSWERED
    assert "چطور نوبت رزرو کنم؟" in ai_chat.system_prompt and "ساعت کاری" in ai_chat.system_prompt


async def test_the_whole_knowledge_base_is_returned_best_match_first(
    container: ApplicationContainer, tmp_path: Path
) -> None:
    (tmp_path / "booking.txt").write_text(BOOKING, encoding="utf-8")
    (tmp_path / "hours.txt").write_text(HOURS, encoding="utf-8")
    await _seed_use_case(container, tmp_path).execute()

    query = SearchQuery.from_text("ساعت کاری", PersianTextNormalizer())
    passages = await container.knowledge_search().all_entries_if_small(query, max_entries=12, max_total_chars=8000)

    assert [p.title for p in passages] == ["ساعت کاری", "چطور نوبت رزرو کنم؟"]
    assert passages[0].score > passages[1].score


async def test_a_large_knowledge_base_is_not_sent_whole_and_uses_the_relevance_gate(
    container: ApplicationContainer, ai_chat: ScriptedAiChat, tmp_path: Path
) -> None:
    for number in range(13):  # one more than the 12-entry limit
        body = f"title: موضوع شماره {number}\nurl: /faq\n\nمتن یگانه {'الف' * (number + 3)} برای موضوع."
        (tmp_path / f"topic{number}.txt").write_text(body, encoding="utf-8")
    await _seed_use_case(container, tmp_path).execute()

    query = SearchQuery.from_text("می‌خوام یه چیزی بپرسم", PersianTextNormalizer())
    assert await container.knowledge_search().all_entries_if_small(query, max_entries=12, max_total_chars=8000) == []
    answer = await _ask(container, "زنبور عسل چند پا دارد؟")
    assert answer.outcome is AnswerOutcome.INSUFFICIENT_INFORMATION and ai_chat.calls == 0


async def test_too_much_text_also_switches_off_the_whole_knowledge_mode(
    container: ApplicationContainer, tmp_path: Path
) -> None:
    (tmp_path / "big.txt").write_text("title: بزرگ\nurl: /faq\n\n" + "متن " * 500, encoding="utf-8")
    await _seed_use_case(container, tmp_path).execute()
    query = SearchQuery.from_text("متن", PersianTextNormalizer())
    assert await container.knowledge_search().all_entries_if_small(query, max_entries=12, max_total_chars=1000) == []
    assert (
        len(await container.knowledge_search().all_entries_if_small(query, max_entries=12, max_total_chars=8000)) == 1
    )
