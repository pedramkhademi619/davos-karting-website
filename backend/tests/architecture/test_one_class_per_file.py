"""Structural rule: one top-level class per file, and the file is named after that class."""

from __future__ import annotations

import ast

import pytest

from tests.architecture.source_tree import parse, python_files, relative


def _flat(name: str) -> str:
    """Compare names ignoring underscores and case so SqlAlchemyX matches sqlalchemy_x.py."""
    return name.replace("_", "").lower()


def _top_level_classes(path) -> list[ast.ClassDef]:
    return [node for node in parse(path).body if isinstance(node, ast.ClassDef)]


@pytest.mark.parametrize("path", list(python_files()), ids=relative)
def test_file_contains_at_most_one_top_level_class(path) -> None:
    classes = [c.name for c in _top_level_classes(path)]
    assert len(classes) <= 1, f"{relative(path)} defines several classes: {classes}"


@pytest.mark.parametrize("path", list(python_files()), ids=relative)
def test_file_name_matches_the_class_it_contains(path) -> None:
    classes = _top_level_classes(path)
    if len(classes) != 1:
        return
    assert _flat(path.stem) == _flat(classes[0].name), (
        f"{relative(path)} should be named after its class {classes[0].name}"
    )
