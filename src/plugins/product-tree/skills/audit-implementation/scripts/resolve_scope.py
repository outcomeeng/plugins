"""Resolve an implementation audit selector and reconcile a run against it.

Tested before this script is bundled by the audit node's
``test_implementation_scope.scenario.l1.py`` (stale-local-base resolution, a
nonexistent repository) and ``test_implementation_scope.compliance.l1.py``
(a run-input file whose keys cannot displace the git-resolved scope, an absent
run-input file, an unreadable run-input path, JSON text passed as the run-input
value in place of a path, a run-input path given without the scratch directory,
a scratch directory that names no directory, a run-input file outside that
directory and a symbolic link inside it that points outside, a non-object and a
malformed run-input file, a sealed
inventory path carrying no recorded scope unit, a required unit outside the final coverage statuses beside
an optional unit carrying the same status, exact inventory agreement, drift in
both directions, a recorded subject outside the inventory, a missing-skill unit
naming its absent skill, an advisory live path beside the committed inventory, a reconcile request carrying no sealed
scope identity, a run token the CLI cannot read, a CLI that cannot be launched,
a run document shaped so the comparison cannot run, a head behind the
fetched base relayed as the stale-base refusal, and the registry selection
emitted per resolved path, the complete run-start document written to the
``--output`` file equal to the printed document, and an unwritable ``--output``
path refused with a diagnostic), and by the artifact-registry node's
``test_artifact_registry.mapping.l1.py`` (one path per registered artifact
selecting it and its kind's detection-less artifacts, the most specific of two
matches, and an unregistered path selecting nothing).

The changeset-scope and select-artifacts providers are reached by the
installed tree's `__file__`-relative layout, the plugin build's contract for
logic one provider skill owns and several consumers execute; this script
carries no registry reader or field vocabulary of its own.
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
    # accepts; `_scope_provider()` loads the same module by path at run time.
    from changeset_scope import Runner

ERROR_PREFIX = "error: implementation scope resolution failed"
RECONCILE_PREFIX = "error: implementation audit reconciliation failed"
# The longest excerpt of a caller-supplied value that a diagnostic echoes.
EXCERPT_LIMIT = 200
SPX_COMMAND = "spx"
RUN_COMMAND_PREFIX = ("verification", "run")
INPUT_COMMAND = "input"
RENDER_COMMAND = "render"
SCOPE_OPTION = "--scope"
# The option naming the file that receives the complete run-start input in
# place of standard output.
OUTPUT_OPTION = "--output"
# The option naming the file that holds the audit input merged beneath the
# resolved scope.
AUDIT_INPUT_OPTION = "--audit-input"
# The option naming the session scratch directory that must contain the
# audit-input file once symbolic links are followed.
SCRATCH_DIR_OPTION = "--scratch-dir"
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
# The run input carries the select-artifacts provider's selection for every
# resolved path, and for every live path an advisory audit adds, under this key.
SELECTION_KEY = "artifact_selection"


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


def _sibling_provider(skill: str, module_name: str) -> ModuleType:
    """Load a sibling provider skill's script by the installed tree's layout."""
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    skills = pathlib.Path(__file__).resolve().parents[2]
    path = skills / skill / "scripts" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None or not path.is_file():
        raise ImportError(
            f"cannot load the `{skill}` provider script {path}: the installed "
            f"tree has no importable `{module_name}.py` at that location. "
            f"Reinstall the product-tree plugin so the `{skill}` skill "
            "directory sits beside this skill's directory."
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        # A module that failed to execute never stays cached as if it loaded.
        del sys.modules[spec.name]
        raise
    return module


def _scope_provider() -> ModuleType:
    return _sibling_provider("scope-changeset", "changeset_scope")


def _selection_provider() -> ModuleType:
    return _sibling_provider("select-artifacts", "select_artifacts")


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
    command = f"{SPX_COMMAND} {' '.join((*RUN_COMMAND_PREFIX, *argv))}"
    if completed.returncode:
        detail = completed.stderr.strip() or "it wrote nothing to stderr"
        raise RuntimeError(
            f"`{command}` exited {completed.returncode}: {detail}. "
            "Confirm the run token names a run that "
            "`spx verification run start` created, and that `spx` is "
            "installed and current."
        )
    for line in reversed(completed.stdout.splitlines()):
        if not line.strip():
            continue
        try:
            document = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"`{command}` wrote a stdout line that is not JSON "
                f"({exc}): {line[:EXCERPT_LIMIT]!r}. Update `spx` to a release whose "
                "`verification run` commands print JSON documents."
            ) from exc
        if isinstance(document, dict) and field in document:
            return document[field]
    raise RuntimeError(
        f"`{command}` printed no JSON document carrying the `{field}` field. "
        "Confirm the run token names an existing run and update `spx` to a "
        f"release whose `verification run {argv[0]}` output carries `{field}`."
    )


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
            raise RuntimeError(
                f"the recorded start input `{AuditField.INPUT_CONTENT}` field is "
                f"a {type(content).__name__}, not a string holding the run-start "
                "JSON document. Start the run with `--input` set to the file "
                f"this script wrote through `{OUTPUT_OPTION}`."
            )
        recorded_input = json.loads(content)
        units = read_run_document(
            runner, args.repo, [RENDER_COMMAND, *locator], AuditField.SCOPE_UNITS
        )
        if not isinstance(recorded_input, dict):
            raise RuntimeError(
                "the recorded start input decodes to a "
                f"{type(recorded_input).__name__}, not a JSON object. Start the "
                f"run with `--input` set to the file this script wrote through "
                f"`{OUTPUT_OPTION}`."
            )
        if not isinstance(units, list) or not all(isinstance(u, dict) for u in units):
            raise RuntimeError(
                f"the rendered `{AuditField.SCOPE_UNITS}` field is a "
                f"{type(units).__name__}"
                + ("" if not isinstance(units, list) else " holding a non-object entry")
                + ", not a list of scope-unit objects. Update `spx` to a release "
                "whose `verification run render` prints scope units as objects."
            )
        sealed = recorded_input.get(scope.ScopeField.CHANGED_PATHS) or []
        live = recorded_input.get(LIVE_PATHS_KEY) or []
        fresh = resolved[scope.ScopeField.CHANGED_PATHS]
        if (
            not isinstance(sealed, list)
            or not isinstance(live, list)
            or not isinstance(fresh, list)
        ):
            raise RuntimeError(
                "the path lists are not all arrays: "
                f"`{scope.ScopeField.CHANGED_PATHS}` in the recorded start input "
                f"is a {type(sealed).__name__}, `{LIVE_PATHS_KEY}` in it is a "
                f"{type(live).__name__}, and the freshly resolved "
                f"`{scope.ScopeField.CHANGED_PATHS}` is a {type(fresh).__name__}. "
                f"Start the run with `--input` set to the file this script wrote "
                f"through `{OUTPUT_OPTION}`."
            )
        verdict = reconcile(sealed, fresh, units, live)
    except (OSError, RuntimeError, TypeError, json.JSONDecodeError) as exc:
        print(f"{RECONCILE_PREFIX}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
    print(json.dumps(verdict, sort_keys=True))
    return 0 if verdict[ReconcileField.RECONCILED] else EXIT_UNRECONCILED


def _read_audit_input(
    path: pathlib.Path, scratch_dir: pathlib.Path | None
) -> dict[str, object]:
    """Return the JSON object the audit-input file inside `scratch_dir` holds; raise `RuntimeError` naming the failure."""
    if scratch_dir is None:
        raise RuntimeError(
            f"{AUDIT_INPUT_OPTION} requires {SCRATCH_DIR_OPTION}, the session "
            "scratch directory that holds the audit-input file."
        )
    try:
        root = scratch_dir.resolve(strict=True)
        if not root.is_dir():
            raise NotADirectoryError(str(root))
    except OSError as exc:
        raise RuntimeError(
            f"{SCRATCH_DIR_OPTION} must name an existing directory, received "
            f"{str(scratch_dir)[:EXCERPT_LIMIT]!r} ({type(exc).__name__}: {exc}). "
            "Pass the session scratch directory."
        ) from exc
    try:
        confined = path.resolve(strict=True)
        if not confined.is_relative_to(root):
            raise RuntimeError(
                f"{AUDIT_INPUT_OPTION} file {str(path)[:EXCERPT_LIMIT]!r} lies outside "
                f"the {SCRATCH_DIR_OPTION} directory {str(scratch_dir)[:EXCERPT_LIMIT]!r}. "
                "Write the object to a file in the session scratch directory "
                "with the file-write tool and pass that file's path."
            )
        supplied = json.loads(confined.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"{AUDIT_INPUT_OPTION} must name a readable file holding "
            f"one JSON object, received {str(path)[:EXCERPT_LIMIT]!r} "
            f"({type(exc).__name__}: {exc}). Write the object to a file in "
            "the session scratch directory with the file-write tool and pass "
            "that file's path."
        ) from exc
    if not isinstance(supplied, dict):
        raise RuntimeError(
            f"{AUDIT_INPUT_OPTION} file {str(path)[:EXCERPT_LIMIT]!r} "
            f"holds a {type(supplied).__name__}, not a JSON object. Write one "
            "JSON object to the file."
        )
    return supplied


def main(argv: list[str] | None = None, runner: Runner = subprocess.run) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", help="HEAD, a branch, or a three-dot range")
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument(
        AUDIT_INPUT_OPTION,
        type=pathlib.Path,
        help="file holding a JSON object merged beneath the resolved scope to form a run-start input",
    )
    parser.add_argument(
        SCRATCH_DIR_OPTION,
        type=pathlib.Path,
        help="session scratch directory that must contain the audit-input file",
    )
    parser.add_argument(
        "--reconcile-run",
        help="run token whose recorded coverage is reconciled against its sealed inventory",
    )
    parser.add_argument(
        SCOPE_IDENTITY_OPTION,
        help="the run's sealed <base>..<head> identity, required with --reconcile-run",
    )
    parser.add_argument(
        OUTPUT_OPTION,
        type=pathlib.Path,
        help="file that receives the complete run-start input instead of standard output",
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
        scope = _scope_provider()
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
            resolved = {
                **_read_audit_input(args.audit_input, args.scratch_dir),
                **resolved,
            }
        except RuntimeError as exc:
            print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
            return EXIT_COMMAND_FAILURE
    # The selection is set after the merge, so no run-input key displaces it.
    try:
        selection = _selection_provider()
        registry = selection.load_artifact_registry()
    except (ImportError, OSError, ValueError) as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
    changed = resolved[scope.ScopeField.CHANGED_PATHS]
    live = resolved.get(LIVE_PATHS_KEY) or []
    if not isinstance(live, list) or not all(isinstance(p, str) for p in live):
        print(
            f"{ERROR_PREFIX}: {LIVE_PATHS_KEY} in --audit-input must be a list of "
            f"path strings, received {json.dumps(live)[:EXCERPT_LIMIT]}. Pass the modified "
            "and untracked paths as a JSON array of strings.",
            file=sys.stderr,
        )
        return EXIT_COMMAND_FAILURE
    resolved[SELECTION_KEY] = selection.selection_for_paths(
        [*changed, *(path for path in live if path not in changed)], registry
    )
    document = json.dumps(resolved, sort_keys=True)
    if args.output is None:
        print(document)
        return 0
    try:
        args.output.write_text(document + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"{ERROR_PREFIX}: cannot write {args.output}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
