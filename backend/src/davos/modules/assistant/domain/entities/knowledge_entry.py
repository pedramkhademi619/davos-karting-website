from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.errors.invalid_knowledge_entry_error import InvalidKnowledgeEntryError

MAX_BODY_CHARS = 4000


@dataclass(frozen=True)
class KnowledgeEntry:
    """One approved, public piece of content that the assistant may quote.

    The entry is created only from *published* content; unpublishing removes it from the index.
    """

    entry_id: uuid.UUID
    source_type: KnowledgeSourceType
    source_ref: str
    title: str
    body: str
    url: str
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        source_type: KnowledgeSourceType,
        source_ref: str,
        title: str,
        body: str,
        url: str,
        now: datetime,
    ) -> KnowledgeEntry:
        source_ref = source_ref.strip()
        if not source_ref:
            raise InvalidKnowledgeEntryError("عنوان، متن و شناسه منبع الزامی است.")
        title, body, url = cls._checked(title, body, url)
        return cls(uuid.uuid4(), source_type, source_ref, title, body, url, now)

    def revise(
        self, *, source_type: KnowledgeSourceType, title: str, body: str, url: str, now: datetime
    ) -> KnowledgeEntry:
        """The same entry (same id and reference) with new content, held to the same rules as a new one."""
        title, body, url = self._checked(title, body, url)
        return replace(self, source_type=source_type, title=title, body=body, url=url, updated_at=now)

    @staticmethod
    def _checked(title: str, body: str, url: str) -> tuple[str, str, str]:
        title, body, url = title.strip(), body.strip(), url.strip()
        if not title or not body:
            raise InvalidKnowledgeEntryError("عنوان، متن و شناسه منبع الزامی است.")
        if len(body) > MAX_BODY_CHARS:
            raise InvalidKnowledgeEntryError("متن پایگاه دانش بیش از حد طولانی است.")
        if not url.startswith("/") or url.startswith("//"):
            raise InvalidKnowledgeEntryError("پیوند منبع باید یک مسیر داخلی سایت باشد.", code="invalid_source_url")
        return title, body, url
