from __future__ import annotations

from pathlib import Path

from davos.modules.assistant.application.ports.knowledge_document_batch import KnowledgeDocumentBatch
from davos.modules.assistant.application.ports.knowledge_document_problem import KnowledgeDocumentProblem
from davos.modules.assistant.application.ports.knowledge_document_source_port import KnowledgeDocumentSourcePort
from davos.modules.assistant.application.ports.knowledge_source_unavailable_error import KnowledgeSourceUnavailableError
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.knowledge_document import KnowledgeDocument

MAX_FILE_BYTES = 64 * 1024
_HEADER_KEYS = ("title", "url", "type", "status")


class TextFileKnowledgeSource(KnowledgeDocumentSourcePort):
    """Knowledge written as one plain ``.txt`` file per topic in a folder.

    A file is a short header, a blank line, then the text the assistant may quote::

        # lines starting with # are notes for the editor
        title: چطور نوبت رزرو کنم؟
        url: /faq
        type: faq            (optional: faq, policy, service, pricing or contact; default faq)
        status: published    (optional: use draft to keep it on file without the assistant quoting it)

        The text of the answer, in plain sentences.

    The file name (without ``.txt``) is the document's identity: renaming a file removes one document and adds another.
    """

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)

    def read_all(self) -> KnowledgeDocumentBatch:
        if not self._directory.is_dir():
            raise KnowledgeSourceUnavailableError(f"{self._directory} is not a readable folder")
        documents: list[KnowledgeDocument] = []
        problems: list[KnowledgeDocumentProblem] = []
        for path in sorted(self._directory.glob("*.txt")):
            try:
                documents.append(self._parse(path))
            except (ValueError, OSError) as exc:
                problems.append(KnowledgeDocumentProblem(path.stem, str(exc)))
        return KnowledgeDocumentBatch(tuple(documents), tuple(problems))

    @staticmethod
    def _parse(path: Path) -> KnowledgeDocument:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("حجم فایل بیشتر از ۶۴ کیلوبایت است.")
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeDecodeError:
            raise ValueError("فایل باید متن UTF-8 باشد.") from None

        index = 0
        while index < len(lines) and not lines[index].strip():
            index += 1
        header: dict[str, str] = {}
        while index < len(lines) and lines[index].strip():
            line = lines[index].strip()
            index += 1
            if line.startswith("#"):
                continue
            key, colon, value = line.partition(":")
            key = key.strip().lower()
            if not colon:
                raise ValueError("خط‌های بالای فایل باید به شکل «title: ...» باشند و بین آن‌ها و متن یک خط خالی بماند.")
            if key not in _HEADER_KEYS:
                raise ValueError(f"کلید «{key}» شناخته‌شده نیست؛ فقط {', '.join(_HEADER_KEYS)} مجاز است.")
            header[key] = value.strip()

        body = "\n".join(lines[index:]).strip()
        title, url = header.get("title", ""), header.get("url", "")
        if not title:
            raise ValueError("خط «title:» الزامی است.")
        if not url:
            raise ValueError("خط «url:» الزامی است (صفحه‌ای از سایت، مثل /faq).")
        if not body:
            raise ValueError("متن زیر خط‌های بالای فایل خالی است.")
        try:
            source_type = KnowledgeSourceType(header.get("type", "faq").lower())
        except ValueError:
            allowed = ", ".join(kind.value for kind in KnowledgeSourceType)
            raise ValueError(f"مقدار type باید یکی از این‌ها باشد: {allowed}.") from None
        status = header.get("status", "published").lower()
        if status not in {"published", "draft"}:
            raise ValueError("مقدار status باید published یا draft باشد.")
        return KnowledgeDocument(path.stem, source_type, title, url, body, published=status == "published")
