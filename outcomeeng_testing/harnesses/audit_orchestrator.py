"""Harness for audit-orchestrator tests.

Loads ``audit_orchestrator.py`` — the ``/audit`` skill's script for changeset
scope expansion, base-ref helpers, scope hashing, and prior-run diffing — for
the test files under ``spx/21-spec-tree.enabler/68-audit.enabler/tests/``.

The script is not importable as a package because it lives under
``src/plugins/`` (authored plugin source) and ships as a bare module under
``scripts/``. Tests that inspect its pure helpers load it through ``importlib``
instead of a regular import.

The harness lives in ``outcomeeng_testing/harnesses/`` so shared test scaffolding
stays outside ``tests/`` and outside ``spx/``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/audit_orchestrator.py``.
AUDIT_ORCHESTRATOR_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "audit"
    / "scripts"
    / "audit_orchestrator.py"
)


def load_audit_orchestrator_module() -> ModuleType:
    """Load ``audit_orchestrator.py`` as a module, cached under ``sys.modules``.

    Returns the already-loaded module on subsequent calls so the importlib
    loader runs at most once per test session.
    """
    cached = sys.modules.get("audit_orchestrator")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "audit_orchestrator", AUDIT_ORCHESTRATOR_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {AUDIT_ORCHESTRATOR_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_orchestrator"] = module
    spec.loader.exec_module(module)
    return module
