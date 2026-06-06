"""Compliance test: the changeset-derivation primitives have one home.

Covers the Compliance assertion in ``../changeset-scope.md`` that the
derivation primitives resolve to one module and the ``branch_slug`` re-export at
``plugins/spec-tree/skills/thread-store/scripts/branch_slug.py`` is
identity-equal to the canonical symbol in ``changeset_scope``.

The re-export module loads the canonical module through the shared
``sys.modules['changeset_scope']`` cache, so a re-exported symbol is the same
function object as the canonical one. ``is`` identity — not mere equality —
proves there is a single implementation rather than a copy.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import load_changeset_scope_module
from outcomeeng_testing.harnesses.thread_store import load_branch_slug_module


def test_branch_slug_re_export_is_identity_equal_to_canonical() -> None:
    canonical = load_changeset_scope_module()
    re_export = load_branch_slug_module()
    assert re_export.branch_slug is canonical.branch_slug


def test_branch_identity_helpers_re_export_is_identity_equal_to_canonical() -> None:
    canonical = load_changeset_scope_module()
    re_export = load_branch_slug_module()
    assert re_export.detect_current_branch is canonical.detect_current_branch
    assert re_export.detect_base_ref is canonical.detect_base_ref


def test_error_classes_re_export_is_identity_equal_to_canonical() -> None:
    canonical = load_changeset_scope_module()
    re_export = load_branch_slug_module()
    assert re_export.DetachedHeadError is canonical.DetachedHeadError
    assert re_export.BaseRefNotConfiguredError is canonical.BaseRefNotConfiguredError
