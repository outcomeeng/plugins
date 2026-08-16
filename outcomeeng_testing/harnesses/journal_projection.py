"""Harness for journal-projection tests.

Loads the shared run-journal projection helper for the test files under
``spx/21-spec-tree.enabler/16-verification.enabler/18-journal-projection.enabler/tests/``.

The helper is not importable as a package — it lives under ``src/plugins/``
(authored plugin source) and the marketplace ships every plugin script under
``scripts/`` as a bare module that ``python3 path/to/script.py`` resolves via
``sys.path[0]``. Tests that introspect its dataclasses, constants, and pure
functions load it through ``importlib`` instead of a regular import.

The harness lives in ``outcomeeng_testing/harnesses/`` because shared test
scaffolding is production code with its home outside ``tests/`` and outside
``spx/``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/journal_projection.py``.
PROJECTION_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "verification-run-journal-standards"
    / "scripts"
    / "journal_projection.py"
)
RENDER_REVIEW_RUN_MODULE_PATH = PROJECTION_MODULE_PATH.with_name("render_review_run.py")
INSPECT_REVIEW_RUN_SCRIPT = (
    PROJECTION_MODULE_PATH.parents[2]
    / "inspect-review-run"
    / "scripts"
    / "inspect_review_run.py"
)


def load_journal_projection_module() -> ModuleType:
    """Load ``journal_projection.py`` as a module, cached under ``sys.modules``.

    Returns the already-loaded module on subsequent calls so the importlib
    loader runs at most once per test session.
    """
    cached = sys.modules.get("journal_projection")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "journal_projection", PROJECTION_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {PROJECTION_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["journal_projection"] = module
    spec.loader.exec_module(module)
    return module


def load_render_review_run_module() -> ModuleType:
    """Load ``render_review_run.py`` as a module after its sibling dependency."""
    load_journal_projection_module()
    cached = sys.modules.get("render_review_run")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "render_review_run", RENDER_REVIEW_RUN_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {RENDER_REVIEW_RUN_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_review_run"] = module
    spec.loader.exec_module(module)
    return module
