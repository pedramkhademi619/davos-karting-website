from dataclasses import dataclass

from davos.modules.assistant.domain.enums.grounding_kind import GroundingKind


@dataclass(frozen=True)
class GroundingResult:
    kind: GroundingKind
    text: str = ""
    cited_indices: tuple[int, ...] = ()
