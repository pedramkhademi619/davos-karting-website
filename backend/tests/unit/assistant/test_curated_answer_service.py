"""Answers the owner writes by hand: served like stored model answers, but not tied to the knowledge texts."""

from __future__ import annotations

import uuid

import pytest

from davos.modules.assistant.application.services.curated_answer_service import CuratedAnswerService
from davos.modules.assistant.domain.value_objects.curated_answer import CURATED_FINGERPRINT
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from tests.fakes.concept_embedding import ConceptEmbedding
from tests.unit.assistant.test_answer_cache_flow import PAYMENT, PAYMENT_PARAPHRASE, World, service_passage

OWNER_ANSWER = "فقط از درگاه بانک ملت؛ پرداخت در محل نداریم."


def curated(world: World) -> CuratedAnswerService:
    return CuratedAnswerService(
        embedding=world.embedding,
        cache=world.store,
        policy=world.cache._policy,
        clock=world.clock,
    )


async def test_an_answer_the_owner_wrote_is_served_without_calling_the_model() -> None:
    world = World()
    await curated(world).add(question=PAYMENT, answer=OWNER_ANSWER)

    answer = await world.ask(PAYMENT_PARAPHRASE)

    assert answer.text == OWNER_ANSWER and answer.from_cache
    assert world.chat.calls == 0


async def test_it_keeps_being_served_after_the_knowledge_texts_change() -> None:
    """A model answer stops matching when a text it was written from changes; the owner's does not."""
    world = World()
    await curated(world).add(question=PAYMENT, answer=OWNER_ANSWER)
    world.passages = [service_passage("متن کاملا تازه و متفاوت درباره پرداخت از درگاه.")]

    assert (await world.ask(PAYMENT)).text == OWNER_ANSWER
    assert world.chat.calls == 0


async def test_editing_a_model_answer_turns_it_into_the_owners_and_keeps_its_use_count() -> None:
    world = World()
    await world.ask(PAYMENT)  # the model answers and the answer is stored
    stored = world.store.entries[0]
    stored.hits = 4

    await curated(world).edit(stored.entry.entry_id, question=PAYMENT, answer=OWNER_ANSWER)

    assert stored.entry.fingerprint == CURATED_FINGERPRINT and stored.hits == 4 and stored.active
    assert (await world.ask(PAYMENT_PARAPHRASE)).text == OWNER_ANSWER


async def test_editing_brings_a_retired_answer_back() -> None:
    world = World()
    await world.ask(PAYMENT)
    stored = world.store.entries[0]
    stored.active = False
    await curated(world).edit(stored.entry.entry_id, question=PAYMENT, answer=OWNER_ANSWER)
    assert stored.active


async def test_a_question_that_depends_on_the_asker_is_refused() -> None:
    world = World()
    with pytest.raises(ValidationError, match="عمومی"):
        await curated(world).add(question="۱۴ سالمه ساعت ۵ میتونم بیام؟", answer="بله")
    assert world.store.entries == []


@pytest.mark.parametrize(("question", "answer"), [("", "پاسخ"), (PAYMENT, "  "), (PAYMENT, "ا" * 2001)])
async def test_an_empty_or_oversized_text_is_refused(question: str, answer: str) -> None:
    with pytest.raises(ValidationError):
        await curated(World()).add(question=question, answer=answer)


async def test_editing_something_that_does_not_exist_says_so() -> None:
    with pytest.raises(NotFoundError):
        await curated(World()).edit(uuid.uuid4(), question=PAYMENT, answer=OWNER_ANSWER)


async def test_a_model_that_is_not_ready_gives_a_clear_message() -> None:
    world = World(embedding=ConceptEmbedding(ready=False))
    with pytest.raises(ValidationError, match="آماده نیست"):
        await curated(world).add(question=PAYMENT, answer=OWNER_ANSWER)
