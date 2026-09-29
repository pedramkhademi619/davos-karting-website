from __future__ import annotations

from pathlib import Path

from davos.modules.assistant.adapters.knowledge.text_file_knowledge_source import TextFileKnowledgeSource
from davos.modules.assistant.adapters.persona.file_assistant_persona import FileAssistantPersona
from davos.modules.assistant.application.ports.ai_provider_rejected_error import AiProviderRejectedError
from davos.tools.assistant_eval.eval_case import EvalCase
from davos.tools.assistant_eval.eval_report import EvalReport
from davos.tools.assistant_eval.eval_runner import EvalRunner
from davos.tools.assistant_eval.expectation_kind import ExpectationKind
from davos.tools.assistant_eval.file_knowledge_search import FileKnowledgeSearch
from davos.tools.assistant_eval.fixed_booking_facts import FixedBookingFacts
from davos.tools.assistant_eval.run_config import RunConfig
from tests.fakes.scripted_ai_chat import ScriptedAiChat
from tests.fakes.standard_config import assistant_policy, booking_facts

BACKEND = Path(__file__).resolve().parents[3]
YES_CASE = EvalCase("y", "single_seater", "من ۲۵ سالمه، میتونم تک نفره سوار بشم؟", ExpectationKind.YES)
HELLO = EvalCase("h", "small_talk", "سلام", ExpectationKind.SMALL_TALK)


def runner(chat: ScriptedAiChat, **config: object) -> EvalRunner:
    return EvalRunner(
        config=RunConfig(model="fake-model", **config),  # type: ignore[arg-type]
        chat=chat,
        search=FileKnowledgeSearch(TextFileKnowledgeSource(BACKEND / "knowledge")),
        persona=FileAssistantPersona(str(BACKEND / "prompts" / "assistant_persona.txt")),
        booking_facts=FixedBookingFacts(booking_facts()),
        policy=assistant_policy(),
    )


async def test_cases_run_through_the_real_pipeline_and_are_graded() -> None:
    chat = ScriptedAiChat("آره، می‌تونید تک‌نفره سوار بشید [1].")
    runs = await runner(chat, repeats=2).run([YES_CASE, HELLO])
    assert [r.grade.passed for r in runs] == [True, True, True, True]
    assert chat.calls == 2  # the greeting never reaches the model
    # the published knowledge rides in the system message, the question in the user message
    assert "خودرو تک‌نفره و شرایط سنی" in chat.system_prompt and "۲۵ سالمه" in chat.user_prompt
    summary = EvalReport(runs, RunConfig(model="fake-model", repeats=2), {"date": "d"}).summary()
    assert summary["pass_rate"] == 1.0 and summary["pass_all_repeats"] == 1.0


async def test_a_rejected_request_stops_the_run_instead_of_filling_the_report_with_failures() -> None:
    chat = ScriptedAiChat(AiProviderRejectedError(403))
    evaluation = runner(chat, repeats=3, concurrency=1)
    runs = await evaluation.run([YES_CASE, YES_CASE, YES_CASE])
    assert len(runs) == 1 and not runs[0].grade.passed
    assert "rejected" in evaluation.aborted
