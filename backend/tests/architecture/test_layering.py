"""Hexagonal boundaries, enforced by import-linter plus direct source checks."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from tests.architecture.source_tree import MODULES_ROOT, SRC_ROOT, module_names, parse, python_files, relative

BACKEND_DIR = Path(__file__).resolve().parents[2]


def test_import_linter_contracts_hold() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "importlinter.cli"], cwd=BACKEND_DIR, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module", module_names())
def test_every_module_has_an_application_layer_and_no_stray_top_level_code(module: str) -> None:
    root = MODULES_ROOT / module
    assert (root / "application").is_dir(), f"{module} must have an application layer"
    stray = [p.name for p in root.glob("*.py") if p.name != "__init__.py"]
    assert stray == [], f"{module} has code outside domain/application/adapters: {stray}"
    allowed = {"domain", "application", "adapters", "__pycache__"}
    unknown = {p.name for p in root.iterdir() if p.is_dir()} - allowed
    assert unknown == set(), f"{module} has unexpected packages: {unknown}"


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(parse(path)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


@pytest.mark.parametrize("path", list(python_files(MODULES_ROOT)), ids=relative)
def test_modules_never_import_the_composition_root_or_the_api(path: Path) -> None:
    offending = [i for i in _imports(path) if i.startswith(("davos.composition", "davos.api"))]
    assert offending == [], f"{relative(path)} imports {offending}"


_PURE_LAYERS = ("domain", "application")


def _pure_layer_files() -> list[Path]:
    return [p for p in python_files(SRC_ROOT) if any(f"/{layer}/" in relative(p) for layer in _PURE_LAYERS)]


_WALL_CLOCK_CALLS = {"now", "utcnow", "today"}


@pytest.mark.parametrize("path", _pure_layer_files(), ids=relative)
def test_domain_and_application_never_read_the_wall_clock(path: Path) -> None:
    """Time comes from the injected Clock; this keeps rules deterministic and testable."""
    for node in ast.walk(parse(path)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _WALL_CLOCK_CALLS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"datetime", "date"}
        ):
            pytest.fail(f"{relative(path)}:{node.lineno} reads the wall clock; inject Clock instead")


@pytest.mark.parametrize("path", [p for p in python_files(SRC_ROOT) if "/domain/" in relative(p)], ids=relative)
def test_domain_layer_is_synchronous_and_free_of_io(path: Path) -> None:
    for node in ast.walk(parse(path)):
        assert not isinstance(node, ast.AsyncFunctionDef | ast.Await), f"{relative(path)} is async in the domain"
    forbidden = {"random", "logging", "os", "subprocess", "socket", "requests"}
    assert not (_imports(path) & forbidden), f"{relative(path)} imports I/O or non-deterministic modules"


def test_ports_are_abstract_base_classes() -> None:
    for path in python_files(SRC_ROOT):
        rel = relative(path)
        if "/application/ports/" not in rel or not path.stem.endswith(
            ("_port", "_repository", "_hasher", "_generator", "_delivery", "_service")
        ):
            continue
        classes = [n for n in parse(path).body if isinstance(n, ast.ClassDef)]
        for cls in classes:
            bases = {b.id for b in cls.bases if isinstance(b, ast.Name)}
            assert "ABC" in bases, f"{rel}:{cls.name} is a port and must derive from ABC"


def test_every_orm_model_is_registered_for_migrations() -> None:
    registry = (SRC_ROOT / "platform/persistence/model_registry.py").read_text(encoding="utf-8")
    for path in python_files(SRC_ROOT):
        if path.stem.endswith("_model") and "persistence" in relative(path):
            dotted = "davos." + relative(path).removesuffix(".py").replace("/", ".")
            assert dotted in registry, f"{dotted} is missing from model_registry.py"


def test_orm_models_never_leak_into_the_application_or_domain_layers() -> None:
    for path in _pure_layer_files():
        leaked = [i for i in _imports(path) if i.endswith("_model") or "sqlalchemy" in i]
        assert leaked == [], f"{relative(path)} imports persistence details: {leaked}"
