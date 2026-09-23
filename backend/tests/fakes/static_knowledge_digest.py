from __future__ import annotations

from davos.modules.assistant.application.ports.knowledge_digest_port import KnowledgeDigestPort


class StaticKnowledgeDigest(KnowledgeDigestPort):
    """A digest tests can change by hand, to stand in for an edited knowledge file."""

    def __init__(self, value: str = "digest-1") -> None:
        self.value = value

    async def current(self) -> str:
        return self.value
