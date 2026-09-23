"""Downloads the local embedding model once, into a folder the API then reads without any network access.

    docker compose --profile tools run --rm fetch-embedding-model

This is the only step that touches the internet, and it is a plain file download (a public model repository, no API
key, nothing sent about you). Run it once; afterwards the API runs with ``HF_HUB_OFFLINE=1`` and never connects to
anything for embeddings. If this machine must stay offline, copy the folder in from another machine instead.

The revision is pinned to a commit, so the files are exactly the ones the cache was tested with.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_REPOSITORY = "intfloat/multilingual-e5-base"
# Commit of the repository that the semantic cache was calibrated against.
DEFAULT_REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"
# Only what sentence-transformers needs to run on the CPU: not the duplicate pytorch_model.bin, ONNX or OpenVINO copies.
_FILES = (
    "config.json",
    "model.safetensors",
    "modules.json",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "1_Pooling/config.json",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("destination", help="folder to put the model in (created if missing)")
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    args = parser.parse_args(argv)

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub is not installed here; run this inside the api image (it carries the model libraries).")
        return 2

    destination = Path(args.destination)
    destination.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=args.repository, revision=args.revision, local_dir=str(destination), allow_patterns=list(_FILES)
    )
    missing = [name for name in _FILES if not (destination / name).is_file()]
    if missing:
        print(f"download incomplete, missing: {', '.join(missing)}")
        return 1
    size_mb = sum(f.stat().st_size for f in destination.rglob("*") if f.is_file()) / 1_048_576
    print(f"model ready in {destination} ({size_mb:.0f} MB, revision {args.revision[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
