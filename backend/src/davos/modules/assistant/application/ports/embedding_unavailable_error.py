class EmbeddingUnavailableError(Exception):
    """The embedding model cannot serve a request right now (not loaded, files missing, inference failed)."""
