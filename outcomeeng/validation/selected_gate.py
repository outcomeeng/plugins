"""Changed-path selection for the local validation gate."""

from __future__ import annotations

import fnmatch
import importlib.util
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, TextIO, cast

from outcomeeng.validation._engine import run_check, run_recipe
from outcomeeng.validation._git import GitCommandResult, GitRunner, run_git_command
from outcomeeng.validation._model import ProcessSpawner, Recipe, Step
from outcomeeng.validation._steps import (
    ACTIONLINT_ARGV,
    CHECK_RECIPES,
    FMT_CHECK_ARGV,
    HOOK_SAFETY_ARGV,
    MYPY_ARGV,
    PREFLIGHT_STEPS,
    PYRIGHT_ARGV,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SHELLCHECK_ARGV,
    SPX_MARKDOWN_ARGV,
    SPX_VERSION_FLOOR_ARGV,
    TEST_RECIPE,
    VALIDATION_STEPS,
)

RECIPE_CHECK_FULL: Final = "check-full"
DEFAULT_BASE_REF: Final = "origin/main"
CHANGESET_SCOPE_SCRIPT: Final = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "scope-changeset"
    / "scripts"
    / "changeset_scope.py"
)
SELECTED_CHECK_PLAN_HEADER: Final = "━━━ Selected check plan ━━━"
NO_CHANGED_PATHS_REASON: Final = "no changed paths"
GIT_DISCOVERY_FAILURE_EXIT_CODE: Final = 1
GIT_DISCOVERY_ERROR_PREFIX: Final = "error: selected gate git discovery failed"
FULL_GATE_REASON: Final = "full gate surface changed"
PYTHON_REASON: Final = "python source or test path changed"
MARKDOWN_REASON: Final = "markdown or spec path changed"
WORKFLOW_REASON: Final = "workflow or shell surface changed"
SKILL_REASON: Final = "plugin skill source or generated runtime changed"
TEST_REASON: Final = "changed python assertion tests"
ROOT_README_PATH: Final = "README.md"
SKILL_STEP_LABELS: Final = (
    "build-skills",
    "dist-diff",
    "manifests",
    "skills",
    "skill-injection",
    "reference-portability",
    "runtime-token",
    "docs-check",
)

FULL_GATE_PATTERNS: Final = (
    "pyproject.toml",
    "uv.lock",
    "justfile",
    "Justfile",
    "outcomeeng/catalog/**",
    "outcomeeng/distribution/**",
    "outcomeeng/validation/**",
    "outcomeeng_evals/**",
    "outcomeeng_testing/**",
    ".github/workflows/check.yml",
    ".github/workflows/spec-tree-evals.yml",
)
PYTHON_PATTERNS: Final = (
    "outcomeeng/**",
    "outcomeeng_testing/**",
    "outcomeeng_evals/**",
    "spx/**/tests/test_*.py",
)
PYTHON_ASSERTION_TEST_PATTERNS: Final = ("spx/**/tests/test_*.py",)
MARKDOWN_PATTERNS: Final = (
    ROOT_README_PATH,
    "*.md",
    "spx/**",
    "src/plugins/**/*.md",
)
WORKFLOW_PATTERNS: Final = (
    ".github/workflows/**",
    "**/*.sh",
)
SKILL_PATTERNS: Final = (
    "src/plugins/**",
    "dist/claude/**",
    "dist/codex/**",
    ".claude-plugin/**",
    ".agents/plugins/**",
)

_STEP_REASONS: Final = {
    FMT_CHECK_ARGV: MARKDOWN_REASON,
    SPX_MARKDOWN_ARGV: MARKDOWN_REASON,
    ACTIONLINT_ARGV: WORKFLOW_REASON,
    SHELLCHECK_ARGV: WORKFLOW_REASON,
    RUFF_FORMAT_ARGV: PYTHON_REASON,
    RUFF_CHECK_ARGV: PYTHON_REASON,
    MYPY_ARGV: PYTHON_REASON,
    PYRIGHT_ARGV: PYTHON_REASON,
    HOOK_SAFETY_ARGV: WORKFLOW_REASON,
    SPX_VERSION_FLOOR_ARGV: FULL_GATE_REASON,
}
GIT_DIFF_BRANCH_ARGV_PREFIX: Final = (
    "git",
    "diff",
    "--name-status",
    "--diff-filter=ACDMRT",
)
GIT_DIFF_STAGED_ARGV: Final = (
    "git",
    "diff",
    "--cached",
    "--name-status",
    "--diff-filter=ACDMRT",
)
GIT_DIFF_UNSTAGED_ARGV: Final = (
    "git",
    "diff",
    "--name-status",
    "--diff-filter=ACDMRT",
)
GIT_LS_UNTRACKED_ARGV: Final = ("git", "ls-files", "--others", "--exclude-standard")
DELETED_GIT_STATUS_PREFIX: Final = "D"
RENAMED_GIT_STATUS_PREFIX: Final = "R"
COPIED_GIT_STATUS_PREFIX: Final = "C"


@dataclass(frozen=True)
class SelectedGateStep:
    """One selected gate step and the reason it is present."""

    step: Step
    reason: str


@dataclass(frozen=True)
class SelectedGatePlan:
    """A concrete local gate plan."""

    changed_paths: tuple[str, ...]
    selected_steps: tuple[SelectedGateStep, ...]
    full_gate: bool

    @property
    def steps(self) -> tuple[Step, ...]:
        return tuple(item.step for item in self.selected_steps)


@dataclass(frozen=True)
class ChangedPath:
    """One changed path with its git status preserved."""

    path: str
    status: str

    @property
    def is_deleted(self) -> bool:
        return self.status.startswith(DELETED_GIT_STATUS_PREFIX)


class GitDiscoveryError(RuntimeError):
    """A git path-discovery command failed before the gate could select steps."""

    def __init__(self, command: Sequence[str], result: GitCommandResult) -> None:
        self.command: tuple[str, ...] = tuple(command)
        self.returncode = result.returncode
        self.stdout = result.stdout
        super().__init__(self.message)

    @property
    def command_text(self) -> str:
        return " ".join(self.command)

    @property
    def message(self) -> str:
        return (
            f"{GIT_DISCOVERY_ERROR_PREFIX}: {self.command_text} "
            f"exited {self.returncode}"
        )


class ChangesetScopeModule(Protocol):
    """Typed subset of the canonical changeset-scope helper."""

    def detect_base_ref(self, repo: Path, *, strict: bool = False) -> str: ...

    def remote_tracking_ref(self, base_ref: str) -> str: ...


class BaseRefResolver(Protocol):
    """Resolve the remote-tracking base ref for selected-gate path discovery."""

    def __call__(self, repo: Path, /) -> str: ...


def collect_changed_paths(
    repo: Path,
    *,
    base_ref: str | None = None,
    base_ref_resolver: BaseRefResolver | None = None,
    runner: GitRunner = run_git_command,
) -> tuple[str, ...]:
    """Return branch, staged, unstaged, and untracked paths for local gate selection."""

    entries = collect_changed_path_entries(
        repo,
        base_ref=base_ref,
        base_ref_resolver=base_ref_resolver,
        runner=runner,
    )
    return tuple(sorted({entry.path for entry in entries}))


def collect_changed_path_entries(
    repo: Path,
    *,
    base_ref: str | None = None,
    base_ref_resolver: BaseRefResolver | None = None,
    runner: GitRunner = run_git_command,
) -> tuple[ChangedPath, ...]:
    """Return branch, staged, unstaged, and untracked paths with git status."""

    resolver = base_ref_resolver or resolve_default_base_ref
    resolved_base_ref = base_ref if base_ref is not None else resolver(repo)
    commands = (
        (*GIT_DIFF_BRANCH_ARGV_PREFIX, f"{resolved_base_ref}...HEAD"),
        GIT_DIFF_STAGED_ARGV,
        GIT_DIFF_UNSTAGED_ARGV,
        GIT_LS_UNTRACKED_ARGV,
    )
    entries: set[ChangedPath] = set()
    for command in commands:
        completed = runner(command, repo)
        if completed.returncode != 0:
            raise GitDiscoveryError(command, completed)
        entries.update(_changed_path_entries_from_output(command, completed.stdout))
    return tuple(sorted(entries, key=lambda entry: (entry.path, entry.status)))


def build_selected_gate_plan(
    changed_paths: tuple[str, ...],
    *,
    deleted_paths: tuple[str, ...] = (),
) -> SelectedGatePlan:
    """Build the selected local gate plan for changed paths."""

    normalized = tuple(sorted(set(changed_paths)))
    if not normalized:
        return SelectedGatePlan(changed_paths=(), selected_steps=(), full_gate=False)

    if _matches_any(normalized, FULL_GATE_PATTERNS):
        return SelectedGatePlan(
            changed_paths=normalized,
            selected_steps=tuple(
                SelectedGateStep(step=step, reason=FULL_GATE_REASON)
                for recipe in CHECK_RECIPES
                for step in recipe.steps
            ),
            full_gate=True,
        )

    selected_argvs: set[tuple[str, ...]] = set()
    reasons: dict[tuple[str, ...], str] = {}
    if _matches_any(normalized, MARKDOWN_PATTERNS):
        markdown_argvs: tuple[tuple[str, ...], ...] = (
            FMT_CHECK_ARGV,
            SPX_MARKDOWN_ARGV,
        )
        for argv in markdown_argvs:
            selected_argvs.add(argv)
            reasons[argv] = MARKDOWN_REASON
    if _matches_any(normalized, WORKFLOW_PATTERNS):
        workflow_argvs: tuple[tuple[str, ...], ...] = (ACTIONLINT_ARGV, SHELLCHECK_ARGV)
        for argv in workflow_argvs:
            selected_argvs.add(argv)
            reasons[argv] = WORKFLOW_REASON
    if _matches_any(normalized, PYTHON_PATTERNS):
        python_argvs: tuple[tuple[str, ...], ...] = (
            RUFF_FORMAT_ARGV,
            RUFF_CHECK_ARGV,
            MYPY_ARGV,
            PYRIGHT_ARGV,
        )
        for argv in python_argvs:
            selected_argvs.add(argv)
            reasons[argv] = PYTHON_REASON
    if _matches_any(normalized, SKILL_PATTERNS):
        for step in VALIDATION_STEPS:
            if step.label in SKILL_STEP_LABELS:
                selected_argvs.add(step.argv)
                reasons[step.argv] = SKILL_REASON

    selected_steps = [
        SelectedGateStep(step=step, reason=reasons[step.argv])
        for step in VALIDATION_STEPS
        if step.argv in selected_argvs
    ]
    deleted_path_set = set(deleted_paths)
    test_paths = tuple(
        path
        for path in normalized
        if _is_python_assertion_test(path) and path not in deleted_path_set
    )
    if test_paths:
        selected_steps.append(
            SelectedGateStep(
                step=Step(
                    label=TEST_RECIPE.steps[0].label, argv=(*PYTEST_ARGV, *test_paths)
                ),
                reason=TEST_REASON,
            )
        )
    return SelectedGatePlan(
        changed_paths=normalized,
        selected_steps=tuple(selected_steps),
        full_gate=False,
    )


def run_selected_check(
    *,
    spawner: ProcessSpawner,
    sink: TextIO,
    repo: Path,
    base_ref: str | None = None,
    base_ref_resolver: BaseRefResolver | None = None,
    runner: GitRunner = run_git_command,
) -> int:
    """Run the selected local check through the recipe orchestrator."""

    try:
        changed_path_entries = collect_changed_path_entries(
            repo,
            base_ref=base_ref,
            base_ref_resolver=base_ref_resolver,
            runner=runner,
        )
    except GitDiscoveryError as exc:
        _write_git_discovery_error(sink, exc)
        return GIT_DISCOVERY_FAILURE_EXIT_CODE
    plan = build_selected_gate_plan(
        tuple(entry.path for entry in changed_path_entries),
        deleted_paths=tuple(
            entry.path for entry in changed_path_entries if entry.is_deleted
        ),
    )
    _write_plan(sink, plan)
    if plan.full_gate:
        return run_check(spawner=spawner, sink=sink, recipes=CHECK_RECIPES)
    return run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=Recipe(
            name=RECIPE_CHECK,
            verification_type=None,
            purpose=None,
            preflight_steps=PREFLIGHT_STEPS,
            steps=plan.steps,
        ),
    )


def resolve_default_base_ref(repo: Path) -> str:
    """Return the canonical remote-tracking base ref for this repository."""

    changeset_scope = _load_changeset_scope()
    bare_base = changeset_scope.detect_base_ref(repo)
    return changeset_scope.remote_tracking_ref(bare_base)


def _load_changeset_scope() -> ChangesetScopeModule:
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cast("ChangesetScopeModule", cached)
    spec = importlib.util.spec_from_file_location(
        "changeset_scope", CHANGESET_SCOPE_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {CHANGESET_SCOPE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return cast("ChangesetScopeModule", module)


def _write_plan(sink: TextIO, plan: SelectedGatePlan) -> None:
    sink.write(f"{SELECTED_CHECK_PLAN_HEADER}\n")
    if not plan.changed_paths:
        sink.write(f"No gate steps selected: {NO_CHANGED_PATHS_REASON}.\n")
        sink.flush()
        return
    for item in plan.selected_steps:
        sink.write(f"  {item.step.label}: {item.reason}\n")
    sink.flush()


def _write_git_discovery_error(sink: TextIO, exc: GitDiscoveryError) -> None:
    sink.write(f"{exc.message}\n")
    output = exc.stdout.strip()
    if output:
        sink.write(f"git output:\n{output}\n")
    sink.flush()


def _matches_any(paths: tuple[str, ...], patterns: tuple[str, ...]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in patterns
    )


def _is_python_assertion_test(path: str) -> bool:
    return _matches_any((path,), PYTHON_ASSERTION_TEST_PATTERNS)


def _changed_path_entries_from_output(
    command: tuple[str, ...],
    output: str,
) -> tuple[ChangedPath, ...]:
    entries: list[ChangedPath] = []
    status_output = command != GIT_LS_UNTRACKED_ARGV
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if status_output:
            entries.extend(_parse_name_status_line(stripped))
        else:
            entries.append(ChangedPath(path=stripped, status="A"))
    return tuple(entries)


def _parse_name_status_line(line: str) -> tuple[ChangedPath, ...]:
    parts = line.split("\t")
    status = parts[0]
    if len(parts) < 2:
        return ()
    if status.startswith(RENAMED_GIT_STATUS_PREFIX):
        if len(parts) < 3:
            return ()
        return (
            ChangedPath(path=parts[1], status=DELETED_GIT_STATUS_PREFIX),
            ChangedPath(path=parts[2], status=status),
        )
    if status.startswith(COPIED_GIT_STATUS_PREFIX):
        if len(parts) < 3:
            return ()
        return (
            ChangedPath(path=parts[1], status=status),
            ChangedPath(path=parts[2], status=status),
        )
    return (ChangedPath(path=parts[1], status=status),)
