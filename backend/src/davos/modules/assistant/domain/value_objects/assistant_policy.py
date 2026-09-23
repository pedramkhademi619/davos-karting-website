from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantPolicy:
    max_question_chars: int = 500
    retrieval_limit: int = 4
    min_relevance: float = 0.3
    max_passage_chars: int = 4000  # equal to the largest allowed entry, so a stored fact is never silently cut
    max_answer_chars: int = 900
    max_output_tokens: int = 400
    questions_per_ip_per_hour: int = 30
    questions_per_conversation: int = 20
    interaction_retention_days: int = 90
    whole_knowledge_max_entries: int = 12
    whole_knowledge_max_chars: int = 8000
