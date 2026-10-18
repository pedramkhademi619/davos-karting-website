from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunConfig:
    """The model and how it is called; the rest of the pipeline is exactly production's."""

    model: str
    token_limit_param: str = "max_tokens"  # noqa: S105 - JSON field name, not a secret
    send_temperature: bool = True
    min_output_tokens: int = 0
    timeout_seconds: float = 12.0
    repeats: int = 1
    concurrency: int = 4
    label: str = ""
    judge_repeats: int = 1  # the judge reads the replies of the first repeats only (it costs more than the answers)
    support_check: bool = True  # the production setting AI_SUPPORT_CHECK_ENABLED; off to measure what it adds
    max_cost_usd: float = 1.0  # stop scheduling questions once the provider-reported spend passes this
