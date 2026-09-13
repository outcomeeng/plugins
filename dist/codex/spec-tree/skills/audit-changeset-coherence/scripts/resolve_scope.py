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
        raise ImportError(f"cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


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
        scope = _load_changeset_scope()
    except ImportError as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    try:
        resolved = scope.resolve_committed_scope(
            args.scope, repo=args.repo, runner=subprocess.run
        )
    except scope.ScopeResolutionError as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(resolved, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
