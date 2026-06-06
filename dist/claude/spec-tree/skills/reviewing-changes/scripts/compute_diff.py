"""CLI: compute the working diff against the resolved base ref.

Resolves the current thread (via ``thread_store.current_slug()``,
which honors ``SPX_VERIFY_BRANCH`` or falls back to git current branch),
reads the optional ``changes.json`` override from the thread, resolves
``base_ref`` from the precedence chain (env → file → git symbolic-ref),
resolves ``head_ref`` from a parallel precedence chain
(``SPX_VERIFY_HEAD_REF`` env → ``changes.json`` ``head_ref`` field →
literal ``HEAD``), runs ``git diff <base_ref>...<head_ref>`` (three-dot,
merge-base) via ``subprocess``, and emits the diff to stdout. Every filesystem effect against the thread-store backend
routes through the ``thread_store`` facade.

Exit codes:

- ``0`` — the diff was produced (possibly empty).
- non-zero — slug derivation failed, the optional ``changes.json`` is
  malformed, no ``base_ref`` could be resolved from any source, or git
  itself fails.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from types import ModuleType

CHANGES_RECORD_NAME = "changes.json"
ENV_BASE_REF = "SPX_VERIFY_BASE_REF"
ENV_HEAD_REF = "SPX_VERIFY_HEAD_REF"
DEFAULT_HEAD_REF = "HEAD"


def _load_thread_store() -> ModuleType:
    """Load the ``thread_store`` facade via ``importlib``.

    The facade lives at
    ``plugins/spec-tree/skills/thread-store/scripts/thread_store.py``.
    Resolving it via ``__file__`` keeps the import independent of
    ``sys.path[0]`` and of the consumer's working directory.
    """
    cached = sys.modules.get("thread_store")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "thread-store"
        / "scripts"
        / "thread_store.py"
    )
    spec = importlib.util.spec_from_file_location("thread_store", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load thread_store from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["thread_store"] = module
    spec.loader.exec_module(module)
    return module


def _load_changeset_scope() -> ModuleType:
    """Load the ``changeset_scope`` module via ``importlib``.

    The canonical git-derivation home lives at
    ``plugins/spec-tree/skills/changeset-scope/scripts/changeset_scope.py``
    and surfaces ``detect_base_ref``, ``remote_tracking_ref``, and
    ``BaseRefNotConfiguredError``. Loading here keeps the strict base-ref
    derivation and the remote-tracking composition a single source rather
    than a private duplicate inside this script.
    """
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "changeset-scope"
        / "scripts"
        / "changeset_scope.py"
    )
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


def _read_changes_json(thread_store: ModuleType, slug: str) -> dict[str, object] | None:
    """Return the parsed ``changes.json`` override, or ``None`` when absent.

    A missing record is the happy path for auto-derivation. A malformed
    record (not JSON, not a dict) is a hard error — the caller asked for
    an override but supplied something this skill cannot read.
    """
    try:
        payload = thread_store.read(slug, CHANGES_RECORD_NAME)
    except thread_store.NotFound:
        return None
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{CHANGES_RECORD_NAME} is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"{CHANGES_RECORD_NAME} must be a JSON object")
    return parsed


def _resolve_head_ref(changes: dict[str, object] | None) -> str:
    """Resolve head_ref via env → file → literal ``HEAD``.

    Symmetric with ``_resolve_base_ref`` but with a literal default so
    the common "diff against current HEAD" case requires no
    configuration. Same precedence: env overrides file overrides default.
    """
    env_value = os.environ.get(ENV_HEAD_REF, "").strip()
    if env_value:
        return env_value
    if changes is not None:
        file_value = changes.get("head_ref")
        if isinstance(file_value, str) and file_value:
            return file_value
    return DEFAULT_HEAD_REF


def _resolve_base_ref(changes: dict[str, object] | None) -> str:
    """Resolve base_ref via env → file → git, aborting when no source yields one.

    The error message names every source so the operator knows which to
    populate. No fallback to a literal default — silent fallbacks would
    let a diff compute against the wrong ref without surfacing it. The
    strict git derivation delegates to ``changeset_scope.detect_base_ref(strict=True)``
    so the symbolic-ref read lives in one source, then composes the
    remote-tracking ref via ``changeset_scope.remote_tracking_ref`` so a
    stale local branch ref cannot widen the diff. Env and ``changes.json``
    values are used verbatim — the operator owns those.
    """
    env_value = os.environ.get(ENV_BASE_REF, "").strip()
    if env_value:
        return env_value
    if changes is not None:
        file_value = changes.get("base_ref")
        if isinstance(file_value, str) and file_value:
            return file_value
    changeset_scope = _load_changeset_scope()
    try:
        bare_base = changeset_scope.detect_base_ref(pathlib.Path.cwd(), strict=True)
    except changeset_scope.BaseRefNotConfiguredError as exc:
        raise RuntimeError(
            "cannot resolve base_ref from any source; tried: "
            f"{ENV_BASE_REF} env, {CHANGES_RECORD_NAME} 'base_ref' field, "
            f"git symbolic-ref refs/remotes/origin/HEAD ({exc})"
        ) from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            "cannot resolve base_ref from any source; tried: "
            f"{ENV_BASE_REF} env, {CHANGES_RECORD_NAME} 'base_ref' field, "
            f"git symbolic-ref refs/remotes/origin/HEAD (git is not on PATH)"
        ) from exc
    return str(changeset_scope.remote_tracking_ref(bare_base))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute git diff against the resolved base ref."
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="thread slug; derived via thread_store.current_slug() when omitted",
    )
    args = parser.parse_args(argv)

    thread_store = _load_thread_store()
    slug = args.slug
    if slug is None:
        try:
            slug = thread_store.current_slug()
        except thread_store.ConfigurationError as exc:
            sys.stderr.write(f"{exc}\n")
            return 1

    try:
        changes = _read_changes_json(thread_store, slug)
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except thread_store.ThreadStoreError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    try:
        base_ref = _resolve_base_ref(changes)
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    head_ref = _resolve_head_ref(changes)

    completed = subprocess.run(  # noqa: S603 — refs derived from validated sources
        # Three-dot (merge-base) diff: what head_ref added since branching from base_ref.
        ["git", "diff", f"{base_ref}...{head_ref}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode
    sys.stdout.write(completed.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
