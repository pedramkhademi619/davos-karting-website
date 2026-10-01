"""The embedding adapter: its failure behaviour always, and the real model when this machine has it
(backend/models/paraphrase-multilingual-minilm, from ``python -m davos.tools.fetch_embedding_model``)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from davos.modules.assistant.adapters.embedding.onnx_sentence_embedding import OnnxSentenceEmbedding
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError

MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / "paraphrase-multilingual-minilm"
needs_model = pytest.mark.skipif(
    not (MODEL_DIR / "model.onnx").is_file(), reason="the embedding model has not been downloaded on this machine"
)


async def test_a_missing_model_folder_never_raises_on_warm_up_and_reports_unavailable() -> None:
    embedding = OnnxSentenceEmbedding("no/such/folder", threads=1)
    await embedding.warm_up()
    await embedding.warm_up()  # and a second time: it does not retry the load on every question
    with pytest.raises(EmbeddingUnavailableError):
        await embedding.embed_query("قیمت چنده؟")


async def test_an_empty_folder_is_unavailable_too(tmp_path: Path) -> None:
    with pytest.raises(EmbeddingUnavailableError):
        await OnnxSentenceEmbedding(str(tmp_path), threads=1).embed_query("سلام")


async def test_a_damaged_model_file_is_unavailable_not_a_crash(tmp_path: Path) -> None:
    (tmp_path / "model.onnx").write_bytes(b"not a model")
    (tmp_path / "sentencepiece.bpe.model").write_bytes(b"not a tokenizer")
    with pytest.raises(EmbeddingUnavailableError):
        await OnnxSentenceEmbedding(str(tmp_path), threads=1).embed_query("سلام")


@pytest.fixture
async def model() -> OnnxSentenceEmbedding:
    embedding = OnnxSentenceEmbedding(str(MODEL_DIR), threads=1)
    await embedding.warm_up()
    return embedding


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


@needs_model
async def test_the_real_model_gives_unit_vectors_of_the_size_the_table_expects(model: OnnxSentenceEmbedding) -> None:
    vector = (await model.embed_query("قیمت هاتون چطوریه؟")).values
    assert len(vector) == 384
    assert cosine(vector, vector) == pytest.approx(1.0, abs=1e-5)


@needs_model
async def test_the_real_model_puts_a_rewording_closer_than_an_unrelated_question(model: OnnxSentenceEmbedding) -> None:
    price = (await model.embed_query("قیمت هاتون چطوریه؟")).values
    reworded = (await model.embed_query("قیمتتون چیه؟")).values
    unrelated = (await model.embed_query("ساعت کاریتون چیه؟")).values
    assert cosine(price, reworded) > 0.9 > 0.5 > cosine(price, unrelated)


@needs_model
async def test_the_real_model_handles_empty_long_and_mixed_script_text(model: OnnxSentenceEmbedding) -> None:
    for text in ("", "a" * 3000, "سلام hello ۱۲۳ 😀"):
        assert len((await model.embed_query(text)).values) == 384


@needs_model
async def test_the_real_model_is_fast_enough_to_sit_in_front_of_every_question(model: OnnxSentenceEmbedding) -> None:
    await model.embed_query("گرم کردن")
    started = time.perf_counter()
    for _ in range(20):
        await model.embed_query("پرداخت با چه درگاهیه؟")
    assert (time.perf_counter() - started) / 20 < 0.05  # measured about 4 ms; a generous bound for a busy test machine
