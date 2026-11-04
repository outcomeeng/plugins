"""Test infrastructure for the shipped document-levels script."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).parents[2]
DOCUMENT_LEVELS_PATH = (
    ROOT / "src/plugins/product-tree/skills/understand/scripts/document_levels.py"
)
FIXTURE_ROOT = ROOT / "outcomeeng_testing/fixtures/document_levels"
DOCUMENT_FILE = "document.md.txt"
PATH_FILE = "path.txt"


def load_document_levels() -> ModuleType:
    """Load the shipped script so linked tests can exercise its public contract."""
    spec = importlib.util.spec_from_file_location(
        "product_tree_document_levels", DOCUMENT_LEVELS_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load document-levels script: {DOCUMENT_LEVELS_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fixture_documents() -> tuple[Path, ...]:
    """Return the fixture directories, one per document form, in a fixed order."""
    return tuple(sorted(path for path in FIXTURE_ROOT.iterdir() if path.is_dir()))


def document_text(directory: Path) -> str:
    return (directory / DOCUMENT_FILE).read_text(encoding="utf-8")


def document_path(directory: Path) -> str:
    return (directory / PATH_FILE).read_text(encoding="utf-8").strip()


def expected_view(directory: Path, label: str) -> str:
    """Read the view a fixture directory declares for the level the label names."""
    return (directory / f"{label}.txt").read_text(encoding="utf-8")
