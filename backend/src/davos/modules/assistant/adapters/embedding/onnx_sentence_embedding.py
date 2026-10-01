from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding

logger = logging.getLogger(__name__)

_MODEL_FILE = "model.onnx"
_TOKENIZER_FILE = "sentencepiece.bpe.model"
_MAX_TOKENS = 128  # the model was trained on sentences of at most this many tokens
# XLM-RoBERTa token layout (the tokenizer this model uses): <s>=0, <pad>=1, </s>=2, <unk>=3, and every other
# SentencePiece id is shifted up by one. Checked against the model's own tokenizer.json on 224 questions
# (docs/ASSISTANT_EVALUATION.md): identical ids, at a sixth of the memory.
_BOS, _EOS, _UNK = 0, 2, 3


class OnnxSentenceEmbedding(EmbeddingPort):
    """Sentence embeddings from paraphrase-multilingual-MiniLM-L12-v2 (int8 ONNX, 384 dimensions), on this machine.

    The model is read from a folder made by ``python -m davos.tools.fetch_embedding_model``; nothing is fetched at run
    time. It loads once (``warm_up``, called when the API starts) and inference runs in a worker thread, so a question
    never blocks the event loop; the model needs about 170 MB per API process and about 4 ms per question. A model that
    cannot load leaves the answer cache off (every question goes to the language model) and never breaks a request.
    """

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2-int8"

    def __init__(self, model_dir: str, *, threads: int) -> None:
        self._dir = Path(model_dir)
        self._threads = threads
        self._lock = asyncio.Lock()
        self._session: Any = None
        self._tokenizer: Any = None
        self._input_names: frozenset[str] = frozenset()
        self._failed = False

    @property
    def model_name(self) -> str:
        return self.MODEL_NAME

    async def warm_up(self) -> None:
        async with self._lock:
            if self._session is not None or self._failed:
                return
            try:
                await asyncio.to_thread(self._load)
            except Exception as exc:  # missing files, unsupported CPU, damaged model: keep the cache off
                self._failed = True
                logger.warning("answer cache model not loaded from %s: %s", self._dir, type(exc).__name__)
                return
            logger.info("answer cache embedding model ready (%s)", self.MODEL_NAME)

    async def embed_query(self, text: str) -> QueryEmbedding:
        if self._session is None and not self._failed:
            await self.warm_up()
        if self._session is None:
            raise EmbeddingUnavailableError("the embedding model is not loaded")
        try:
            return await asyncio.to_thread(self._embed, text)
        except Exception as exc:
            raise EmbeddingUnavailableError("the embedding model failed on a question") from exc

    # ---- blocking work, run in a thread -----------------------------------------------------------------------
    def _load(self) -> None:
        import onnxruntime as ort
        import sentencepiece as spm

        model, tokenizer = self._dir / _MODEL_FILE, self._dir / _TOKENIZER_FILE
        for required in (model, tokenizer):
            if not required.is_file():
                raise FileNotFoundError(required.name)
        options = ort.SessionOptions()
        options.intra_op_num_threads = self._threads
        options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(model), options, providers=["CPUExecutionProvider"])
        self._input_names = frozenset(i.name for i in session.get_inputs())
        self._tokenizer = spm.SentencePieceProcessor(model_file=str(tokenizer))
        self._session = session

    def _embed(self, text: str) -> QueryEmbedding:
        import numpy as np

        pieces = self._tokenizer.encode(text)[: _MAX_TOKENS - 2]
        ids = np.array([[_BOS, *(_UNK if p == 0 else p + 1 for p in pieces), _EOS]], dtype=np.int64)
        mask = np.ones_like(ids)
        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in self._input_names:
            feeds["token_type_ids"] = np.zeros_like(ids)
        hidden = self._session.run(None, feeds)[0]  # (1, tokens, 384)
        pooled = hidden.mean(axis=1)[0]  # mean over the tokens (every token counts: there is no padding)
        norm = float(np.linalg.norm(pooled))
        return QueryEmbedding(tuple(float(v) for v in pooled / norm))
