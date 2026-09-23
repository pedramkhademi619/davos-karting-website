from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedding(EmbeddingPort):
    """Runs a sentence-transformers model on this machine's CPU. Nothing here ever touches the network.

    * One instance per process (the container owns it), so the model is loaded once and shared by every request.
    * The model loads in a background thread (``warm_up``); until it is ready ``embed_query`` raises
      ``EmbeddingUnavailableError`` and the cache steps aside, so start-up and the first requests are never blocked.
    * All inference runs on one dedicated worker thread: the event loop stays free, and torch is never entered twice
      at the same time.
    * Recently embedded texts are kept in a small LRU, so a repeated question costs no inference at all.

    ``model_path`` is a local folder (see ``python -m davos.tools.fetch_embedding_model``). E5 models expect the
    ``query: `` prefix on both sides of a similarity comparison.
    """

    def __init__(
        self,
        *,
        model_path: str,
        model_name: str,
        dimension: int,
        threads: int = 2,
        lru_size: int = 1024,
        prefix: str = "query: ",
    ) -> None:
        self._model_path = model_path
        self._model_name = model_name
        self._dimension = dimension
        self._threads = threads
        self._lru_size = lru_size
        self._prefix = prefix
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="embedding")
        self._model: Any = None
        self._loading: asyncio.Task[None] | None = None
        self._failure: str | None = None
        self._lru: OrderedDict[str, QueryEmbedding] = OrderedDict()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    async def warm_up(self) -> None:
        """Loads the model once; never raises (a failure is remembered and the cache simply stays off)."""
        if self._model is not None or self._failure is not None:
            return
        if self._loading is None:
            self._loading = asyncio.create_task(self._load(), name="embedding-model-load")
        await asyncio.shield(self._loading)

    async def embed_query(self, text: str) -> QueryEmbedding:
        cached = self._lru.get(text)
        if cached is not None:
            self._lru.move_to_end(text)
            return cached
        if self._model is None:
            if self._loading is None and self._failure is None:
                self._loading = asyncio.create_task(self._load(), name="embedding-model-load")
            raise EmbeddingUnavailableError(self._failure or "the embedding model is still loading")
        loop = asyncio.get_running_loop()
        values = await loop.run_in_executor(self._executor, self._encode, text)
        embedding = QueryEmbedding(values=values, model=self._model_name)
        self._lru[text] = embedding
        if len(self._lru) > self._lru_size:
            self._lru.popitem(last=False)
        return embedding

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    async def _load(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            self._model = await loop.run_in_executor(self._executor, self._load_blocking)
            logger.info("embedding model ready: %s (%d dimensions)", self._model_name, self._dimension)
        except Exception as exc:
            self._failure = f"{type(exc).__name__}: {exc}"
            logger.error("embedding model could not be loaded from %s: %s", self._model_path, self._failure)

    def _load_blocking(self) -> Any:
        # Imported here, not at the top: torch is slow to import and absent from images built without the model.
        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(self._threads)
        model = SentenceTransformer(self._model_path, device="cpu", local_files_only=True)
        actual = model.get_sentence_embedding_dimension()
        if actual != self._dimension:
            raise ValueError(f"the model produces {actual} dimensions but {self._dimension} are configured")
        model.eval()
        return model

    def _encode(self, text: str) -> tuple[float, ...]:
        vector = self._model.encode(
            self._prefix + text, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )
        return tuple(float(value) for value in vector)
