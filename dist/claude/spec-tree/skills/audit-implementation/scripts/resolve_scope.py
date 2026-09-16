"""Resolve an implementation audit selector and reconcile a run against it.

Tested before this script is bundled by the audit node's
``test_implementation_scope.scenario.l1.py`` (stale-local-base resolution, a
nonexistent repository) and ``test_implementation_scope.compliance.l1.py``
(a run-input object whose keys cannot displace the git-resolved scope, a
non-object and a malformed run-input value, a sealed inventory path carrying no
recorded scope unit, a required unit outside the final coverage statuses beside
an optional unit carrying the same status, exact inventory agreement, drift in
both directions, a recorded subject outside the inventory, a missing-skill unit
naming its absent skill, an advisory live path beside the committed inventory, a reconcile request carrying no sealed
scope identity, a run token the CLI cannot read, a CLI that cannot be launched,
a run document shaped so the comparison cannot run, and a head behind the
fetched base relayed as the stale-base refusal).

The provider is reached by the installed tree's `__file__`-relative layout,
the plugin build's contract for logic one provider skill owns and several
consumers execute.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
from collections.abc import Mapping, Sequence
from enum import StrEnum
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # The provider skill publishes the process-boundary Protocol every consumer
    # accepts; `_provider()` loads the same module by path at run time.
    from changeset_scope import Runner

ERROR_PREFIX = "error: implementation scope resolution failed"
RECONCILE_PREFIX = "error: implementation audit reconciliation failed"
SPX_COMMAND = "spx"
RUN_COMMAND_PREFIX = ("verification", "run")
INPUT_COMMAND = "input"
RENDER_COMMAND = "render"
SCOPE_OPTION = "--scope"
# Audit-input key under which an advisory (`worktree:`) audit carries its live
# modified and untracked paths; a committed audit omits it.
LIVE_PATHS_KEY = "live_paths"
# Exit 1 is a readable run that does not reconcile; exit 2 is a request or
# command this script cannot carry out. The two never overlap.
EXIT_UNRECONCILED = 1
EXIT_COMMAND_FAILURE = 2
SCOPE_IDENTITY_OPTION = "--scope-identity"
REQUIRED_COVERAGE = "required"
# A missing-skill unit names the absent concern skill as its subject rather
# than a path, so it stands beside the path units and never counts as a
# recorded subject outside the inventory.
MISSING_SKILL_STATUS = "missing-skill"
FINAL_COVERAGE_STATUSES = frozenset(
    {"audited", "not-applicable", MISSING_SKILL_STATUS, "unsupported"}
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
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    skills = pathlib.Path(__file__).resolve().parents[2]
    path = skills / "scope-changeset" / "scripts" / "changeset_scope.py"
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        # A module that failed to execute never stays cached as if it loaded.
        del sys.modules[spec.name]
        raise
    return module


def read_run_document(
    runner: Runner, repo: pathlib.Path, argv: Sequence[str], field: str
) -> object:
    """Return the last `spx verification run` document carrying ``field``."""
    completed = runner(
        [SPX_COMMAND, *RUN_COMMAND_PREFIX, *argv],
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


def reconcile(
    expected_paths: Sequence[str],
    resolved_paths: Sequence[str],
    scope_units: Sequence[Mapping[str, object]],
    live_paths: Sequence[str] = (),
) -> dict[str, object]:
    """Return the verdict comparing recorded coverage to the sealed inventory.

    ``live_paths`` is the advisory live list the run's start input sealed, if
    any: those paths are expected subjects beside the committed inventory, but
    drift is judged on the committed inventory alone.
    """
    expected = list(expected_paths)
    expected += [path for path in live_paths if path not in expected]
    recorded = {
        str(unit.get(AuditField.SUBJECT))
        for unit in scope_units
        if unit.get(AuditField.COVERAGE_STATUS) != MISSING_SKILL_STATUS
    }
    verdict: dict[str, object] = {
        ReconcileField.EXPECTED: len(expected),
        ReconcileField.RECORDED: len(recorded),
        ReconcileField.UNACCOUNTED: [p for p in expected if p not in recorded],
        ReconcileField.UNEXPECTED: sorted(s for s in recorded if s not in expected),
        ReconcileField.DRIFTED: sorted(set(expected_paths) ^ set(resolved_paths)),
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


def _reconcile_run(
    runner: Runner,
    scope: ModuleType,
    args: argparse.Namespace,
    resolved: Mapping[str, object],
) -> int:
    # The locator carries the run's own sealed scope identity, never the freshly
    # resolved one: a drifted selector resolves to an identity SPX cannot match
    # against the recorded run, which would surface drift as a command failure
    # rather than as the `drifted` field reporting it.
    locator = [
        "--verification-type",
        "audit",
        "--scope-type",
        "changeset",
        SCOPE_OPTION,
        args.scope_identity,
        "--run",
        args.reconcile_run,
    ]
    # A run this script cannot read — a launch that fails before spx runs
    # (OSError), a nonzero spx exit, a document without the field, or a
    # document shaped so the comparison cannot run — is a command failure.
    try:
        content = read_run_document(
            runner, args.repo, [INPUT_COMMAND, *locator], AuditField.INPUT_CONTENT
        )
        if not isinstance(content, str):
            raise RuntimeError("recorded start input content is not a string")
        recorded_input = json.loads(content)
        units = read_run_document(
            runner, args.repo, [RENDER_COMMAND, *locator], AuditField.SCOPE_UNITS
        )
        if not isinstance(recorded_input, dict):
            raise RuntimeError("recorded start input is not a JSON object")
        if not isinstance(units, list) or not all(isinstance(u, dict) for u in units):
            raise RuntimeError("recorded scope units are not a list of objects")
        sealed = recorded_input.get(scope.ScopeField.CHANGED_PATHS) or []
        live = recorded_input.get(LIVE_PATHS_KEY) or []
        fresh = resolved[scope.ScopeField.CHANGED_PATHS]
        if (
            not isinstance(sealed, list)
            or not isinstance(live, list)
            or not isinstance(fresh, list)
        ):
            raise RuntimeError("recorded start input path lists are not arrays")
        verdict = reconcile(sealed, fresh, units, live)
    except (OSError, RuntimeError, TypeError, json.JSONDecodeError) as exc:
        print(f"{RECONCILE_PREFIX}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
    print(json.dumps(verdict, sort_keys=True))
    return 0 if verdict[ReconcileField.RECONCILED] else EXIT_UNRECONCILED


def main(argv: list[str] | None = None, runner: Runner = subprocess.run) -> int:
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
    except scope.StaleBaseError as exc:
        # The refusal is the verdict, not a command failure: the selector
        # resolved, and the head is not the tree that would merge.
        print(json.dumps(exc.diagnostic(), sort_keys=True), file=sys.stderr)
        return int(scope.EXIT_STALE_BASE)
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
