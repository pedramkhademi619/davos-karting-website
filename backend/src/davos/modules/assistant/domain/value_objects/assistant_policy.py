from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantPolicy:
    """Limits and tuning for answering questions.

    The first group comes from the settings (ASSISTANT_*, AI_*), built in the composition root. The second group are
    design constants of the retrieval pipeline, measured with the evaluation (docs/ASSISTANT_EVALUATION.md); they are
    not deployment settings, so they keep their values here.
    """

    max_question_chars: int
    max_output_tokens: int
    temperature: float
    questions_per_ip_per_hour: int
    questions_per_conversation: int
    interaction_retention_days: int

    retrieval_limit: int = 4
    min_relevance: float = 0.3
    max_passage_chars: int = 4000  # equal to the largest allowed entry, so a stored fact is never silently cut
    max_answer_chars: int = 900
    whole_knowledge_max_entries: int = 12
    whole_knowledge_max_chars: int = 8000
