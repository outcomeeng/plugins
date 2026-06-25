"""Re-export the canonical changeset-derivation symbols.

The canonical git-derivation primitives live in
``plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py``.
This module loads that file via ``importlib`` (the changeset-scope scripts
are not a package — they ship as bare modules under a runtime-substituted
plugin directory) and re-exports the symbols so the thread-store, audit,
and review-changes surfaces share one slug and base-ref rule.

The re-exported symbols are identity-equal to their canonical
counterparts. Tests assert this with ``branch_slug is canonical``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

_CHANGESET_SCOPE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "scope-changeset"
    / "scripts"
    / "changeset_scope.py"
)


def _load_changeset_scope() -> ModuleType:
    """Load ``changeset_scope`` via ``importlib`` and cache the module."""
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "changeset_scope", _CHANGESET_SCOPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {_CHANGESET_SCOPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


_changeset_scope = _load_changeset_scope()

# Re-export. ``is`` identity holds — the same function/class object.
branch_slug = _changeset_scope.branch_slug
detect_current_branch = _changeset_scope.detect_current_branch
detect_base_ref = _changeset_scope.detect_base_ref
DetachedHeadError = _changeset_scope.DetachedHeadError
BaseRefNotConfiguredError = _changeset_scope.BaseRefNotConfiguredError
BRANCH_SLUG_MAX_LENGTH = _changeset_scope.BRANCH_SLUG_MAX_LENGTH
BRANCH_SLUG_COLLISION_SUFFIX_LENGTH = (
    _changeset_scope.BRANCH_SLUG_COLLISION_SUFFIX_LENGTH
)
