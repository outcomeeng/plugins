"""Resolve an implementation audit selector and reconcile a run against it.

Tested inputs and error cases: the implementation-scope scenario and compliance
suites exercise stale-local-base resolution, a nonexistent repository, a
run-input object whose keys cannot displace the git-resolved scope, a non-object
and a malformed run-input value, a sealed inventory path carrying no recorded
scope unit, a required unit outside the final coverage statuses beside an
optional unit carrying the same status, exact inventory agreement, drift in
both directions, a recorded subject outside the inventory, a reconcile request
carrying no sealed scope identity, a run token the CLI cannot read, and a CLI
that cannot be launched, before this script is bundled.
"""

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
SPX_COMMAND = "spx"
# Exit 1 is a readable run that does not reconcile; exit 2 is a request or
# command this script cannot carry out. The two never overlap.
EXIT_UNRECONCILED = 1
EXIT_COMMAND_FAILURE = 2
SCOPE_IDENTITY_OPTION = "--scope-identity"
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
        [SPX_COMMAND, "verification", "run", *argv],
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
    # The locator carries the run's own sealed scope identity, never the freshly
    # resolved one: a drifted selector resolves to an identity SPX cannot match
    # against the recorded run, which would surface drift as a command failure
    # rather than as the `drifted` field reporting it.
    locator = [
        "--verification-type",
        "audit",
        "--scope-type",
        "changeset",
        "--scope",
        args.scope_identity,
        "--run",
        args.reconcile_run,
    ]
    # A run this script cannot read — a launch that fails before spx runs
    # (OSError), a nonzero spx exit, a document without the field, or a unit
    # shaped so the comparison cannot run — is a command failure.
    try:
        recorded_input = json.loads(
            read_run_document(
                runner, args.repo, ["input", *locator], AuditField.INPUT_CONTENT
            )
        )
        units = read_run_document(
            runner, args.repo, ["render", *locator], AuditField.SCOPE_UNITS
        )
        verdict = reconcile(
            recorded_input.get(scope.ScopeField.CHANGED_PATHS) or (),
            resolved[scope.ScopeField.CHANGED_PATHS],
            units,
        )
    except (OSError, RuntimeError, TypeError, json.JSONDecodeError) as exc:
        print(f"{RECONCILE_PREFIX}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
    print(json.dumps(verdict, sort_keys=True))
    return 0 if verdict[ReconcileField.RECONCILED] else EXIT_UNRECONCILED


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
    parser.add_argument(
        SCOPE_IDENTITY_OPTION,
        help="the run's sealed <base>..<head> identity, required with --reconcile-run",
    )
    args = parser.parse_args(argv)
    if args.reconcile_run is not None and args.scope_identity is None:
        print(
            f"{RECONCILE_PREFIX}: --reconcile-run requires {SCOPE_IDENTITY_OPTION}, "
            "the sealed <base>..<head> the run was started with",
            file=sys.stderr,
        )
        return EXIT_COMMAND_FAILURE
    try:
        scope = _provider()
    except (ImportError, OSError) as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
    try:
        resolved = scope.resolve_committed_scope(
            args.scope, repo=args.repo, runner=runner
        )
    except scope.ScopeResolutionError as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
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
            return EXIT_COMMAND_FAILURE
    print(json.dumps(resolved, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
