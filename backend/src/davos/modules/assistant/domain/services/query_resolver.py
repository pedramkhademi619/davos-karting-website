from __future__ import annotations

from collections.abc import Sequence

from davos.modules.assistant.domain.services.follow_up_detector import FollowUpDetector
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn
from davos.modules.assistant.domain.value_objects.resolved_query import ResolvedQuery

_CONTEXT_CHARS = 200
_JOINER = " — "


class QueryResolver:
    """Turns a follow-up into a stand-alone question before the cache lookup, without calling a model.

    "هزینه‌ش چقدره؟" asked after "دو نفره چیه؟" becomes "دو نفره چیه؟ — هزینه‌ش چقدره؟". Storing the bare fragment would
    make the cache answer the next customer's "هزینه‌ش چقدره؟" about a different subject with this one's answer. A
    fragment with nothing to lean on is reported as such (``needs_context`` without ``is_follow_up``) so it is never
    cached.
    """

    def __init__(self, follow_ups: FollowUpDetector | None = None) -> None:
        self._follow_ups = follow_ups or FollowUpDetector()

    def resolve(self, text: str, history: Sequence[ConversationTurn]) -> ResolvedQuery:
        needs_context = self._follow_ups.is_follow_up(text)
        if not history or not needs_context:
            return ResolvedQuery(original=text, text=text, is_follow_up=False, needs_context=needs_context)
        subject = history[-1].question[-_CONTEXT_CHARS:].strip()
        return ResolvedQuery(original=text, text=f"{subject}{_JOINER}{text}", is_follow_up=True, needs_context=True)
