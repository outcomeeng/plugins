"""Compliance evidence for the review-changes shipped-script boundaries.

Covers two universal rules in ``../reviewing-changes.md`` and the matching
Testing rule in ``../21-script-decomposition.adr.md``:

- ALWAYS: scripts under the skill's ``scripts/`` directory write no durable
  review state directly; ``compute_diff.py`` may write only the caller-owned
  scratch review-input bundle and ``review_run.py`` only runner-owned scratch
  state.
- NEVER: any script imports a third-party package, depends on ``uv`` at
  runtime, or imports any ``outcomeeng_*`` module.

Each rule is exercised against the real shipped scripts (the conforming side)
and against a violating fixture read by path (the detecting side), so a
disabled observer fails the linked test.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.reviewing_changes_audit import (
    DIRECT_WRITE_FIXTURE,
    OUTCOMEENG_IMPORT_FIXTURE,
    RUNTIME_UV_FIXTURE,
    THIRD_PARTY_IMPORT_FIXTURE,
    direct_write_violations,
    non_stdlib_imports,
    outcomeeng_imports,
    runtime_uv_references,
    script_files,
)

SHIPPED_SCRIPTS = script_files()


class TestScriptsWriteNoDurableState:
    """Scripts write no durable review state through direct primitives."""

    @pytest.mark.parametrize("script_path", SHIPPED_SCRIPTS, ids=lambda p: p.name)
    def test_shipped_script_uses_no_direct_write_primitive(
        self, script_path: pathlib.Path
    ) -> None:
        assert direct_write_violations(script_path) == []

    def test_direct_write_fixture_is_detected(self) -> None:
        violations = direct_write_violations(DIRECT_WRITE_FIXTURE)
        assert any("open(" in violation for violation in violations)
        assert any(".write_text()" in violation for violation in violations)


class TestScriptsAreStdlibOnly:
    """No script imports third-party or ``outcomeeng_*`` modules or references ``uv``."""

    @pytest.mark.parametrize("script_path", SHIPPED_SCRIPTS, ids=lambda p: p.name)
    def test_shipped_script_imports_only_stdlib_and_local_modules(
        self, script_path: pathlib.Path
    ) -> None:
        assert non_stdlib_imports(script_path) == []

    @pytest.mark.parametrize("script_path", SHIPPED_SCRIPTS, ids=lambda p: p.name)
    def test_shipped_script_imports_no_outcomeeng_module(
        self, script_path: pathlib.Path
    ) -> None:
        assert outcomeeng_imports(script_path) == []

    @pytest.mark.parametrize("script_path", SHIPPED_SCRIPTS, ids=lambda p: p.name)
    def test_shipped_script_references_no_runtime_uv(
        self, script_path: pathlib.Path
    ) -> None:
        assert runtime_uv_references(script_path) == []

    def test_third_party_import_fixture_is_detected(self) -> None:
        assert non_stdlib_imports(THIRD_PARTY_IMPORT_FIXTURE) == ["requests"]

    def test_outcomeeng_import_fixture_is_detected(self) -> None:
        assert outcomeeng_imports(OUTCOMEENG_IMPORT_FIXTURE) == ["outcomeeng_testing"]

    def test_runtime_uv_fixture_is_detected(self) -> None:
        assert runtime_uv_references(RUNTIME_UV_FIXTURE) != []
