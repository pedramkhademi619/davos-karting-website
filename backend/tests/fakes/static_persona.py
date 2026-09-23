from __future__ import annotations

from davos.modules.assistant.application.ports.assistant_persona_port import AssistantPersonaPort


class StaticPersona(AssistantPersonaPort):
    def __init__(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text
