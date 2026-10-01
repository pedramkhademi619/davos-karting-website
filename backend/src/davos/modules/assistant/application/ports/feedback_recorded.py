from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackRecorded:
    """The vote was stored. ``cache_entry_id`` is the stored answer this reply came from or was saved as, if any."""

    cache_entry_id: uuid.UUID | None
