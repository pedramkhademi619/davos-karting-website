from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelCall:
    """One provider call made while answering a question (the answer itself or a citation repair)."""

    model: str
    prompt_tokens: int
    cached_prompt_tokens: int
    completion_tokens: int
    cost_usd: float | None
    latency_s: float
    failed: bool = False
    error: str = ""  # the port error's class name when the call failed
