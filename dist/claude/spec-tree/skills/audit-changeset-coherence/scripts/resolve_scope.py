"""Resolve the exact committed changeset scope for the coherence audit.

Emits the base and head commit identities and the changed-file set the audit
classifies, as one JSON object on stdout. The audit skill names no caller and
stays invocable on its own, so it resolves its own scope here rather than
requiring a caller-prepared packet.

Base-ref resolution, remote-tracking-ref composition, commit-identity
resolution, and diff scope route through the canonical `changeset_scope`
module — never re-implemented here — per the `scope-changeset` skill's
contract. Composing against `origin/<base>` keeps the merge base at the true
branch point, so commits already merged into the base never re-enter the
scope of a multi-worktree checkout.

Portability: stdlib only — no third-party packages, no `uv`, no `outcomeeng_*`
imports. This script ships into consumer plugin trees where only the standard
library is available.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
from types import ModuleType

_CHANGESET_SCOPE_RELPATH = ("scope-changeset", "scripts", "changeset_scope.py")
ERROR_PREFIX = "error: coherence scope resolution failed"
RANGE_SEPARATOR = "..."


class ScopeResolutionError(RuntimeError):
    """The audit cannot resolve an exact committed changeset."""


def _load_changeset_scope() -> ModuleType:
    """Load the sibling `changeset_scope` module via the co-location convention.

    The module lives at `plugins/spec-tree/skills/scope-changeset/scripts/
    changeset_scope.py`, resolved relative to this script so no path is
    hard-coded in agent prose. Cached in `sys.modules` so repeated loads in one
    process reuse the same module object.
    """
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    skills_dir = pathlib.Path(__file__).resolve().parent.parent.parent
    path = skills_dir.joinpath(*_CHANGESET_SCOPE_RELPATH)
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise ScopeResolutionError(f"cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


def _resolve_range(
    scope: ModuleType, spec: str, repo: pathlib.Path
) -> dict[str, object]:
    """Resolve an explicit `<base>...<head>` range to identities and paths.

    The caller supplied both endpoints, so the base is taken verbatim rather
    than derived: an explicit range is already an exact committed scope, and
    re-deriving it would discard the endpoints the caller named.
    """
    base_spec, _, head_spec = spec.partition(RANGE_SEPARATOR)
    if not base_spec or not head_spec:
        raise ScopeResolutionError(
            f"malformed commit range: {spec!r} — expected '<base>...<head>', "
            "for example 'origin/main...HEAD'"
        )
    return {
        "base": scope.commit_oid(base_spec, repo=repo),
        "head": scope.commit_oid(head_spec, repo=repo),
        "changed_paths": scope.expand_diff_range(spec, repo=repo),
    }


def _resolve_branch(
    scope: ModuleType, ref: str, repo: pathlib.Path
) -> dict[str, object]:
    """Resolve a branch or `HEAD` against its configured remote base.

    The range is composed against the supplied `ref` rather than through
    `branch_scope`, whose range template fixes the far end at `HEAD`: an audit
    invoked on a branch that is not the checked-out one would otherwise record
    that branch's head identity beside the checked-out branch's paths and
    classify the wrong changeset. Composition still goes through
    `remote_tracking_ref`, the single source of the `origin/` form, so a bare
    local base ref never widens the scope.
    """
    base_ref = scope.detect_base_ref(repo)
    origin_ref = scope.remote_tracking_ref(base_ref)
    return {
        "base": scope.commit_oid(origin_ref, repo=repo),
        "head": scope.commit_oid(ref, repo=repo),
        "changed_paths": scope.expand_diff_range(
            f"{origin_ref}{RANGE_SEPARATOR}{ref}", repo=repo
        ),
    }


def resolve(spec: str, repo: pathlib.Path) -> dict[str, object]:
    """Return the exact committed scope for `spec` as a JSON-ready mapping."""
    scope = _load_changeset_scope()
    try:
        if RANGE_SEPARATOR in spec:
            return _resolve_range(scope, spec, repo)
        return _resolve_branch(scope, spec, repo)
    except subprocess.CalledProcessError as exc:
        raise ScopeResolutionError(
            f"git could not resolve {spec}: {(exc.stderr or '').strip()}"
        ) from exc
    except (
        getattr(scope, "BaseRefNotConfiguredError", RuntimeError),
        getattr(scope, "DetachedHeadError", RuntimeError),
    ) as exc:
        raise ScopeResolutionError(str(exc)) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve the committed changeset scope for the coherence audit."
    )
    parser.add_argument(
        "scope",
        help="A branch name, HEAD, or an explicit <base>...<head> commit range.",
    )
    parser.add_argument(
        "--repo",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="Repository working tree (default: current directory).",
    )
    args = parser.parse_args(argv)
    try:
        resolved = resolve(args.scope, args.repo)
    except ScopeResolutionError as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(resolved, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
