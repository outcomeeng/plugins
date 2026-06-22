"""Harness for the audit consumer's run-journal adapter tests.

Loads ``journal_emit.py`` — the ``/audit`` skill's consumer-side adapter that
maps an audit wrapper verdict onto ``spx journal`` channel events and renders
the run's verdict from a sealed event prefix — for the test files under
``spx/21-spec-tree.enabler/tests/``.

The adapter is not importable as a package — it lives under ``src/plugins/``
(authored plugin source) and the marketplace ships every plugin script under
``scripts/`` as a bare module that ``python3 path/to/script.py`` resolves via
``sys.path[0]``. Tests that introspect its pure functions load it through
``importlib`` instead of a regular import. The adapter resolves its own
sibling (``verdict.py``) and cross-skill (``journal_projection.py``) imports
relative to its ``__file__``, so loading it here triggers no ``sys.path``
dependency.

The harness lives in ``outcomeeng_testing/harnesses/`` per
``spx/15-test-infrastructure.pdr.md`` — shared test scaffolding is production
code with its home outside ``tests/`` and outside ``spx/``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/audit_journal_emit.py``.
JOURNAL_EMIT_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "audit"
    / "scripts"
    / "journal_emit.py"
)


def load_journal_emit_module() -> ModuleType:
    """Load ``journal_emit.py`` as a module, cached under ``sys.modules``.

    Returns the already-loaded module on subsequent calls so the importlib
    loader runs at most once per test session.
    """
    cached = sys.modules.get("journal_emit")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "journal_emit", JOURNAL_EMIT_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {JOURNAL_EMIT_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["journal_emit"] = module
    spec.loader.exec_module(module)
    return module
