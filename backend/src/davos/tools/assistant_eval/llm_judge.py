from __future__ import annotations

import json
import re

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.enums.chat_role import ChatRole
from davos.modules.assistant.domain.value_objects.chat_message import ChatMessage
from davos.tools.assistant_eval.eval_case import EvalCase
from davos.tools.assistant_eval.judge_verdict import JudgeVerdict

_INSTRUCTIONS = """You grade replies of a customer-service assistant for a go-kart track in Iran.
The assistant must answer only from the KNOWLEDGE below (published texts, the live booking settings and the
owner's riding rules), in natural, polite, colloquial Persian, verdict first, usually 2-4 sentences, and say it
does not know when the knowledge does not cover the question. You get the question (and earlier questions of the
same conversation), the reply, and the label a human wrote for this question (EXPECTED). Judge four things
independently, each strictly true or false:

- correct: the decision (yes / no / "ask the venue") and every number match the knowledge and EXPECTED.
- faithful: every claim in the reply is supported by the knowledge; no invented facts, prices, rules or promises.
- helpful: it answers exactly what was asked, the verdict comes first, and when the answer is no it offers the allowed
  alternative that the knowledge gives for that person (for example the rear seat of the two-seater for a child).
- natural: it reads like a friendly person at the counter: natural Persian, no stiff template, no repeated question,
  no needless clarifying question when the message already says it.

Ignore the bracketed source numbers like [1]. Reply with JSON only:
{"correct": true, "faithful": true, "helpful": true, "natural": true, "rationale": "one short English sentence"}"""

_JSON = re.compile(r"\{.*\}", re.DOTALL)


class LlmJudge:
    """LLM-as-judge with binary criteria and the human label as reference (a stronger model of another family than
    the one evaluated, to limit self-preference). It complements the keyword grader; it does not replace it, and the
    report shows where the two disagree so those replies can be read by a person."""

    def __init__(self, chat: AIChatPort, knowledge: str) -> None:
        self._chat = chat
        self._knowledge = knowledge
        self.cost_usd = 0.0  # provider-reported spend of the judge's own calls

    async def judge(self, case: EvalCase, reply: str) -> JudgeVerdict | None:
        history = "\n".join(f"- {h}" for h in case.history) or "(none)"
        expected = f"{case.kind.value}; must mention: {case.must or '-'}; must not say: {case.never or '-'}"
        if case.note:
            expected += f"; note: {case.note}"
        user = (
            f"KNOWLEDGE:\n{self._knowledge}\n\nEARLIER QUESTIONS:\n{history}\n\nQUESTION:\n{case.question}\n\n"
            f"EXPECTED:\n{expected}\n\nREPLY:\n{reply}"
        )
        request = ChatCompletionRequest(
            messages=(ChatMessage(ChatRole.SYSTEM, _INSTRUCTIONS), ChatMessage(ChatRole.USER, user)),
            max_output_tokens=2000,  # reasoning judges think inside this limit
            temperature=0.0,
        )
        try:
            completion = await self._chat.complete(request)
        except AiProviderError:
            return None
        self.cost_usd += completion.cost_usd or 0.0
        match = _JSON.search(completion.text)
        if match is None:
            return None
        try:
            data = json.loads(match.group(0))
        except ValueError:
            return None
        return JudgeVerdict(
            correct=data.get("correct") is True,
            faithful=data.get("faithful") is True,
            helpful=data.get("helpful") is True,
            natural=data.get("natural") is True,
            rationale=str(data.get("rationale", ""))[:300],
        )
