"""The answer cache inside the answering flow: which questions reuse a stored answer and which never may."""

from __future__ import annotations

import uuid

from davos.modules.assistant.adapters.budget.in_memory_ai_budget import InMemoryAiBudget
from davos.modules.assistant.application.ports.ai_provider_unavailable_error import AiProviderUnavailableError
from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.modules.assistant.application.services.question_equivalence_verifier import QuestionEquivalenceVerifier
from davos.modules.assistant.application.services.semantic_answer_cache import SemanticAnswerCache
from davos.modules.assistant.application.use_cases.ask_assistant_command import AskAssistantCommand
from davos.modules.assistant.application.use_cases.ask_assistant_use_case import AskAssistantUseCase
from davos.modules.assistant.application.use_cases.submit_feedback_use_case import SubmitFeedbackUseCase
from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.answer_cache_policy import AnswerCachePolicy
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from tests.fakes.concept_embedding import BLUR_WORD, ConceptEmbedding
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_answer_cache import InMemoryAnswerCache
from tests.fakes.passages import passage
from tests.fakes.recording_interaction_log import RecordingInteractionLog
from tests.fakes.scripted_ai_chat import ScriptedAiChat
from tests.fakes.standard_config import assistant_policy, booking_facts
from tests.fakes.static_knowledge_search import StaticKnowledgeSearch
from tests.fakes.static_persona import StaticPersona

PAYMENT = "پرداخت با چه درگاهیه؟"
PAYMENT_PARAPHRASE = "با کدوم درگاه پول بدم؟"
REPLY = "پرداخت با درگاه بانک ملت است [1]."


def service_passage(text: str = "پرداخت از درگاه بانک ملت انجام می‌شود."):
    return passage(title="نحوه رزرو", text=text, url="/booking", source_type=KnowledgeSourceType.SERVICE)


class _Facts:
    def __init__(self) -> None:
        self.facts = booking_facts()

    async def current(self):
        return self.facts


class World:
    """One shared store and embedding model; ``ask`` builds the use case anew so a test can change what it reads."""

    def __init__(
        self,
        *,
        cache_fails: bool = False,
        embedding: ConceptEmbedding | None = None,
        verifier_says: str | BaseException | list[str | BaseException] | None = None,
    ) -> None:
        self.clock = FixedClock()
        self.embedding = embedding or ConceptEmbedding()
        self.store = InMemoryAnswerCache(fail=cache_fails)
        self.chat = ScriptedAiChat(REPLY)
        self.log = RecordingInteractionLog()
        self.passages = [service_passage()]
        self.persona = "لحن گرم"
        self.facts = _Facts()
        # the model's check of close questions; absent unless a test gives it an answer
        script = verifier_says if isinstance(verifier_says, list) else [verifier_says or ""]
        self.verifier_chat = ScriptedAiChat(script[0], then=script[1:])
        verifier = (
            None
            if verifier_says is None
            else QuestionEquivalenceVerifier(
                chat=self.verifier_chat,
                budget=InMemoryAiBudget(daily_limit=1_000_000, clock=self.clock),
                timeout_seconds=2.0,
            )
        )
        self.cache = SemanticAnswerCache(
            embedding=self.embedding,
            cache=self.store,
            fingerprint=AnswerFingerprint(
                rules_version="r1", answer_models="m", embedding_model="concept-test-embedding"
            ),
            policy=AnswerCachePolicy(
                similarity_threshold=0.9, verify_from_similarity=0.6, candidate_limit=8, max_text_chars=400
            ),
            verifier=verifier,
            clock=self.clock,
        )

    def use_case(self) -> AskAssistantUseCase:
        return AskAssistantUseCase(
            search=StaticKnowledgeSearch(list(self.passages)),
            chat=self.chat,
            budget=InMemoryAiBudget(daily_limit=1_000_000, clock=self.clock),
            interactions=self.log,
            rate_limiter=InMemoryRateLimiter(self.clock),
            clock=self.clock,
            policy=assistant_policy(),
            persona=StaticPersona(self.persona),
            booking_facts=self.facts,
            answer_cache=self.cache,
        )

    async def ask(self, text: str):
        return await self.use_case().execute(AskAssistantCommand(text=text, client_ip="203.0.113.9"))


async def test_a_paraphrase_of_a_general_question_is_answered_from_the_cache() -> None:
    world = World()
    first = await world.ask(PAYMENT)
    second = await world.ask(PAYMENT_PARAPHRASE)
    assert world.chat.calls == 1, "the second question must not reach the model"
    assert not first.from_cache and second.from_cache
    assert second.outcome is AnswerOutcome.ANSWERED and second.text == first.text
    assert [s.url for s in second.sources] == [s.url for s in first.sources] == ["/booking"]


async def test_a_hit_costs_no_tokens_and_is_recorded() -> None:
    world = World()
    await world.ask(PAYMENT)
    await world.ask(PAYMENT_PARAPHRASE)
    stored = world.store.entries[0]
    served = world.log.items[-1]
    assert stored.hits == 1
    assert served.served_from_cache and served.cache_entry_id == stored.entry.entry_id
    assert served.usage.total == 0
    assert world.log.items[0].cache_entry_id == stored.entry.entry_id  # the answer the model wrote was stored as it


async def test_questions_that_differ_in_a_deciding_detail_never_share_an_answer() -> None:
    """Online and by phone are the same to an embedding model but have different answers: the signature splits them."""
    world = World()
    await world.ask("پرداخت آنلاین چطوریه؟")
    answer = await world.ask("پرداخت تلفنی چطوریه؟")
    assert not answer.from_cache and world.chat.calls == 2


async def test_a_question_with_an_age_a_day_or_an_hour_is_never_cached() -> None:
    world = World()
    for text in (
        "پسرم ۱۲ ساله است، پرداخت چطوریه؟",
        "شنبه پرداخت چطوریه؟",
        "ساعت ۵ پرداخت چطوریه؟",
        "۹ نفریم، پرداخت؟",
    ):
        await world.ask(text)
        await world.ask(text)
    assert world.store.entries == [] and world.chat.calls == 8


async def test_a_question_with_personal_data_is_never_stored_or_looked_up() -> None:
    world = World()
    await world.ask("شماره من 09123456789 است، پرداخت چطوریه؟")
    assert world.store.entries == [] and world.embedding.embedded == []


async def test_a_fragment_that_only_makes_sense_after_another_message_is_never_cached() -> None:
    world = World()
    await world.ask("و برای روز تعطیل؟")
    assert world.store.entries == []


async def test_an_answer_that_cites_the_riding_rules_is_never_stored() -> None:
    world = World()
    world.passages = [passage(title="شرایط", text="قانون سواری.", url="/faq")]  # a policy source
    await world.ask(PAYMENT)
    answer = await world.ask(PAYMENT_PARAPHRASE)
    assert world.store.entries == [] and not answer.from_cache and world.chat.calls == 2


async def test_changing_a_published_text_stops_old_answers_from_being_served() -> None:
    world = World()
    await world.ask(PAYMENT)
    world.passages = [service_passage("پرداخت از درگاه بانک دیگری انجام می‌شود.")]
    answer = await world.ask(PAYMENT_PARAPHRASE)
    assert not answer.from_cache and world.chat.calls == 2


async def test_changing_a_price_in_the_admin_panel_stops_old_answers_from_being_served() -> None:
    world = World()
    await world.ask(PAYMENT)
    world.facts.facts = booking_facts(normal_single_toman=900_000)
    answer = await world.ask(PAYMENT_PARAPHRASE)
    assert not answer.from_cache and world.chat.calls == 2


async def test_changing_the_style_notes_stops_old_answers_from_being_served() -> None:
    world = World()
    await world.ask(PAYMENT)
    world.persona = "لحن رسمی"
    answer = await world.ask(PAYMENT_PARAPHRASE)
    assert not answer.from_cache and world.chat.calls == 2


async def test_a_cache_that_is_down_never_breaks_an_answer() -> None:
    world = World(cache_fails=True)
    first = await world.ask(PAYMENT)
    second = await world.ask(PAYMENT_PARAPHRASE)
    assert first.outcome is second.outcome is AnswerOutcome.ANSWERED
    assert world.chat.calls == 2 and not second.from_cache


async def test_an_embedding_model_that_is_not_ready_only_turns_the_cache_off() -> None:
    world = World(embedding=ConceptEmbedding(ready=False))
    first = await world.ask(PAYMENT)
    second = await world.ask(PAYMENT)
    assert first.outcome is second.outcome is AnswerOutcome.ANSWERED
    assert world.chat.calls == 2 and world.store.entries == []


async def test_a_not_helpful_vote_retires_the_stored_answer() -> None:
    world = World()
    first = await world.ask(PAYMENT)
    feedback = SubmitFeedbackUseCase(interactions=world.log, answer_cache=world.cache)
    assert first.interaction_id is not None
    await feedback.execute(interaction_id=first.interaction_id, helpful=False)
    assert not world.store.entries[0].active
    answer = await world.ask(PAYMENT_PARAPHRASE)
    assert not answer.from_cache and world.chat.calls == 2


async def test_a_helpful_vote_keeps_the_stored_answer() -> None:
    world = World()
    first = await world.ask(PAYMENT)
    assert first.interaction_id is not None
    await SubmitFeedbackUseCase(interactions=world.log, answer_cache=world.cache).execute(
        interaction_id=first.interaction_id, helpful=True
    )
    assert world.store.entries[0].active


async def test_a_vote_about_an_unknown_answer_is_still_not_found() -> None:
    from davos.shared_kernel.domain.errors.not_found_error import NotFoundError

    world = World()
    feedback = SubmitFeedbackUseCase(interactions=world.log, answer_cache=world.cache)
    try:
        await feedback.execute(interaction_id=uuid.uuid4(), helpful=False)
    except NotFoundError:
        return
    raise AssertionError("expected NotFoundError")


# --- close, but not identical, questions: the language model's check decides ---------------------------------------
CLOSE = f"{BLUR_WORD} پرداخت با چه درگاهیه؟"  # similarity 0.86 to PAYMENT: above the floor, below the threshold


async def test_a_close_question_is_served_when_the_model_confirms_it_means_the_same() -> None:
    world = World(verifier_says="YES")
    await world.ask(PAYMENT)
    answer = await world.ask(CLOSE)
    assert answer.from_cache and world.chat.calls == 1
    assert world.verifier_chat.calls == 2, "asked in both directions"


async def test_a_close_question_is_answered_by_the_model_when_the_check_says_no() -> None:
    world = World(verifier_says="NO")
    await world.ask(PAYMENT)
    answer = await world.ask(CLOSE)
    assert not answer.from_cache and world.chat.calls == 2


async def test_both_directions_must_agree() -> None:
    world = World(verifier_says=["YES", "NO"])  # the first direction agrees, the second does not
    await world.ask(PAYMENT)
    answer = await world.ask(CLOSE)
    assert not answer.from_cache and world.chat.calls == 2


async def test_a_failing_check_only_sends_the_question_to_the_model() -> None:
    world = World(verifier_says=AiProviderUnavailableError("down"))
    await world.ask(PAYMENT)
    answer = await world.ask(CLOSE)
    assert answer.outcome is AnswerOutcome.ANSWERED and not answer.from_cache and world.chat.calls == 2


async def test_without_the_check_a_close_question_is_never_served() -> None:
    world = World()  # no verifier
    await world.ask(PAYMENT)
    answer = await world.ask(CLOSE)
    assert not answer.from_cache and world.chat.calls == 2


async def test_the_check_is_not_asked_below_the_floor_or_when_the_signature_differs() -> None:
    world = World(verifier_says="YES")
    await world.ask(PAYMENT)
    await world.ask("باشگاه مشتریان فعاله؟")  # another topic: similarity 0
    await world.ask(f"{BLUR_WORD} پرداخت تلفنی چطوریه؟")  # close, but "by phone" is not what was stored
    assert world.verifier_chat.calls == 0
