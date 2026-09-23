import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SpendPointsCommand:
    customer_id: uuid.UUID
    points: int
    source_ref: str
    reason: str
