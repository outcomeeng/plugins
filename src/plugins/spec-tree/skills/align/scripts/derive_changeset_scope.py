"""Emit canonical branch changeset scope for the align skill.

The adapter stays deliberately thin: it loads ``detect_base_ref`` and
``branch_scope`` from the sibling scope-changeset skill and serializes their
result for the align workflow.

Tested inputs and error cases: a repository with an advanced remote-tracking
base returns only the feature branch's changed paths; a repository without
``refs/remotes/origin/HEAD`` returns structured remediation and a nonzero exit.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
from types import ModuleType

_CHANGESET_SCOPE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "scope-changeset"
    / "scripts"
    / "changeset_scope.py"
)

SCHEMA_VERSION = 1
SCHEMA_VERSION_FIELD = "schema_version"
BASE_REF_FIELD = "base_ref"
CHANGED_FILES_FIELD = "changed_files"
ERROR_FIELD = "error"
REMEDIATION_FIELD = "remediation"
BASE_REF_REMEDIATION = (
    "Configure refs/remotes/origin/HEAD to the repository's authoritative "
    "default branch, then rerun alignment."
)
GIT_SCOPE_REMEDIATION = (
    "Confirm the repository and origin/<base> refs are readable, then rerun alignment."
)


def _module_origin(module: ModuleType) -> pathlib.Path | None:
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str):
        return None
    return pathlib.Path(module_file).resolve()


def _load_changeset_scope() -> ModuleType:
    """Load and cache the canonical sibling changeset-scope module."""
    resolved_path = _CHANGESET_SCOPE_PATH.resolve()
    cached = sys.modules.get("changeset_scope")
    if cached is not None and _module_origin(cached) == resolved_path:
        return cached
    module_name = (
        "changeset_scope"
        if cached is None
        else "changeset_scope_"
        + hashlib.sha256(str(resolved_path).encode()).hexdigest()
    )
    path_cached = sys.modules.get(module_name)
    if path_cached is not None and _module_origin(path_cached) == resolved_path:
        return path_cached
    spec = importlib.util.spec_from_file_location(module_name, resolved_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {_CHANGESET_SCOPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_changeset_scope = _load_changeset_scope()
detect_base_ref = _changeset_scope.detect_base_ref
branch_scope = _changeset_scope.branch_scope
BaseRefNotConfiguredError = _changeset_scope.BaseRefNotConfiguredError


def derive_changeset_scope(repo: pathlib.Path) -> dict[str, object]:
    """Return the canonical base and complete branch scope for ``repo``."""
    resolved_repo = repo.resolve()
    base_ref = detect_base_ref(resolved_repo)
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        BASE_REF_FIELD: base_ref,
        CHANGED_FILES_FIELD: branch_scope(base_ref, repo=resolved_repo),
        ERROR_FIELD: None,
    }


def _error_payload(error: str, remediation: str) -> dict[str, object]:
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        ERROR_FIELD: error,
        REMEDIATION_FIELD: remediation,
    }


def main(argv: list[str]) -> int:
    """Parse the repository path and emit one newline-terminated JSON object."""
    parser = argparse.ArgumentParser(
        description="Derive the complete branch changeset scope for alignment."
    )
    parser.add_argument("repo", nargs="?", default=".")
    args = parser.parse_args(argv[1:])
    repo = pathlib.Path(args.repo)
    if not repo.is_dir():
        sys.stderr.write(
            json.dumps(
                _error_payload(
                    f"Repository path is not a directory: {repo}",
                    "Pass the path to an existing Git repository.",
                )
            )
            + "\n"
        )
        return 2

    try:
        payload = derive_changeset_scope(repo)
    except BaseRefNotConfiguredError as error:
        sys.stderr.write(
            json.dumps(_error_payload(str(error), BASE_REF_REMEDIATION)) + "\n"
        )
        return 1
    except (OSError, subprocess.CalledProcessError) as error:
        sys.stderr.write(
            json.dumps(_error_payload(str(error), GIT_SCOPE_REMEDIATION)) + "\n"
        )
        return 1

    sys.stdout.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
