from dataclasses import dataclass

from davos.modules.assistant.domain.enums.chat_role import ChatRole


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str
