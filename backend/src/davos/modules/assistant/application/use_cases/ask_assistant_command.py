import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AskAssistantCommand:
    text: str
    client_ip: str
    conversation_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    consent_to_store: bool = False
