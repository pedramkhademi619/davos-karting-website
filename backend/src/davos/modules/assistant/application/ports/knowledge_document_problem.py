from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeDocumentProblem:
    """A document that could not be used, with a reason a non-programmer can act on."""

    name: str
    reason: str
