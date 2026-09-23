"""The content that ships in the repository (backend/knowledge and backend/prompts) must always be loadable and safe."""

from __future__ import annotations

from pathlib import Path

from davos.modules.assistant.adapters.knowledge.text_file_knowledge_source import TextFileKnowledgeSource
from davos.modules.assistant.adapters.persona.file_assistant_persona import MAX_PERSONA_CHARS, FileAssistantPersona
from davos.modules.assistant.application.messages.assistant_messages import QUICK_TOPIC_TITLES
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from tests.fakes.fixed_clock import FixedClock

BACKEND = Path(__file__).resolve().parents[3]
KNOWLEDGE = BACKEND / "knowledge"
PERSONA = BACKEND / "prompts" / "assistant_persona.txt"

# The website's placeholder contact line. It is a sample, not a real number, so it must never be quoted to a customer.
PLACEHOLDER_PHONE = "021-12345678"


def test_every_shipped_knowledge_file_parses_without_problems() -> None:
    batch = TextFileKnowledgeSource(KNOWLEDGE).read_all()
    assert batch.problems == (), [(p.name, p.reason) for p in batch.problems]
    assert batch.documents, "the assistant would know nothing"


def test_every_published_document_is_a_valid_knowledge_entry() -> None:
    now = FixedClock().now()
    for doc in TextFileKnowledgeSource(KNOWLEDGE).read_all().documents:
        if doc.published:
            KnowledgeEntry.create(
                source_type=doc.source_type, source_ref=doc.ref, title=doc.title, body=doc.body, url=doc.url, now=now
            )


def test_the_placeholder_phone_number_is_never_published() -> None:
    leaks = [
        d.ref
        for d in TextFileKnowledgeSource(KNOWLEDGE).read_all().documents
        if d.published and PLACEHOLDER_PHONE in d.body
    ]
    assert leaks == [], f"unverified sample data is published: {leaks}"


def test_the_shipped_style_notes_load_and_fit() -> None:
    text = FileAssistantPersona(str(PERSONA)).text()
    assert text and len(text) <= MAX_PERSONA_CHARS
    assert "#" not in text  # comment lines were stripped


def test_every_quick_answer_topic_has_a_published_entry_with_that_title() -> None:
    """A renamed or unpublished entry would silently turn its quick answer off; this makes that visible."""
    normalize = PersianTextNormalizer().normalize
    published = {normalize(d.title) for d in TextFileKnowledgeSource(KNOWLEDGE).read_all().documents if d.published}
    missing = [topic.value for topic, title in QUICK_TOPIC_TITLES.items() if normalize(title) not in published]
    assert missing == [], f"no published knowledge entry has the title of quick topics: {missing}"
