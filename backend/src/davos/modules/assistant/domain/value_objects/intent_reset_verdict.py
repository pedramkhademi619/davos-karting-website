from dataclasses import dataclass


@dataclass(frozen=True)
class IntentResetVerdict:
    """``reset`` says the customer asked to drop the conversation so far; ``remainder`` is what they asked besides."""

    reset: bool
    remainder: str = ""
