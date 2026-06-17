"""Compliance tests for facade-level rules.

Covers the Compliance clauses on ``thread_store`` in
``../thread-store.md`` that are universal rules rather than per-case
scenarios:

- ``thread_store.write`` is atomic: an interruption between temp-write
  and rename leaves the prior content of the target intact.
- ``branch_slug`` is the symbol re-exported from
  ``plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py`` —
  slug derivation has exactly one canonical implementation source.
- The test harness at ``outcomeeng_testing/harnesses/thread_store.py``
  exposes the symbols the spec mandates.
- The filesystem backend confines every write to its configured root —
  writes against normal slugs and names resolve to paths inside the
  configured root.
"""

from __future__ import annotations

import os
import pathlib

import pytest

from outcomeeng_testing.harnesses.changeset_scope import load_changeset_scope_module
from outcomeeng_testing.harnesses.thread_store import (
    load_branch_slug_module,
    load_fs_backend_module,
    load_thread_store_module,
    make_changes_json,
    with_temp_local_store,
)


SLUG = "feature__x"
NAME = "result.json"
PAYLOAD = b'{"verdict":"APPROVED"}'


class TestWriteAtomicity:
    """``thread_store.write`` preserves prior content on crash."""

    def test_atomic_write_leaves_prior_payload_on_failure(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patches ``os.replace`` to raise after the temp file lands on disk.

        The prior payload must remain readable; the rename never
        completes, so the post-failure read returns the original bytes.
        """
        with with_temp_local_store(tmp_path):
            ts = load_thread_store_module()
            ts.write(SLUG, NAME, PAYLOAD)

            real_replace = os.replace

            def raising_replace(src: object, dst: object) -> None:
                raise OSError("simulated crash between temp-write and rename")

            monkeypatch.setattr(os, "replace", raising_replace)
            new_payload = b'{"verdict":"REJECTED"}'
            with pytest.raises(OSError):
                ts.write(SLUG, NAME, new_payload)
            monkeypatch.setattr(os, "replace", real_replace)

            assert ts.read(SLUG, NAME) == PAYLOAD


class TestSlugSymbolIdentity:
    """``branch_slug`` has one canonical implementation source."""

    def test_branch_slug_is_re_exported_from_changeset_scope(self) -> None:
        re_exported = load_branch_slug_module().branch_slug
        canonical = load_changeset_scope_module().branch_slug
        assert re_exported is canonical

    def test_max_length_constant_matches_changeset_scope(self) -> None:
        re_exported_const = load_branch_slug_module().BRANCH_SLUG_MAX_LENGTH
        canonical_const = load_changeset_scope_module().BRANCH_SLUG_MAX_LENGTH
        assert re_exported_const == canonical_const


class TestFilesystemConfinedToRoot:
    """Every filesystem-backend write resolves inside the configured root."""

    def test_normal_write_lands_under_root(self, tmp_path: pathlib.Path) -> None:
        fs_backend = load_fs_backend_module()
        backend = fs_backend.FilesystemBackend(root=tmp_path)
        backend.write(SLUG, NAME, PAYLOAD)
        target = backend.thread_path(SLUG) / NAME
        assert target.is_file()
        # The spec mandates ``<root>/<slug>/<name>`` as the only target
        # shape — verify the exact two-segment construction, not just
        # that the file lies somewhere under root.
        assert target == tmp_path / SLUG / NAME
        # Defence-in-depth: the resolved path also lives under the
        # resolved root (catches symlink-based escape attempts).
        resolved_target = target.resolve()
        resolved_root = tmp_path.resolve()
        assert resolved_root in resolved_target.parents

    def test_no_files_created_outside_root(self, tmp_path: pathlib.Path) -> None:
        """After writing one record, no files exist above the configured root.

        The test creates a sentinel structure parallel to the root and
        asserts the backend never reaches into it: only the configured
        root acquires new contents.
        """
        sibling = tmp_path.parent / "sibling-outside-root"
        sibling.mkdir(exist_ok=True)
        sentinel = sibling / "sentinel.txt"
        sentinel.write_text("untouched")

        try:
            fs_backend = load_fs_backend_module()
            backend = fs_backend.FilesystemBackend(root=tmp_path)
            backend.write(SLUG, NAME, PAYLOAD)
            backend.delete(SLUG, NAME)

            assert sentinel.read_text() == "untouched"
            # The sibling directory's contents are unchanged.
            assert list(sibling.iterdir()) == [sentinel]
        finally:
            sentinel.unlink()
            sibling.rmdir()


class TestHarnessSurface:
    """The harness exposes every symbol the spec mandates.

    The thread-store spec asserts that the harness exposes
    ``make_changes_json``, ``with_temp_local_store``, ``run_script``,
    and an importlib loader for the facade module. These tests verify
    the contract holds and the helpers behave as advertised.
    """

    def test_with_temp_local_store_restores_environment(
        self, tmp_path: pathlib.Path
    ) -> None:
        sentinel = "previous-value"
        os.environ["SPX_VERIFY_BACKEND"] = sentinel
        try:
            with with_temp_local_store(tmp_path):
                assert os.environ["SPX_VERIFY_BACKEND"] == "local"
                assert os.environ["SPX_VERIFY_LOCAL_ROOT"] == str(tmp_path)
            assert os.environ["SPX_VERIFY_BACKEND"] == sentinel
        finally:
            os.environ.pop("SPX_VERIFY_BACKEND", None)

    def test_make_changes_json_writes_payload_with_base_ref(
        self, tmp_path: pathlib.Path
    ) -> None:
        import json

        target = make_changes_json(tmp_path, base_ref="main")
        payload = json.loads(target.read_text())
        assert payload["base_ref"] == "main"
        assert target.name == "changes.json"

    def test_make_changes_json_merges_overrides(self, tmp_path: pathlib.Path) -> None:
        import json

        target = make_changes_json(
            tmp_path, base_ref="main", extra_field="future-extension"
        )
        payload = json.loads(target.read_text())
        assert payload["base_ref"] == "main"
        assert payload["extra_field"] == "future-extension"

    def test_facade_module_loads_via_importlib(self) -> None:
        ts = load_thread_store_module()
        assert hasattr(ts, "write")
        assert hasattr(ts, "read")
        assert hasattr(ts, "delete")
        assert hasattr(ts, "list")
        assert hasattr(ts, "get_backend")
        assert hasattr(ts, "NotFound")

    def test_run_script_has_required_signature(self) -> None:
        """``run_script`` accepts ``(script, *args, stdin=None, env=None)``.

        The spec line 35 names this exact signature as part of the
        harness's externally observable contract. A regression that
        drops the ``env`` keyword (or renames ``stdin``) would break
        every test that invokes a CLI via subprocess; the explicit
        signature check guards against that.
        """
        import inspect

        from outcomeeng_testing.harnesses.thread_store import run_script

        sig = inspect.signature(run_script)
        param_names = list(sig.parameters)
        assert param_names[0] == "script", (
            f"first parameter must be 'script', got {param_names[0]!r}"
        )
        var_positional = [
            p
            for p in sig.parameters.values()
            if p.kind == inspect.Parameter.VAR_POSITIONAL
        ]
        assert var_positional, "run_script must accept *args"
        for kwarg in ("stdin", "env"):
            assert kwarg in sig.parameters, f"run_script missing kwarg {kwarg!r}"
            assert sig.parameters[kwarg].default is None, (
                f"run_script kwarg {kwarg!r} must default to None"
            )
