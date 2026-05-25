"""Re-export the canonical ``branch_slug`` function.

The canonical slug derivation lives in
``plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py``.
This module loads that file via ``importlib`` (the auditing scripts are
not a package — they ship as bare modules under a runtime-substituted
plugin directory) and re-exports the symbol so audit and review
surfaces share one rule.

The re-exported symbols are identity-equal to their canonical
counterparts. Tests assert this with ``branch_slug is canonical``.

See ``spx/21-spec-tree.enabler/16-verification.enabler/21-thread-store.enabler/21-backend-abstraction.adr.md``
for the architectural rationale.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType


_AUDIT_ORCHESTRATOR_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "auditing"
    / "scripts"
    / "audit_orchestrator.py"
)


def _load_audit_orchestrator() -> ModuleType:
    """Load ``audit_orchestrator`` via ``importlib`` and cache the module."""
    cached = sys.modules.get("audit_orchestrator")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "audit_orchestrator", _AUDIT_ORCHESTRATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load audit_orchestrator from {_AUDIT_ORCHESTRATOR_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_orchestrator"] = module
    spec.loader.exec_module(module)
    return module


_audit_orchestrator = _load_audit_orchestrator()

# Re-export. ``is`` identity holds — the same function object.
branch_slug = _audit_orchestrator.branch_slug
detect_current_branch = _audit_orchestrator.detect_current_branch
detect_base_ref = _audit_orchestrator.detect_base_ref
DetachedHeadError = _audit_orchestrator.DetachedHeadError
BaseRefNotConfiguredError = _audit_orchestrator.BaseRefNotConfiguredError
BRANCH_SLUG_MAX_LENGTH = _audit_orchestrator.BRANCH_SLUG_MAX_LENGTH
BRANCH_SLUG_COLLISION_SUFFIX_LENGTH = (
    _audit_orchestrator.BRANCH_SLUG_COLLISION_SUFFIX_LENGTH
)
