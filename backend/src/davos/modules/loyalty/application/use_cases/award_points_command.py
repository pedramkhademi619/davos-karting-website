import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AwardPointsCommand:
    customer_id: uuid.UUID
    points: int
    source_ref: str
    reason: str
    expires_in_days: int | None = None
