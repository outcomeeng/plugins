"""Resolve an implementation audit selector through the shared scope provider."""

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
from types import ModuleType

ERROR_PREFIX = "error: implementation scope resolution failed"


def _provider() -> ModuleType:
    skills = pathlib.Path(__file__).resolve().parents[2]
    path = skills / "scope-changeset" / "scripts" / "changeset_scope.py"
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", help="HEAD, a branch, or a three-dot range")
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument(
        "--audit-input",
        help="JSON object merged beneath the resolved scope to form a run-start input",
    )
    args = parser.parse_args(argv)
    try:
        scope = _provider()
    except (ImportError, OSError) as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    try:
        resolved = scope.resolve_committed_scope(
            args.scope, repo=args.repo, runner=subprocess.run
        )
    except scope.ScopeResolutionError as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    if args.audit_input is not None:
        try:
            resolved = {**json.loads(args.audit_input), **resolved}
        except (json.JSONDecodeError, TypeError) as exc:
            print(
                f"{ERROR_PREFIX}: --audit-input must be a JSON object: {exc}",
                file=sys.stderr,
            )
            return 2
    print(json.dumps(resolved, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
