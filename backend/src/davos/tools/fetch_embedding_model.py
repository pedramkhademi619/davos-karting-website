"""Download the answer cache's local embedding model once, into the folder the API then reads with no network access.

    backend/.venv/Scripts/python.exe -m davos.tools.fetch_embedding_model backend/models/paraphrase-multilingual-minilm

This is the only step that touches the internet, and it is a plain download of three public files at pinned commits
(no API key, nothing sent about you): about 124 MB. Afterwards the API reads the folder named in
SEMANTIC_CACHE_MODEL_DIR and never connects to anything for embeddings; to set up a machine that must stay offline,
copy the folder in from another one. Every file is checked against its SHA-256 below, so a changed or damaged file is
refused instead of silently changing how questions are compared.

Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (Apache-2.0; trained on paraphrase pairs in 50+
languages, Persian included; 384 dimensions). The network comes as the int8-quantised ONNX export by Xenova (113 MB);
the tokenizer is the model's own SentencePiece file from the official repository (5 MB, 39 MB of memory where the
equivalent tokenizer.json needs 250 MB; the two give identical token ids, checked on 224 sentences).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import httpx

from davos.tools.embedding_model.model_file import ModelFile

FILES = (
    ModelFile(
        "Xenova/paraphrase-multilingual-MiniLM-L12-v2",
        "2c4055b",
        "onnx/model_quantized.onnx",
        "model.onnx",
        "66fc00f5f29afcaff34092e1bdd20008ca3918265a82fb9695a551e510cc4ebc",
    ),
    ModelFile(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
        "sentencepiece.bpe.model",
        "sentencepiece.bpe.model",
        "cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865",
    ),
    ModelFile(
        "Xenova/paraphrase-multilingual-MiniLM-L12-v2",
        "2c4055b",
        "config.json",
        "config.json",
        "05b570bff786faa5c4604152aa16f19f77ed6dfc31e47dd0f3dd987078693ac7",
    ),
)


def _download(client: httpx.Client, file: ModelFile, target: Path) -> str:
    url = f"https://huggingface.co/{file.repository}/resolve/{file.revision}/{file.path}"
    digest = hashlib.sha256()
    partial = target.with_suffix(target.suffix + ".part")
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with partial.open("wb") as out:
            for chunk in response.iter_bytes(1 << 20):
                out.write(chunk)
                digest.update(chunk)
    partial.replace(target)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("destination", type=Path, help="folder to put the model in (created if missing)")
    args = parser.parse_args(argv)
    args.destination.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(60.0, connect=15.0)) as client:
        for file in FILES:
            target = args.destination / file.name
            actual = _download(client, file, target)
            if actual != file.sha256:
                target.unlink()
                print(f"REFUSED {file.path}: SHA-256 {actual} is not the pinned {file.sha256}")
                return 1
            print(f"{file.name:<26} {target.stat().st_size / 1_048_576:7.1f} MB  sha256 verified")
    print(f"model ready in {args.destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
