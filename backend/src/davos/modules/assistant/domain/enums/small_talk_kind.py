from enum import StrEnum


class SmallTalkKind(StrEnum):
    GREETING = "greeting"
    GREETING_AND_HOW_ARE_YOU = "greeting_and_how_are_you"
    HOW_ARE_YOU = "how_are_you"
    THANKS = "thanks"
    ACKNOWLEDGEMENT = "acknowledgement"
    GOODBYE = "goodbye"
    IDENTITY = "identity"
