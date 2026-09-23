from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationTurn:
    """One exchange kept for follow-up questions: the stand-alone form of the question, and the answer given."""

    question: str
    answer: str
