from __future__ import annotations

import logging
import secrets
import uuid
from collections.abc import Callable, Sequence
from datetime import timedelta

from davos.modules.assistant.application.messages import assistant_messages as messages
from davos.modules.assistant.application.ports.ai_budget_port import AiBudgetPort
from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError
from davos.modules.assistant.application.ports.assistant_persona_port import AssistantPersonaPort
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.application.ports.conversation_context_port import ConversationContextPort
from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.modules.assistant.application.ports.knowledge_search_port import KnowledgeSearchPort
from davos.modules.assistant.application.services.prompt_builder import PromptBuilder
from davos.modules.assistant.application.use_cases.ask_assistant_command import AskAssistantCommand
from davos.modules.assistant.domain.entities.assistant_interaction import AssistantInteraction
from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.assistant.domain.enums.grounding_kind import GroundingKind
from davos.modules.assistant.domain.enums.quick_topic import QuickTopic
from davos.modules.assistant.domain.services.answer_grounding_guard import AnswerGroundingGuard
from davos.modules.assistant.domain.services.intent_reset_detector import IntentResetDetector
from davos.modules.assistant.domain.services.prompt_injection_screen import PromptInjectionScreen
from davos.modules.assistant.domain.services.query_resolver import QueryResolver
from davos.modules.assistant.domain.services.quick_topic_detector import QuickTopicDetector
from davos.modules.assistant.domain.services.small_talk_detector import SmallTalkDetector
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.assistant_policy import AssistantPolicy
from davos.modules.assistant.domain.value_objects.chat_message import ChatMessage
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.question import Question
from davos.modules.assistant.domain.value_objects.resolved_query import ResolvedQuery
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery
from davos.modules.assistant.domain.value_objects.support_answer import SupportAnswer
from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.rate_limiter import RateLimiter
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 2  # conservative for Persian; only used to size the budget reservation
_REMEMBERED_QUESTION_CHARS = 400
_REMEMBERED_ANSWER_CHARS = 500


class AskAssistantUseCase:
    """Retrieval-grounded answering with layered safety.

    Order matters and each step can end the request without calling the model:
    validate -> rate limit -> injection screen -> intent reset -> small talk -> resolve follow-up ->
    quick answer -> retrieve -> relevance gate -> budget -> model call -> grounding guard.
    The model is never asked to guess: without published sources it is not called at all, and every answer it gives
    must cite one. A bare greeting or thanks gets a fixed friendly reply (nothing to cite, nothing to ask a model).
    The conversation memory is optional: without it this is the plain grounded flow.
    """

    def __init__(
        self,
        *,
        search: KnowledgeSearchPort,
        chat: AIChatPort,
        budget: AiBudgetPort,
        interactions: InteractionLogPort,
        rate_limiter: RateLimiter,
        clock: Clock,
        policy: AssistantPolicy,
        persona: AssistantPersonaPort | None = None,
        context: ConversationContextPort | None = None,
        normalizer: PersianTextNormalizer | None = None,
        screen: PromptInjectionScreen | None = None,
        small_talk: SmallTalkDetector | None = None,
        quick_topics: QuickTopicDetector | None = None,
        resets: IntentResetDetector | None = None,
        resolver: QueryResolver | None = None,
        canary_factory: Callable[[], str] = lambda: secrets.token_hex(8),
    ) -> None:
        self._search = search
        self._chat = chat
        self._budget = budget
        self._interactions = interactions
        self._rate_limiter = rate_limiter
        self._clock = clock
        self._policy = policy
        self._persona = persona
        self._context = context
        self._normalizer = normalizer or PersianTextNormalizer()
        self._screen = screen or PromptInjectionScreen()
        self._small_talk = small_talk or SmallTalkDetector(self._normalizer)
        self._quick_topics = quick_topics or QuickTopicDetector(self._normalizer)
        self._resets = resets or IntentResetDetector(self._normalizer)
        self._resolver = resolver or QueryResolver()
        self._canary_factory = canary_factory
        self._prompt_builder = PromptBuilder(max_passage_chars=policy.max_passage_chars)
        self._guard = AnswerGroundingGuard(max_chars=policy.max_answer_chars)

    async def execute(self, command: AskAssistantCommand) -> SupportAnswer:
        question = Question.create(command.text, max_chars=self._policy.max_question_chars)
        await self._enforce_limits(command)

        verdict = self._screen.assess(question.text)
        if verdict.suspicious:
            logger.warning("assistant input refused by screen: %s", ",".join(verdict.reasons))
            return await self._finish(
                command,
                question,
                AnswerOutcome.REFUSED_UNSAFE_INPUT,
                messages.REFUSED_UNSAFE_INPUT,
                passages=[],
                suggest_ticket=True,
            )

        history: tuple[ConversationTurn, ...] = ()
        reset = self._resets.detect(question.text)
        if reset.reset:
            await self._forget(command)
            if not reset.remainder:
                return await self._finish(
                    command,
                    question,
                    AnswerOutcome.SMALL_TALK,
                    messages.CONTEXT_RESET_REPLY,
                    passages=[],
                    suggest_ticket=False,
                )
            question = Question.create(reset.remainder, max_chars=self._policy.max_question_chars)
        else:
            history = await self._recent_history(command)

        small_talk = self._small_talk.detect(question.text)
        if small_talk is not None:
            return await self._finish(
                command,
                question,
                AnswerOutcome.SMALL_TALK,
                messages.SMALL_TALK_REPLIES[small_talk],
                passages=[],
                suggest_ticket=False,
            )

        resolved = self._resolver.resolve(question.text, history)
        quick_passage = await self._quick_passage(self._quick_topics.detect(question.text))
        if quick_passage is not None:
            # A plain, general question about one topic: the published entry is the answer, with no model call.
            await self._remember(command, resolved, quick_passage.text)
            return await self._finish(
                command,
                question,
                AnswerOutcome.QUICK_ANSWER,
                quick_passage.text,
                passages=[quick_passage],
                suggest_ticket=False,
            )

        query = SearchQuery.from_text(resolved.text, self._normalizer)
        passages = [] if query.is_empty else await self._select_passages(query)
        if not passages:
            return await self._finish(
                command,
                question,
                AnswerOutcome.INSUFFICIENT_INFORMATION,
                messages.INSUFFICIENT_INFORMATION,
                passages=[],
                suggest_ticket=True,
            )

        canary = self._canary_factory()
        persona = self._persona.text() if self._persona is not None else ""
        prompt = self._prompt_builder.build(question, passages, canary, persona, history)
        reserved = self._estimate_tokens(prompt)
        if not await self._budget.try_reserve(reserved):
            return await self._finish(
                command,
                question,
                AnswerOutcome.FALLBACK_BUDGET_EXHAUSTED,
                messages.FALLBACK_BUDGET_EXHAUSTED,
                passages=passages,
                suggest_ticket=True,
            )

        try:
            completion = await self._chat.complete(
                ChatCompletionRequest(messages=prompt, max_output_tokens=self._policy.max_output_tokens)
            )
        except AiProviderError as exc:
            await self._budget.release(reserved)
            logger.warning("assistant provider failure: %s", type(exc).__name__)
            return await self._finish(
                command,
                question,
                AnswerOutcome.FALLBACK_PROVIDER_UNAVAILABLE,
                messages.FALLBACK_PROVIDER_UNAVAILABLE,
                passages=passages,
                suggest_ticket=True,
            )

        await self._budget.settle(reserved, completion.usage.total)
        grounding = self._guard.evaluate(
            completion.text, passage_count=len(passages), canary=canary, leak_markers=PromptBuilder.LEAK_MARKERS
        )
        if grounding.kind is not GroundingKind.GROUNDED:
            if grounding.kind is GroundingKind.LEAK:
                logger.warning("assistant output withheld: prompt leak detected")
            return await self._finish(
                command,
                question,
                AnswerOutcome.INSUFFICIENT_INFORMATION,
                messages.INSUFFICIENT_INFORMATION,
                passages=[],
                suggest_ticket=True,
                usage=completion.usage,
            )

        cited = [passages[i - 1] for i in grounding.cited_indices]
        await self._remember(command, resolved, grounding.text)
        return await self._finish(
            command,
            question,
            AnswerOutcome.ANSWERED,
            grounding.text,
            passages=cited,
            suggest_ticket=False,
            usage=completion.usage,
        )

    async def _quick_passage(self, topic: QuickTopic | None) -> RetrievedPassage | None:
        """The published entry that answers `topic`; None if no topic or no such entry, and the normal flow follows."""
        if topic is None:
            return None
        title = self._normalizer.normalize(messages.QUICK_TOPIC_TITLES[topic])
        query = SearchQuery.from_text(messages.QUICK_TOPIC_TITLES[topic], self._normalizer)
        try:
            candidates = await self._select_passages(query)
        except Exception as exc:  # a shortcut must never turn a question into an error
            logger.warning("quick answer lookup failed: %s", type(exc).__name__)
            return None
        return next((p for p in candidates if self._normalizer.normalize(p.title) == title), None)

    async def _select_passages(self, query: SearchQuery) -> list[RetrievedPassage]:
        """A small knowledge base is sent whole; a large one goes through the relevance gate."""
        whole = await self._search.all_entries_if_small(
            query,
            max_entries=self._policy.whole_knowledge_max_entries,
            max_total_chars=self._policy.whole_knowledge_max_chars,
        )
        if whole:
            return whole
        candidates = await self._search.search(query, limit=self._policy.retrieval_limit)
        return [p for p in candidates if p.score >= self._policy.min_relevance]

    async def _recent_history(self, command: AskAssistantCommand) -> tuple[ConversationTurn, ...]:
        if self._context is None or command.conversation_id is None:
            return ()
        try:
            return await self._context.recent(command.conversation_id)
        except Exception as exc:  # the memory is a convenience: never fail a question because of it
            logger.warning("conversation context unavailable: %s", type(exc).__name__)
            return ()

    async def _remember(self, command: AskAssistantCommand, resolved: ResolvedQuery, answer: str) -> None:
        if self._context is None or command.conversation_id is None:
            return
        turn = ConversationTurn(
            question=resolved.text[-_REMEMBERED_QUESTION_CHARS:],
            answer=answer[:_REMEMBERED_ANSWER_CHARS],
        )
        try:
            await self._context.append(command.conversation_id, turn)
        except Exception as exc:
            logger.warning("conversation context not updated: %s", type(exc).__name__)

    async def _forget(self, command: AskAssistantCommand) -> None:
        if self._context is None or command.conversation_id is None:
            return
        try:
            await self._context.clear(command.conversation_id)
        except Exception as exc:
            logger.warning("conversation context not cleared: %s", type(exc).__name__)

    async def _enforce_limits(self, command: AskAssistantCommand) -> None:
        decision = await self._rate_limiter.hit(
            f"assistant:ip:{command.client_ip}", limit=self._policy.questions_per_ip_per_hour, window_seconds=3600
        )
        if not decision.allowed:
            raise RateLimitedError(
                "تعداد پرسش‌ها زیاد است. کمی بعد دوباره تلاش کنید.", retry_after_seconds=decision.retry_after_seconds
            )
        if command.conversation_id is not None:
            decision = await self._rate_limiter.hit(
                f"assistant:conv:{command.conversation_id}",
                limit=self._policy.questions_per_conversation,
                window_seconds=86400,
            )
            if not decision.allowed:
                raise RateLimitedError(
                    "این گفتگو به سقف تعداد پرسش رسیده است. لطفا گفتگوی جدید شروع کنید.",
                    retry_after_seconds=decision.retry_after_seconds,
                )

    def _estimate_tokens(self, prompt: Sequence[ChatMessage]) -> int:
        chars = sum(len(m.content) for m in prompt)
        return chars // _CHARS_PER_TOKEN + self._policy.max_output_tokens

    async def _finish(
        self,
        command: AskAssistantCommand,
        question: Question,
        outcome: AnswerOutcome,
        text: str,
        *,
        passages: list[RetrievedPassage],
        suggest_ticket: bool,
        usage: TokenUsage | None = None,
    ) -> SupportAnswer:
        now = self._clock.now()
        interaction_id = uuid.uuid4()
        shown = tuple(AnswerSource(title=p.title, url=p.url) for p in passages)
        interaction = AssistantInteraction(
            interaction_id=interaction_id,
            occurred_at=now,
            outcome=outcome,
            usage=usage or TokenUsage(),
            source_entry_ids=tuple(p.entry_id for p in passages),
            retention_until=now + timedelta(days=self._policy.interaction_retention_days),
            conversation_id=command.conversation_id,
            user_id=command.user_id if command.consent_to_store else None,
            question_text=question.text if command.consent_to_store else None,
            answer_text=text if command.consent_to_store else None,
        )
        try:
            await self._interactions.record(interaction)
        except Exception:
            logger.exception("assistant interaction could not be recorded")
        return SupportAnswer(
            text=text,
            outcome=outcome,
            sources=shown,
            suggest_ticket=suggest_ticket,
            interaction_id=interaction_id,
        )
