class EmbeddingUnavailableError(Exception):
    """The local embedding model is missing, still loading or failed; the cache then steps aside for that question."""
