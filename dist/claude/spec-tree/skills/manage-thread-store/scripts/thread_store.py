"""Facade for the thread-store CRUD API.

Selects a backend at runtime via ``SPX_VERIFY_BACKEND`` (default ``local``,
which resolves to the filesystem backend) and exposes the same
five-method CRUD surface declared by the ``Backend`` protocol.

Stdlib-only. Imports its sibling modules by name; callers load the
facade via ``importlib`` and the runtime resolves the siblings through
``sys.modules`` cache after the harness pre-loads them, or through the
``sys.path[0]`` directory when ``python3 path/to/thread_store.py``
invokes the module as a script.
"""

from __future__ import annotations

import builtins
import importlib.util
import os
import pathlib
import sys
from collections.abc import Callable
from types import ModuleType
from typing import Any


ENV_BACKEND = "SPX_VERIFY_BACKEND"
DEFAULT_BACKEND_NAME = "local"

# Override env for ``current_slug()`` — when set, the value is the
# branch name the helper feeds into ``branch_slug``. Backend-agnostic:
# the local backend translates branch → slug via ``branch_slug``; a
# future ``gh_pr`` backend would translate branch → PR number.
ENV_BRANCH = "SPX_VERIFY_BRANCH"


# Exception types are declared in ``errors.py`` so backend modules can
# raise them without forming an import cycle with this facade. Loaded
# eagerly through ``_load_sibling`` below; re-exported as
# ``thread_store.NotFound``, ``ThreadStoreError``, and
# ``ConfigurationError`` for consumers that import the facade only.


# Backend registry: name → factory that returns a fresh backend instance.
_BACKEND_FACTORIES: dict[str, Callable[[], object]] = {}

# Required method names every Backend implementation exposes.
_REQUIRED_BACKEND_METHODS = ("thread_path", "write", "read", "delete", "list")


def _load_sibling(module_name: str) -> ModuleType:
    """Load a sibling script via ``importlib`` if not already loaded.

    Allows ``thread_store`` to import ``backend``/``fs_backend`` whether
    callers use the importlib path (the test harness pre-loads them) or
    direct ``python3 thread_store.py`` invocation (``sys.path[0]`` is
    the scripts directory).
    """
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    module_path = pathlib.Path(__file__).resolve().parent / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load sibling module {module_name} from {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def register_backend(name: str, factory: Callable[[], object]) -> None:
    """Register ``factory`` under ``name`` after verifying conformance.

    The factory is invoked once to probe the produced backend's method
    surface; ``ConfigurationError`` is raised when the result lacks any
    method declared by the ``Backend`` protocol. Conformant factories
    are stored for later resolution by :func:`get_backend`.
    """
    sample = factory()
    missing = [
        method
        for method in _REQUIRED_BACKEND_METHODS
        if not callable(getattr(sample, method, None))
    ]
    if missing:
        raise ConfigurationError(
            f"backend {name!r} is missing required method(s): {', '.join(missing)}"
        )
    _BACKEND_FACTORIES[name] = factory


def _register_default_backends() -> None:
    """Register the filesystem backend under ``local`` on module import.

    Idempotent — re-importing ``thread_store`` does not duplicate the
    registration.
    """
    if DEFAULT_BACKEND_NAME in _BACKEND_FACTORIES:
        return
    fs_backend = _load_sibling("fs_backend")
    register_backend(DEFAULT_BACKEND_NAME, fs_backend.FilesystemBackend.from_env)


# Ensure the ``backend`` protocol module and the ``errors`` module are
# loadable for type/import resolution, then register the filesystem
# backend so ``get_backend()`` resolves on first invocation.
_load_sibling("backend")
_errors = _load_sibling("errors")
ThreadStoreError = _errors.ThreadStoreError
NotFound = _errors.NotFound
ConfigurationError = _errors.ConfigurationError
_register_default_backends()


def get_backend() -> Any:
    """Resolve and return the backend selected by ``SPX_VERIFY_BACKEND``.

    Defaults to ``local`` when the env var is unset. Raises
    ``ConfigurationError`` with the unknown name and the set of
    registered names when the selection is not recognized.

    The return annotation is ``Any`` because the ``Backend`` protocol
    sibling module is not a discoverable package (it ships under a
    runtime-substituted plugin directory and is loaded via importlib),
    so a static ``Backend`` annotation would require module discovery
    machinery mypy does not provide here. The runtime-checkable
    ``Backend`` Protocol enforces shape at facade-registration time.
    """
    name = os.environ.get(ENV_BACKEND, DEFAULT_BACKEND_NAME)
    factory = _BACKEND_FACTORIES.get(name)
    if factory is None:
        registered = ", ".join(sorted(_BACKEND_FACTORIES)) or "(none)"
        raise ConfigurationError(
            f"backend {name!r} is not registered; registered backends: {registered}"
        )
    return factory()


# ---------------------------------------------------------------------------
# CRUD surface — every operation routes through ``get_backend()``.
# ---------------------------------------------------------------------------


def write(slug: str, name: str, payload: bytes) -> None:
    """Persist ``payload`` under ``(slug, name)`` via the selected backend."""
    get_backend().write(slug, name, payload)


def read(slug: str, name: str) -> bytes:
    """Return the payload stored under ``(slug, name)``.

    Raises :class:`NotFound` when no record exists.
    """
    result: bytes = get_backend().read(slug, name)
    return result


def delete(slug: str, name: str) -> None:
    """Remove the record at ``(slug, name)``.

    Raises :class:`NotFound` when no record exists.
    """
    get_backend().delete(slug, name)


def list(slug: str) -> "builtins.list[str]":  # noqa: A001 — module-level CRUD surface mirrors the protocol
    """Return the record names present under ``slug``."""
    names: builtins.list[str] = get_backend().list(slug)
    return names


# ---------------------------------------------------------------------------
# Slug derivation — the CRUD CLIs fall back to this when ``--slug`` is omitted.
# ---------------------------------------------------------------------------


def current_slug() -> str:
    """Return the slug for the current thread, derived from env or git.

    Source precedence:

    1. ``SPX_VERIFY_BRANCH`` env — explicit, backend-agnostic override
    2. ``git symbolic-ref --short HEAD`` in the current working
       directory — the operator's current branch

    Detached HEAD or missing git aborts with a structured error message
    that names the ``SPX_VERIFY_BRANCH`` override so the operator can
    recover without reading source.

    Slug derivation itself is delegated to the canonical
    ``branch_slug`` re-exported from the audit skill.
    """
    branch_slug_mod = _load_sibling("branch_slug")
    branch = os.environ.get(ENV_BRANCH, "").strip()
    if branch:
        return str(branch_slug_mod.branch_slug(branch))
    try:
        branch = branch_slug_mod.detect_current_branch(pathlib.Path.cwd())
    except branch_slug_mod.DetachedHeadError as exc:
        raise ConfigurationError(
            f"cannot derive slug on detached HEAD; set {ENV_BRANCH} to override: {exc}"
        ) from exc
    except FileNotFoundError as exc:
        # ``subprocess.run`` raises FileNotFoundError when git is not on PATH.
        raise ConfigurationError(
            f"cannot derive slug: git is not on PATH; set {ENV_BRANCH} to override"
        ) from exc
    return str(branch_slug_mod.branch_slug(branch))
