"""CLI: compute the working diff against the resolved base ref.

Resolves ``base_ref`` from the precedence chain (env -> git symbolic-ref),
resolves ``head_ref`` from a parallel precedence chain
(``SPX_VERIFY_HEAD_REF`` env -> literal ``HEAD``), emits the committed
merge-base diff, then appends staged, unstaged, and untracked worktree diffs.

Exit codes:

- ``0`` — the diff was produced (possibly empty).
- non-zero — no ``base_ref`` could be resolved from any source, or git itself
  fails.

Tested with:

- ``SPX_VERIFY_BASE_REF`` -> emits the committed diff.
- Staged, unstaged, and untracked worktree changes -> emits all four sections.
- ``origin/HEAD`` derivation without env -> emits the diff.
- ``SPX_VERIFY_HEAD_REF`` overrides the default ``HEAD`` head ref.
- Missing base-ref sources -> exits non-zero and names env and git sources.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import pathlib
import subprocess
import sys
from types import ModuleType

ENV_BASE_REF = "SPX_VERIFY_BASE_REF"
ENV_HEAD_REF = "SPX_VERIFY_HEAD_REF"
DEFAULT_HEAD_REF = "HEAD"
DIFF_SECTION_COMMITTED = "Committed diff"
DIFF_SECTION_STAGED = "Staged diff"
DIFF_SECTION_UNSTAGED = "Unstaged diff"
DIFF_SECTION_UNTRACKED = "Untracked files"


def _load_changeset_scope() -> ModuleType:
    """Load the ``changeset_scope`` module via ``importlib``.

    The canonical git-derivation home lives at
    ``plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py``
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
        / "scope-changeset"
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


def _resolve_head_ref() -> str:
    """Resolve head_ref via env -> literal ``HEAD``.

    Symmetric with ``_resolve_base_ref`` but with a literal default so
    the common "diff against current HEAD" case requires no
    configuration.
    """
    env_value = os.environ.get(ENV_HEAD_REF, "").strip()
    if env_value:
        return env_value
    return DEFAULT_HEAD_REF


def _resolve_base_ref() -> str:
    """Resolve base_ref via env -> git, aborting when no source yields one.

    The error message names every source so the operator knows which to
    populate. No fallback to a literal default — silent fallbacks would
    let a diff compute against the wrong ref without surfacing it. The
    strict git derivation delegates to ``changeset_scope.detect_base_ref(strict=True)``
    so the symbolic-ref read lives in one source, then composes the
    remote-tracking ref via ``changeset_scope.remote_tracking_ref`` so a
    stale local branch ref cannot widen the diff. Env values are used verbatim
    because the operator owns explicit override refs.
    """
    env_value = os.environ.get(ENV_BASE_REF, "").strip()
    if env_value:
        return env_value
    changeset_scope = _load_changeset_scope()
    try:
        bare_base = changeset_scope.detect_base_ref(pathlib.Path.cwd(), strict=True)
    except changeset_scope.BaseRefNotConfiguredError as exc:
        raise RuntimeError(
            "cannot resolve base_ref from any source; tried: "
            f"{ENV_BASE_REF} env, git symbolic-ref refs/remotes/origin/HEAD ({exc})"
        ) from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            "cannot resolve base_ref from any source; tried: "
            f"{ENV_BASE_REF} env, git symbolic-ref refs/remotes/origin/HEAD "
            "(git is not on PATH)"
        ) from exc
    return str(changeset_scope.remote_tracking_ref(bare_base))


def _git_diff(args: list[str]) -> str:
    completed = subprocess.run(  # noqa: S603 — refs derived from validated sources
        ["git", "diff", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr)
    return completed.stdout


def _git_stdout(args: list[str]) -> str:
    completed = subprocess.run(  # noqa: S603 — fixed git subcommands
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr)
    return completed.stdout


def _diff_section(title: str, diff: str) -> str:
    if not diff:
        return ""
    return f"### {title}\n\n{diff}"


def _untracked_diff() -> str:
    paths = [
        line
        for line in _git_stdout(
            ["ls-files", "--others", "--exclude-standard", "-z"]
        ).split("\0")
        if line
    ]
    sections: list[str] = []
    for path in paths:
        completed = subprocess.run(  # noqa: S603 — paths come from git ls-files
            ["git", "diff", "--no-index", "--", os.devnull, path],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode not in (0, 1):
            raise RuntimeError(completed.stderr)
        sections.append(completed.stdout)
    return "\n".join(sections)


def combined_diff(base_ref: str, head_ref: str) -> str:
    """Return committed, staged, unstaged, and untracked diffs as one review input."""
    sections = (
        _diff_section(
            DIFF_SECTION_COMMITTED,
            _git_diff([f"{base_ref}...{head_ref}"]),
        ),
        _diff_section(DIFF_SECTION_STAGED, _git_diff(["--cached"])),
        _diff_section(DIFF_SECTION_UNSTAGED, _git_diff([])),
        _diff_section(DIFF_SECTION_UNTRACKED, _untracked_diff()),
    )
    return "\n".join(section for section in sections if section)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute git diff against the resolved base ref."
    )
    parser.parse_args(argv)

    try:
        base_ref = _resolve_base_ref()
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    head_ref = _resolve_head_ref()

    try:
        diff = combined_diff(base_ref, head_ref)
    except RuntimeError as exc:
        sys.stderr.write(str(exc))
        return 1
    sys.stdout.write(diff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
