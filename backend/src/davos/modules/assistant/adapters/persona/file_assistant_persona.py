from __future__ import annotations

import logging
import re
from pathlib import Path

from davos.modules.assistant.application.messages import assistant_messages as messages
from davos.modules.assistant.application.ports.assistant_persona_port import AssistantPersonaPort

logger = logging.getLogger(__name__)

MAX_PERSONA_CHARS = 2000
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class FileAssistantPersona(AssistantPersonaPort):
    """Style notes from a plain text file that the owner edits.

    * lines starting with ``#`` are comments for the editor and never reach the model,
    * the file is read again whenever it changes, so edits apply without a restart,
    * no path configured, or a missing/unreadable file, means the built-in default notes; an existing but empty file
      means "no extra notes",
    * the text is length-limited and stripped of control characters; its content is never logged.
    """

    def __init__(self, path: str, *, default: str = messages.DEFAULT_PERSONA) -> None:
        self._path = Path(path) if path else None
        self._default = default
        self._text: str | None = None
        self._stamp: tuple[int, int] | None = None
        self._warned = False

    def text(self) -> str:
        if self._path is None:
            return self._default
        try:
            stat = self._path.stat()
        except OSError:
            return self._fallback("persona file is missing or unreadable, using the built-in notes")
        stamp = (stat.st_mtime_ns, stat.st_size)
        if self._text is None or stamp != self._stamp:
            loaded = self._load(self._path)
            if loaded is None:
                return self._fallback("persona file could not be decoded, using the built-in notes")
            self._text, self._stamp, self._warned = loaded, stamp, False
        return self._text

    def _load(self, path: Path) -> str | None:
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            return None
        kept = [line.rstrip() for line in raw.splitlines() if not line.lstrip().startswith("#")]
        cleaned = _CONTROL_CHARACTERS.sub("", "\n".join(kept)).strip()
        if len(cleaned) > MAX_PERSONA_CHARS:
            logger.warning("persona file is longer than %d characters, the rest is ignored", MAX_PERSONA_CHARS)
            cleaned = cleaned[:MAX_PERSONA_CHARS].rstrip()
        return cleaned

    def _fallback(self, warning: str) -> str:
        if not self._warned:
            logger.warning(warning)
            self._warned = True
        return self._default
