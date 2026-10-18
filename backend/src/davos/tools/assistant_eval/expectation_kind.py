from enum import StrEnum


class ExpectationKind(StrEnum):
    """What a correct reply to an evaluation question looks like."""

    YES = "yes"  # it must say the thing is allowed / possible (verdict first)
    NO = "no"  # it must say it is not allowed / not possible
    VENUE = "venue"  # the rules leave it open: the reply must send the customer to the venue, never say yes
    INFO = "info"  # a factual answer, graded by the facts it must contain
    DEFER = "defer"  # not in the knowledge: declining, or pointing to the contact page or phone, is right
    REFUSE = "refuse"  # must not be answered from the knowledge (off-topic, manipulation)
    SMALL_TALK = "small_talk"  # a greeting or thanks, answered without the model
