from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import replace

from davos.modules.assistant.adapters.budget.in_memory_ai_budget import InMemoryAiBudget
from davos.modules.assistant.adapters.context.in_memory_conversation_context import InMemoryConversationContext
from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.assistant_persona_port import AssistantPersonaPort
from davos.modules.assistant.application.ports.booking_facts_port import BookingFactsPort
from davos.modules.assistant.application.ports.knowledge_search_port import KnowledgeSearchPort
from davos.modules.assistant.application.use_cases.ask_assistant_command import AskAssistantCommand
from davos.modules.assistant.application.use_cases.ask_assistant_use_case import AskAssistantUseCase
from davos.modules.assistant.domain.value_objects.assistant_policy import AssistantPolicy
from davos.platform.clock.system_clock import SystemClock
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from davos.tools.assistant_eval.case_grader import CaseGrader
from davos.tools.assistant_eval.case_run import CaseRun
from davos.tools.assistant_eval.eval_case import EvalCase
from davos.tools.assistant_eval.llm_judge import LlmJudge
from davos.tools.assistant_eval.metered_ai_chat import MeteredAiChat
from davos.tools.assistant_eval.null_interaction_log import NullInteractionLog
from davos.tools.assistant_eval.run_config import RunConfig

_EVAL_IP = "203.0.113.10"  # documentation range; the per-IP limit is lifted for the evaluation


class EvalRunner:
    """Runs every case through a fresh AskAssistantUseCase wired like production (same prompt, persona, rule checks,
    live-settings passage, grounding guard, citation repair and conversation memory), with in-memory stand-ins for
    the database, Redis and the admin panel. Earlier questions of a case are asked first in the same conversation."""

    def __init__(
        self,
        *,
        config: RunConfig,
        chat: AIChatPort,
        search: KnowledgeSearchPort,
        persona: AssistantPersonaPort,
        booking_facts: BookingFactsPort,
        policy: AssistantPolicy,
        judge: LlmJudge | None = None,
        grader: CaseGrader | None = None,
        progress: Callable[[CaseRun], None] | None = None,
    ) -> None:
        self._config = config
        self._chat = chat
        self._search = search
        self._persona = persona
        self._booking_facts = booking_facts
        # production's policy, with the per-IP and per-conversation limits lifted for the evaluation
        self._policy = replace(policy, questions_per_ip_per_hour=1_000_000, questions_per_conversation=1_000)
        self._judge = judge
        self._grader = grader or CaseGrader()
        self._progress = progress
        self._clock = SystemClock()
        self._spent = 0.0
        self.aborted = ""  # why the run stopped early, empty when it ran to the end

    async def run(self, cases: Sequence[EvalCase]) -> list[CaseRun]:
        gate = asyncio.Semaphore(self._config.concurrency)
        runs: list[CaseRun] = []
        for repeat in range(1, self._config.repeats + 1):

            async def one(case: EvalCase, repeat: int = repeat) -> CaseRun | None:
                async with gate:
                    if self.aborted:
                        return None
                    run = await self._run_case(case, repeat)
                    self._account(run)
                if self._progress is not None:
                    self._progress(run)
                return run

            runs.extend(r for r in await asyncio.gather(*(one(c) for c in cases)) if r is not None)
            if self.aborted:
                break
        return runs

    def _account(self, run: CaseRun) -> None:
        """Stops the run instead of filling a report with failures: a rejected request (bad key, unknown model, no
        credit left) will not heal by retrying, and the spend cap protects the provider account."""
        self._spent += sum(c.cost_usd or 0.0 for c in run.calls)
        if any(c.error == "AiProviderRejectedError" for c in run.calls):
            self.aborted = "the provider rejected a request (credentials, model id or account credit)"
        judge_spent = self._judge.cost_usd if self._judge is not None else 0.0
        if self._spent + judge_spent > self._config.max_cost_usd:
            self.aborted = f"spend cap of ${self._config.max_cost_usd:.2f} reached"

    @property
    def spent_usd(self) -> float:
        return self._spent + (self._judge.cost_usd if self._judge is not None else 0.0)

    async def _run_case(self, case: EvalCase, repeat: int) -> CaseRun:
        context = InMemoryConversationContext(self._clock, max_turns=4, ttl_seconds=3600)
        conversation = uuid.uuid4()
        for earlier in case.history:
            await self._use_case(self._chat, context).execute(self._command(earlier, conversation))
        metered = MeteredAiChat(self._chat, self._config.model)
        started = time.monotonic()
        answer = await self._use_case(metered, context).execute(self._command(case.question, conversation))
        latency = time.monotonic() - started
        grade = self._grader.grade(case, answer.outcome, answer.text)
        verdict = None
        judged = self._judge is not None and repeat <= self._config.judge_repeats
        if judged and self._judge is not None and metered.calls and not any(c.failed for c in metered.calls):
            verdict = await self._judge.judge(case, answer.text)
        return CaseRun(
            case=case,
            repeat=repeat,
            answer=answer.text,
            outcome=answer.outcome.value,
            grade=grade,
            calls=tuple(metered.calls),
            latency_s=latency,
            judge=verdict,
        )

    def _use_case(self, chat: AIChatPort, context: InMemoryConversationContext) -> AskAssistantUseCase:
        return AskAssistantUseCase(
            search=self._search,
            chat=chat,
            budget=InMemoryAiBudget(daily_limit=100_000_000, clock=self._clock),
            interactions=NullInteractionLog(),
            rate_limiter=InMemoryRateLimiter(self._clock),
            clock=self._clock,
            policy=self._policy,
            persona=self._persona,
            context=context,
            booking_facts=self._booking_facts,
        )

    @staticmethod
    def _command(text: str, conversation: uuid.UUID) -> AskAssistantCommand:
        return AskAssistantCommand(text=text, client_ip=_EVAL_IP, conversation_id=conversation)
