"""Resolve an implementation audit selector and reconcile a run against it."""

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
from enum import StrEnum
from types import ModuleType

ERROR_PREFIX = "error: implementation scope resolution failed"
RECONCILE_PREFIX = "error: implementation audit reconciliation failed"
REQUIRED_COVERAGE = "required"
FINAL_COVERAGE_STATUSES = frozenset(
    {"audited", "not-applicable", "missing-skill", "unsupported"}
)


class AuditField(StrEnum):
    """Audit-run payload fields this reconciler reads back from SPX."""

    UNIT_ID = "unitId"
    SUBJECT = "subject"
    COVERAGE_REQUIREMENT = "coverageRequirement"
    COVERAGE_STATUS = "coverageStatus"
    SCOPE_UNITS = "auditScopeUnits"
    INPUT_CONTENT = "content"


class ReconcileField(StrEnum):
    """Fields of the reconciliation verdict this script emits."""

    EXPECTED = "expected"
    RECORDED = "recorded"
    UNACCOUNTED = "unaccounted"
    UNEXPECTED = "unexpected"
    DRIFTED = "drifted"
    NONFINAL = "nonfinal"
    RECONCILED = "reconciled"


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


def read_run_document(runner, repo, argv, field):
    """Return the last `spx verification run` document carrying ``field``."""
    completed = runner(
        ["spx", "verification", "run", *argv],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            completed.stderr.strip() or f"spx exited {completed.returncode}"
        )
    for line in reversed(completed.stdout.splitlines()):
        if not line.strip():
            continue
        document = json.loads(line)
        if field in document:
            return document[field]
    raise RuntimeError(f"no {field} in `spx verification run {argv[0]}` output")


def reconcile(expected_paths, resolved_paths, scope_units):
    """Return the verdict comparing recorded coverage to the sealed inventory."""
    expected = list(expected_paths)
    recorded = {unit.get(AuditField.SUBJECT) for unit in scope_units}
    verdict = {
        ReconcileField.EXPECTED: len(expected),
        ReconcileField.RECORDED: len(recorded),
        ReconcileField.UNACCOUNTED: [p for p in expected if p not in recorded],
        ReconcileField.UNEXPECTED: sorted(s for s in recorded if s not in expected),
        ReconcileField.DRIFTED: sorted(set(expected) ^ set(resolved_paths)),
        ReconcileField.NONFINAL: sorted(
            str(unit.get(AuditField.UNIT_ID))
            for unit in scope_units
            if unit.get(AuditField.COVERAGE_REQUIREMENT) == REQUIRED_COVERAGE
            and unit.get(AuditField.COVERAGE_STATUS) not in FINAL_COVERAGE_STATUSES
        ),
    }
    verdict[ReconcileField.RECONCILED] = not any(
        verdict[field]
        for field in (
            ReconcileField.UNACCOUNTED,
            ReconcileField.UNEXPECTED,
            ReconcileField.DRIFTED,
            ReconcileField.NONFINAL,
        )
    )
    return verdict


def _reconcile_run(runner, scope, args, resolved):
    locator = [
        "--verification-type",
        "audit",
        "--scope-type",
        "changeset",
        "--scope",
        f"{resolved[scope.ScopeField.BASE]}..{resolved[scope.ScopeField.HEAD]}",
        "--run",
        args.reconcile_run,
    ]
    try:
        recorded_input = json.loads(
            read_run_document(
                runner, args.repo, ["input", *locator], AuditField.INPUT_CONTENT
            )
        )
        units = read_run_document(
            runner, args.repo, ["render", *locator], AuditField.SCOPE_UNITS
        )
    except (RuntimeError, TypeError, json.JSONDecodeError) as exc:
        print(f"{RECONCILE_PREFIX}: {exc}", file=sys.stderr)
        return 2
    verdict = reconcile(
        recorded_input.get(scope.ScopeField.CHANGED_PATHS) or (),
        resolved[scope.ScopeField.CHANGED_PATHS],
        units,
    )
    print(json.dumps(verdict, sort_keys=True))
    return 0 if verdict[ReconcileField.RECONCILED] else 1


def main(argv: list[str] | None = None, runner=subprocess.run) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", help="HEAD, a branch, or a three-dot range")
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument(
        "--audit-input",
        help="JSON object merged beneath the resolved scope to form a run-start input",
    )
    parser.add_argument(
        "--reconcile-run",
        help="run token whose recorded coverage is reconciled against its sealed inventory",
    )
    args = parser.parse_args(argv)
    try:
        scope = _provider()
    except (ImportError, OSError) as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    try:
        resolved = scope.resolve_committed_scope(
            args.scope, repo=args.repo, runner=runner
        )
    except scope.ScopeResolutionError as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 2
    if args.reconcile_run is not None:
        return _reconcile_run(runner, scope, args, resolved)
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
