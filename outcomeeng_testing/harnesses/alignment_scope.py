"""Harness assertions for the align skill's changeset-scope adapter."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import ModuleType

from outcomeeng_testing.harnesses.changeset_scope import (
    build_repo_without_origin,
    build_stale_local_base_repo,
    load_changeset_scope_module,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ALIGNMENT_SCOPE_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "align"
    / "scripts"
    / "derive_changeset_scope.py"
)
ALIGNMENT_SCOPE_MODULE_NAME = "outcomeeng_testing_alignment_scope_adapter"


def _module_origin(module: ModuleType) -> pathlib.Path | None:
    origin = getattr(module, "__file__", None)
    return pathlib.Path(origin).resolve() if origin is not None else None


def _load_alignment_scope_module() -> ModuleType:
    cached = sys.modules.get(ALIGNMENT_SCOPE_MODULE_NAME)
    if cached is not None and _module_origin(cached) == ALIGNMENT_SCOPE_MODULE_PATH:
        return cached
    spec = importlib.util.spec_from_file_location(
        ALIGNMENT_SCOPE_MODULE_NAME, ALIGNMENT_SCOPE_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load alignment scope adapter from {ALIGNMENT_SCOPE_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[ALIGNMENT_SCOPE_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def assert_alignment_uses_canonical_changeset_scope() -> None:
    """Prove the executable adapter returns the canonical branch scope."""
    previous = sys.modules.get(ALIGNMENT_SCOPE_MODULE_NAME)
    foreign = sys.modules[__name__]
    sys.modules[ALIGNMENT_SCOPE_MODULE_NAME] = foreign
    try:
        adapter = _load_alignment_scope_module()
    finally:
        if previous is None:
            sys.modules.pop(ALIGNMENT_SCOPE_MODULE_NAME, None)
        else:
            sys.modules[ALIGNMENT_SCOPE_MODULE_NAME] = previous

    assert adapter is not foreign
    assert _module_origin(adapter) == ALIGNMENT_SCOPE_MODULE_PATH

    with TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / "repo"
        repo.mkdir()
        handle = build_stale_local_base_repo(repo)
        canonical = load_changeset_scope_module()

        completed = subprocess.run(
            (sys.executable, str(ALIGNMENT_SCOPE_MODULE_PATH), str(repo)),
            capture_output=True,
            text=True,
            check=False,
        )

        base_ref = canonical.detect_base_ref(repo)
        payload = json.loads(completed.stdout)
        assert completed.returncode == 0
        assert payload == {
            adapter.SCHEMA_VERSION_FIELD: adapter.SCHEMA_VERSION,
            adapter.BASE_REF_FIELD: base_ref,
            adapter.CHANGED_FILES_FIELD: canonical.branch_scope(base_ref, repo=repo),
            adapter.ERROR_FIELD: None,
        }
        assert handle.feature_file in payload[adapter.CHANGED_FILES_FIELD]
        assert handle.merged_file not in payload[adapter.CHANGED_FILES_FIELD]


def assert_alignment_reports_unconfigured_base() -> None:
    """Prove an absent origin/HEAD produces structured actionable failure."""
    with TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / "repo"
        repo.mkdir()
        build_repo_without_origin(repo)
        adapter = _load_alignment_scope_module()
        canonical = load_changeset_scope_module()

        completed = subprocess.run(
            (sys.executable, str(ALIGNMENT_SCOPE_MODULE_PATH), str(repo)),
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(completed.stderr)

        assert completed.returncode != 0
        assert payload[adapter.SCHEMA_VERSION_FIELD] == adapter.SCHEMA_VERSION
        assert canonical.ORIGIN_HEAD_REF in payload[adapter.ERROR_FIELD]
        assert payload[adapter.REMEDIATION_FIELD] == adapter.BASE_REF_REMEDIATION
        assert "Traceback" not in completed.stderr
