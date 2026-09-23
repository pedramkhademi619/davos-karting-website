from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


@dataclass(frozen=True)
class CacheProbe:
    """Everything worked out about a question before the cache is asked, reused when its answer is stored.

    ``fingerprint`` is taken *before* the model is called: if the knowledge or style notes change while it thinks, the
    new entry carries the old fingerprint and is simply never served.
    """

    text: str
    embedding: QueryEmbedding
    signature: str
    fingerprint: str
