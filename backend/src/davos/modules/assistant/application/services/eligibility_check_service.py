from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import replace

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.services.eligibility_advisor import EligibilityAdvisor
from davos.modules.assistant.domain.services.party_facts_extractor import PartyFactsExtractor
from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn
from davos.modules.assistant.domain.value_objects.eligibility_rules import EligibilityRules
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage

CHECK_ENTRY_ID = uuid.UUID("5a1e7c0d-0000-4000-8000-00000000c4ec")
CHECK_TITLE = "بررسی شرایط شما با قوانین مجموعه"
CHECK_URL = "/faq"


class EligibilityCheckService:
    """Turns the rule checks for one question into a passage the model can cite.

    Language models are unreliable at "is ۱۴۰ more than ۱۴۰" or "۶۵ + ۶۵ < ۱۳۰", and at planning sessions for a group.
    Code does those comparisons; the model only has to explain the verdict in friendly words. Facts said in the previous
    question count too, so "قدش ۱۵۰ـه" after "پسرم ۱۲ سالشه" is checked as one party.
    """

    def __init__(self, extractor: PartyFactsExtractor | None = None, rules: EligibilityRules | None = None) -> None:
        self._extractor = extractor or PartyFactsExtractor()
        self._rules = rules or EligibilityRules()

    def passage(
        self, question: str, history: Sequence[ConversationTurn] = (), booking: BookingFacts | None = None
    ) -> RetrievedPassage | None:
        """``booking`` carries the admin panel's kart counts and booking days; without it the defaults apply."""
        facts = self._extractor.extract(question)
        if facts.is_empty:
            return None
        if history and not facts.ages and not facts.group_size:
            # a follow-up that adds a detail ("قدش ۱۵۰ـه"): check it together with the people named just before
            earlier = self._extractor.extract(history[-1].question)
            if earlier.ages or earlier.group_size:
                facts = replace(
                    earlier,
                    height_cm=facts.height_cm or earlier.height_cm,
                    weekday=facts.weekday if facts.weekday is not None else earlier.weekday,
                    weekday_name=facts.weekday_name or earlier.weekday_name,
                    at=facts.at or earlier.at,
                    weights_kg=facts.weights_kg or earlier.weights_kg,
                    has_licence=facts.has_licence if facts.has_licence is not None else earlier.has_licence,
                    mentions_two_seater=facts.mentions_two_seater or earlier.mentions_two_seater,
                    mentions_today=facts.mentions_today,
                    mentions_booking=facts.mentions_booking,
                )
        rules = self._rules.for_booking(booking) if booking is not None else self._rules
        lines = EligibilityAdvisor(rules).advise(facts)
        if not lines:
            return None
        return RetrievedPassage(
            entry_id=CHECK_ENTRY_ID,
            source_type=KnowledgeSourceType.POLICY,
            title=CHECK_TITLE,
            text="\n".join(f"- {line}" for line in lines),
            url=CHECK_URL,
            score=1.0,
            computed=True,
        )
