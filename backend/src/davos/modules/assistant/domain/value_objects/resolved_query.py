from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedQuery:
    """What the customer typed and the stand-alone question it stands for (equal unless it was a follow-up).

    ``needs_context`` says the message only makes sense next to an earlier one ("و برای روز تعطیل؟").
    ``is_follow_up`` says it was joined to that earlier question. A message that needs context but has none is a
    fragment whose meaning nobody can know, so whatever the model guessed for it must not be kept and served to the
    next person who types the same words.
    """

    original: str
    text: str
    is_follow_up: bool
    needs_context: bool = False
