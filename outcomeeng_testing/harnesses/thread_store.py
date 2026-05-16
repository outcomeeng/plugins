"""Harness for thread-store scenario, property, and compliance tests.

Provides the shared scaffolding consumed by every test file under
``spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/21-thread-store.enabler/tests/``:

- ``SCRIPTS_DIR`` and the per-script paths derived from it. A single source
  keeps every test file from walking ``__file__.parents[...]`` to find
  ``plugins/spec-tree/skills/thread-store/scripts``.
- An importlib loader for the ``thread_store`` facade module. The module
  is shipped under ``plugins/`` (a runtime-substituted plugin directory)
  and is not importable as a package; tests that need to introspect the
  facade load it through ``importlib`` instead.
- ``run_script``. A thin ``subprocess.run`` wrapper with the defaults
  every CLI test uses (``capture_output=True``, ``text=True``, optional
  stdin and env override).
- ``with_temp_local_store``. A context manager that points the local
  filesystem backend at a ``tmp_path``-rooted ``.spx/reviews`` tree by
  setting ``SPX_VET_LOCAL_ROOT`` and ``SPX_VET_BACKEND`` for the duration
  of the test, then restores prior values on exit.
- ``make_changes_json``. A factory for synthetic ``changes.json``
  override payloads — the platform-neutral override file the
  reviewing-changes lens reads from the thread store. Lives in the
  harness because consumer tests across multiple lens nodes use the
  same shape.

The harness lives in ``outcomeeng_testing/harnesses/`` per
``spx/15-test-infrastructure.pdr.md`` — shared test scaffolding is
production code with its home outside ``tests/`` and outside ``spx/``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from types import ModuleType

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/thread_store.py``.
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[2]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "thread-store"
    / "scripts"
)

THREAD_STORE_MODULE_PATH = SCRIPTS_DIR / "thread_store.py"
BACKEND_MODULE_PATH = SCRIPTS_DIR / "backend.py"
FS_BACKEND_MODULE_PATH = SCRIPTS_DIR / "fs_backend.py"
BRANCH_SLUG_MODULE_PATH = SCRIPTS_DIR / "branch_slug.py"

WRITE_RECORD_SCRIPT = SCRIPTS_DIR / "write_record.py"
READ_RECORD_SCRIPT = SCRIPTS_DIR / "read_record.py"
DELETE_RECORD_SCRIPT = SCRIPTS_DIR / "delete_record.py"
LIST_RECORDS_SCRIPT = SCRIPTS_DIR / "list_records.py"

AUDIT_ORCHESTRATOR_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
    / "audit_orchestrator.py"
)


def _load_module(module_name: str, module_path: pathlib.Path) -> ModuleType:
    """Load ``module_path`` as ``module_name`` and cache it under ``sys.modules``.

    The thread-store scripts ship under ``plugins/`` (a runtime-substituted
    plugin directory) and the marketplace ships every script under
    ``scripts/`` as a bare module that ``python3 path/to/script.py``
    invocations resolve via ``sys.path[0]``. Tests load these modules
    through ``importlib`` instead of a regular import.

    Returns the already-loaded module on subsequent calls so the importlib
    loader runs at most once per test session for a given module name.
    """
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_thread_store_module() -> ModuleType:
    """Load the ``thread_store`` facade module via importlib.

    The facade depends on ``backend`` and ``fs_backend`` siblings; loading
    those first keeps the facade's top-level imports resolvable when it
    runs ``from backend import Backend`` (and similar).
    """
    _load_module("backend", BACKEND_MODULE_PATH)
    _load_module("fs_backend", FS_BACKEND_MODULE_PATH)
    _load_module("branch_slug", BRANCH_SLUG_MODULE_PATH)
    return _load_module("thread_store", THREAD_STORE_MODULE_PATH)


def load_backend_module() -> ModuleType:
    return _load_module("backend", BACKEND_MODULE_PATH)


def load_fs_backend_module() -> ModuleType:
    _load_module("backend", BACKEND_MODULE_PATH)
    return _load_module("fs_backend", FS_BACKEND_MODULE_PATH)


def load_branch_slug_module() -> ModuleType:
    return _load_module("branch_slug", BRANCH_SLUG_MODULE_PATH)


def load_audit_orchestrator_module() -> ModuleType:
    """Load the canonical ``audit_orchestrator`` module.

    Tests that verify the slug function is the same symbol the
    re-exporting helper imports load both modules and compare identity.
    """
    return _load_module("audit_orchestrator", AUDIT_ORCHESTRATOR_MODULE_PATH)


def run_script(
    script: pathlib.Path,
    *args: str,
    stdin: str | None = None,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke a CRUD CLI script as a subprocess and return the result.

    Every CLI test in the thread-store suite exercises its target via
    ``subprocess.run`` with the same flags: capture stdout/stderr, text
    mode, and an optional stdin payload. ``check=False`` is the default
    so tests can inspect returncode explicitly; success-path tests pass
    ``check=True`` to fail fast.

    ``env``, when provided, is the complete environment passed to the
    child process. Tests that need to control backend selection or the
    filesystem-backend root pass ``{**os.environ, "SPX_VET_BACKEND":
    "local", "SPX_VET_LOCAL_ROOT": str(tmp_path)}``.
    """
    return subprocess.run(  # noqa: S603 — script path comes from the harness, not user input
        [sys.executable, str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )


@contextmanager
def with_temp_local_store(tmp_path: pathlib.Path) -> Iterator[pathlib.Path]:
    """Point the filesystem backend at ``tmp_path`` for the duration of the test.

    Sets ``SPX_VET_BACKEND=local`` and ``SPX_VET_LOCAL_ROOT=<tmp_path>``
    in ``os.environ`` and restores the prior values (or removes the keys
    when they were not set) on exit. Yields the configured root so the
    test can assert against on-disk effects.
    """
    prior: dict[str, str | None] = {
        "SPX_VET_BACKEND": os.environ.get("SPX_VET_BACKEND"),
        "SPX_VET_LOCAL_ROOT": os.environ.get("SPX_VET_LOCAL_ROOT"),
    }
    os.environ["SPX_VET_BACKEND"] = "local"
    os.environ["SPX_VET_LOCAL_ROOT"] = str(tmp_path)
    try:
        yield tmp_path
    finally:
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def make_changes_json(
    tmp_path: pathlib.Path,
    base_ref: str,
    **kw: object,
) -> pathlib.Path:
    """Write a synthetic ``changes.json`` override payload to ``tmp_path`` and return its path.

    The reviewing-changes lens reads an optional ``changes.json`` override
    file from the thread store; this factory writes the same shape to a
    plain ``tmp_path`` location so harness tests can exercise the
    file-parsing surface without standing up a full thread-store backend.
    The minimum payload carries ``base_ref`` (the only field
    ``compute_diff.py`` consults); callers may merge additional keys for
    future extensions.

    ``base_ref`` is named explicitly because the diff range a lens
    computes is anchored on it; every caller passes one.
    """
    payload: dict[str, object] = {
        "base_ref": base_ref,
    }
    payload.update(kw)
    target = tmp_path / "changes.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target
