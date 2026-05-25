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


def _load_branch_slug() -> ModuleType:
    """Load the ``branch_slug`` re-export module via ``importlib``.

    The re-export lives at
    ``plugins/spec-tree/skills/thread-store/scripts/branch_slug.py`` and
    surfaces the canonical git helpers from ``audit_orchestrator``
    (``detect_base_ref``, ``BaseRefNotConfiguredError``). Loading here
    keeps the strict base-ref derivation a single source rather than a
    private duplicate inside this script.
    """
    cached = sys.modules.get("branch_slug")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "thread-store"
        / "scripts"
        / "branch_slug.py"
    )
    spec = importlib.util.spec_from_file_location("branch_slug", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load branch_slug from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["branch_slug"] = module
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
    strict git derivation delegates to ``audit_orchestrator.detect_base_ref(strict=True)``
    via the ``branch_slug`` re-export so the symbolic-ref read lives in
    one source.
    """
    env_value = os.environ.get(ENV_BASE_REF, "").strip()
    if env_value:
        return env_value
    if changes is not None:
        file_value = changes.get("base_ref")
        if isinstance(file_value, str) and file_value:
            return file_value
    branch_slug = _load_branch_slug()
    try:
        return str(branch_slug.detect_base_ref(pathlib.Path.cwd(), strict=True))
    except branch_slug.BaseRefNotConfiguredError as exc:
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
