from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(self.prompt_tokens + other.prompt_tokens, self.completion_tokens + other.completion_tokens)
