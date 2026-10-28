"""Resolve the committed changeset scope for the test-evidence audit.

Emits `base`, `head`, and `changed_paths` as one JSON object on stdout. The
resolution logic is owned by the `scope-changeset` provider and reached by the
installed tree's `__file__`-relative layout; nothing is re-implemented here.

Portability: stdlib only.

Tested with: `HEAD` in a repository with a remote base, which emits `base`,
`head`, and `changed_paths` and exits 0; a malformed range (`HEAD...`), an
unresolvable branch name, and a nonexistent `--repo` path, each of which exits
2 with a one-line `error: test-evidence scope resolution failed` diagnostic and
no traceback or scope JSON; a copy of this script placed where the sibling
`scope-changeset` provider is absent, which exits 2 with the unloadable-provider
diagnostic. The stale-base refusal is the provider's own exit code and
diagnostic, relayed unchanged and covered by the provider-relay test of the
changeset-coherence node. The script writes no file and leaves nothing to clean
up.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys

ERROR_PREFIX = "error: test-evidence scope resolution failed"
PROVIDER_RELPATH = ("scope-changeset", "scripts", "changeset_scope.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selector", help="HEAD, a branch, or a three-dot range.")
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    args = parser.parse_args(argv)
    path = (
        pathlib.Path(__file__)
        .resolve()
        .parent.parent.parent.joinpath(*PROVIDER_RELPATH)
    )
    try:
        spec = importlib.util.spec_from_file_location("changeset_scope", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load changeset_scope from {path}")
        scope = importlib.util.module_from_spec(spec)
        sys.modules["changeset_scope"] = scope
        spec.loader.exec_module(scope)
    except (ImportError, OSError) as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    try:
        resolved = scope.resolve_committed_scope(
            args.selector, repo=args.repo, runner=subprocess.run
        )
    except scope.StaleBaseError as exc:
        print(json.dumps(exc.diagnostic(), sort_keys=True), file=sys.stderr)
        return int(scope.EXIT_STALE_BASE)
    except scope.ScopeResolutionError as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(resolved, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
