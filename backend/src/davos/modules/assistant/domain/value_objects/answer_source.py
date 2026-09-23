from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerSource:
    title: str
    url: str
