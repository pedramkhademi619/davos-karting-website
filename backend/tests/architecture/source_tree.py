"""Helpers shared by the architecture tests: enumerate and parse the production source tree."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "davos"
MODULES_ROOT = SRC_ROOT / "modules"


def python_files(root: Path = SRC_ROOT) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        if path.name != "__init__.py":
            yield path


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def relative(path: Path) -> str:
    return path.relative_to(SRC_ROOT).as_posix()


def module_names() -> list[str]:
    return sorted(p.name for p in MODULES_ROOT.iterdir() if p.is_dir() and not p.name.startswith("__"))
