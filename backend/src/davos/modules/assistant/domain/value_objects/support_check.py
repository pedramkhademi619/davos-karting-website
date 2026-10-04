from __future__ import annotations

from dataclasses import dataclass, field

from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage


@dataclass(frozen=True)
class SupportCheck:
    """Whether the cited sources back the answer, and what the check itself consumed."""

    supported: bool
    usage: TokenUsage = field(default_factory=TokenUsage)
