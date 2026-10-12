"""Changed-path selection for the local validation gate."""

from __future__ import annotations

import fnmatch
import importlib.util
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol, TextIO, cast

from outcomeeng.validation._engine import run_check, run_recipe
from outcomeeng.validation._git import GitCommandResult, GitRunner, run_git_command
from outcomeeng.validation._model import ProcessSpawner, Recipe, Step
from outcomeeng.validation._steps import (
    ACTIONLINT_ARGV,
    CHECK_RECIPES,
    EVAL_LINKS_ARGV,
    EVAL_PROMPTS_ARGV,
    EVAL_TRIGGER_WORKFLOW,
    EVAL_TRIGGERS_ARGV,
    FMT_CHECK_ARGV,
    INSTRUCTION_BLOCK_ARGV,
    MYPY_ARGV,
    PREFLIGHT_STEPS,
    PYRIGHT_ARGV,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SHELLCHECK_ARGV,
    SPX_MARKDOWN_ARGV,
    TEST_RECIPE,
    VALIDATION_STEPS,
)
from outcomeeng.validation.infrastructure_index import (
    TEST_INFRASTRUCTURE_PACKAGE,
    InfrastructureIndex,
    InfrastructureReach,
    index_test_infrastructure,
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
GIT_DISCOVERY_STDOUT_LABEL: Final = "git stdout"
GIT_DISCOVERY_STDERR_LABEL: Final = "git stderr"
FULL_GATE_REASON: Final = "full gate surface changed"
PYTHON_REASON: Final = "python source or test path changed"
MARKDOWN_REASON: Final = "markdown or spec path changed"
WORKFLOW_REASON: Final = "workflow or shell surface changed"
SKILL_REASON: Final = "plugin skill, shared fragment, or generated runtime changed"
INSTRUCTION_BLOCK_REASON: Final = "managed instruction-block source changed"
EVAL_REASON: Final = "eval definition, producer, or trigger surface changed"
EVIDENCE_LINK_REASON: Final = "spec-tree evidence link surface changed"
TEST_REASON: Final = "changed python assertion tests"
REACHED_TESTS_REASON: Final = "tests reaching changed test infrastructure"
FULL_CHECK_REASON: Final = "explicit full gate"
# The real-agent Codex tests: the fresh-session subagent discovery test and the
# real-agent bootstrap test. Both run on the Codex CLI the host installs and
# consume model quota, so the gate wrappers select them only for a changeset
# that changes an agent definition.
REAL_AGENT_CODEX_TEST_MODULE: Final = (
    "spx/32-distribution.enabler/21-installation.enabler/"
    "21-repository-installation.enabler/tests/"
    "test_repository_installation.scenario.l3.py"
)
REAL_AGENT_CODEX_TEST_FUNCTIONS: Final = (
    "test_fresh_codex_session_discovers_every_placed_canonical_subagent",
    "test_real_agent_clis_bootstrap_empty_persistent_state",
)
PYTEST_NODE_ID_SEPARATOR: Final = "::"
REAL_AGENT_CODEX_TESTS: Final = tuple(
    f"{REAL_AGENT_CODEX_TEST_MODULE}{PYTEST_NODE_ID_SEPARATOR}{function}"
    for function in REAL_AGENT_CODEX_TEST_FUNCTIONS
)
REAL_AGENT_CODEX_INCLUDED_REASON: Final = (
    "real-agent Codex tests included: agent definition changed"
)
REAL_AGENT_CODEX_EXCLUDED_REASON: Final = (
    "real-agent Codex tests excluded: no agent definition changed"
)
PYTEST_KEYWORD_OPTION: Final = "-k"
# Deselects by test function name, so the exclusion names no node id and a
# pytest argument tail that carries it still collects every other test.
REAL_AGENT_CODEX_EXCLUSION: Final = (
    PYTEST_KEYWORD_OPTION,
    f"not ({' or '.join(REAL_AGENT_CODEX_TEST_FUNCTIONS)})",
)
# The full gate runs in CI from a merge-commit checkout that carries no
# `origin/HEAD`; its first parent is the base tip there and the previous commit
# on a default-branch push. The plan names the base it used, so a run that fell
# back to the first parent says so before any step runs.
FIRST_PARENT_BASE_REF: Final = "HEAD^"
CHANGESET_BASE_LABEL: Final = "changeset base"
FIRST_PARENT_BASE_NOTE: Final = "first parent; no remote default branch is configured"
PLAN_LINE_INDENT: Final = "  "
SHARED_TEST_INFRASTRUCTURE_REASON: Final = "shared test infrastructure changed"
UNTRACEABLE_TEST_INFRASTRUCTURE_REASON: Final = (
    "test-infrastructure artifact reached by path changed"
)
# One pytest step can carry paths selected for different reasons; its label
# names every reason that contributed a path.
REASON_SEPARATOR: Final = "; "
ROOT_README_PATH: Final = "README.md"
SPX_CONFIG_PATH: Final = "spx.config.yaml"
# Exact-match selection targets, named so a consumer imports the value rather
# than recopying the path.
CHECK_WORKFLOW_PATH: Final = ".github/workflows/check.yml"
PYPROJECT_PATH: Final = "pyproject.toml"
INSTRUCTION_BLOCK_SOURCE_PATH: Final = "src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md"
SKILL_STEP_LABELS: Final = (
    "build-skills",
    "dist-diff",
    "manifests",
    "skills",
    "skill-injection",
    "reference-portability",
    "runtime-token",
    "scratch-paths",
    "grant-locality",
    "hook-safety",
    "foundation-manifest",
    "docs-check",
)

FULL_GATE_PATTERNS: Final = (
    CHECK_WORKFLOW_PATH,
    PYPROJECT_PATH,
    "uv.lock",
    "justfile",
    "Justfile",
    "outcomeeng/catalog/**",
    "outcomeeng/distribution/**",
    "outcomeeng/validation/**",
    "outcomeeng_evals/**",
)
# A test-infrastructure change reaches only the tests that import it, so its
# gate steps come from the static import index rather than a path pattern.
TEST_INFRASTRUCTURE_PATTERNS: Final = (f"{TEST_INFRASTRUCTURE_PACKAGE}/**",)
PYTHON_FORMAT_LINT_PATTERNS: Final = (
    "outcomeeng/**",
    "outcomeeng_testing/**",
    "outcomeeng_evals/**",
    "src/plugins/**/*.py",
    "src/templates/**/*.py",
    "spx/**/tests/test_*.py",
)
PYTHON_TYPECHECK_PATTERNS: Final = (
    "outcomeeng/**",
    "outcomeeng_testing/**",
    "outcomeeng_evals/**",
    "spx/**/tests/test_*.py",
)
PYTHON_ASSERTION_TEST_PATTERNS: Final = ("spx/**/tests/test_*.py",)
MARKDOWN_PATTERNS: Final = (
    ROOT_README_PATH,
    SPX_CONFIG_PATH,
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
    "src/_shared/**",
    "src/templates/**",
    "dist/claude/**",
    "dist/codex/**",
    ".claude-plugin/**",
    ".agents/plugins/**",
)
# The trigger list is generated from the eval definitions and written into the
# eval workflow, so only those two surfaces can stale it.
EVAL_TRIGGER_PATTERNS: Final = (
    "spx/**/evals/**",
    EVAL_TRIGGER_WORKFLOW,
)
# A producer-coupled prompt is derived from a producer the eval names under
# `src/plugins/`. The producer set is per-eval, not statically known here, so
# the whole authored plugin tree is the pattern: selecting the prompt check for
# an unrelated plugin edit costs one fast command, while missing a real producer
# edit would ship a stale prompt.
EVAL_PROMPT_PATTERNS: Final = (
    "spx/**/evals/**",
    "src/plugins/**",
)
# A `[test]` or `[eval]` link lives only in spec markdown, and its target is a
# file under the same node, so any changed spec-tree path can dangle one.
EVIDENCE_LINK_PATTERNS: Final = ("spx/**",)
INSTRUCTION_BLOCK_PATTERNS: Final = (
    "AGENTS.md",
    "CLAUDE.md",
    INSTRUCTION_BLOCK_SOURCE_PATH,
    "src/plugins/spec-tree/skills/update-instruction-block/**",
    "dist/claude/spec-tree/skills/update-instruction-block/templates/instruction-block.md",
    "dist/codex/spec-tree/skills/update-instruction-block/templates/instruction-block.md",
    "outcomeeng/distribution/instruction_block.py",
)
# Agent definitions: authored agent sources, their generated renderings, the
# code that converts and emits them, the repository installation code that
# places and reconciles them in the selected agent home, and the shipped
# placement scripts.
AGENT_DEFINITION_PATTERNS: Final = (
    "src/plugins/*/agents/**",
    "dist/claude/*/agents/**",
    "dist/codex/*/skills/*/agents/**",
    "outcomeeng/distribution/agents.py",
    "outcomeeng/distribution/build.py",
    "outcomeeng/distribution/installation.py",
    "src/templates/plugin/scripts/place_agents.py",
    "dist/*/*/skills/*-plugin/scripts/place_agents.py",
)


class PathCategory(StrEnum):
    """Every changed-path category the selector classifies a path into."""

    FULL_GATE = "full-gate"
    TEST_INFRASTRUCTURE = "test-infrastructure"
    PYTHON_FORMAT_LINT = "python-format-lint"
    PYTHON_TYPECHECK = "python-typecheck"
    PYTHON_ASSERTION_TEST = "python-assertion-test"
    MARKDOWN = "markdown"
    WORKFLOW = "workflow"
    SKILL = "skill"
    INSTRUCTION_BLOCK = "instruction-block"
    EVAL_TRIGGER = "eval-trigger"
    EVAL_PROMPT = "eval-prompt"
    EVIDENCE_LINK = "evidence-link"
    AGENT_DEFINITION = "agent-definition"


# The planner classifies every changed path through this registry alone, so a
# category exists for selection exactly when it has an entry here.
PATH_CATEGORY_PATTERNS: Final[Mapping[PathCategory, tuple[str, ...]]] = (
    MappingProxyType(
        {
            PathCategory.FULL_GATE: FULL_GATE_PATTERNS,
            PathCategory.TEST_INFRASTRUCTURE: TEST_INFRASTRUCTURE_PATTERNS,
            PathCategory.PYTHON_FORMAT_LINT: PYTHON_FORMAT_LINT_PATTERNS,
            PathCategory.PYTHON_TYPECHECK: PYTHON_TYPECHECK_PATTERNS,
            PathCategory.PYTHON_ASSERTION_TEST: PYTHON_ASSERTION_TEST_PATTERNS,
            PathCategory.MARKDOWN: MARKDOWN_PATTERNS,
            PathCategory.WORKFLOW: WORKFLOW_PATTERNS,
            PathCategory.SKILL: SKILL_PATTERNS,
            PathCategory.INSTRUCTION_BLOCK: INSTRUCTION_BLOCK_PATTERNS,
            PathCategory.EVAL_TRIGGER: EVAL_TRIGGER_PATTERNS,
            PathCategory.EVAL_PROMPT: EVAL_PROMPT_PATTERNS,
            PathCategory.EVIDENCE_LINK: EVIDENCE_LINK_PATTERNS,
            PathCategory.AGENT_DEFINITION: AGENT_DEFINITION_PATTERNS,
        }
    )
)


@dataclass(frozen=True)
class ValidationLane:
    """The validation steps one path category selects and the reason it gives."""

    argvs: tuple[tuple[str, ...], ...]
    reason: str


SKILL_LANE_ARGVS: Final = tuple(
    step.argv for step in VALIDATION_STEPS if step.label in SKILL_STEP_LABELS
)
# The validation steps each lane-bearing category selects. The full-gate,
# test-infrastructure, assertion-test, and agent-definition categories select
# no validation lane of their own: they decide the full surface or the pytest
# step instead.
VALIDATION_LANES: Final[Mapping[PathCategory, ValidationLane]] = MappingProxyType(
    {
        PathCategory.MARKDOWN: ValidationLane(
            argvs=(FMT_CHECK_ARGV, SPX_MARKDOWN_ARGV), reason=MARKDOWN_REASON
        ),
        PathCategory.WORKFLOW: ValidationLane(
            argvs=(ACTIONLINT_ARGV, SHELLCHECK_ARGV), reason=WORKFLOW_REASON
        ),
        PathCategory.PYTHON_FORMAT_LINT: ValidationLane(
            argvs=(RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV), reason=PYTHON_REASON
        ),
        PathCategory.PYTHON_TYPECHECK: ValidationLane(
            argvs=(MYPY_ARGV, PYRIGHT_ARGV), reason=PYTHON_REASON
        ),
        PathCategory.SKILL: ValidationLane(argvs=SKILL_LANE_ARGVS, reason=SKILL_REASON),
        PathCategory.INSTRUCTION_BLOCK: ValidationLane(
            argvs=(INSTRUCTION_BLOCK_ARGV,), reason=INSTRUCTION_BLOCK_REASON
        ),
        PathCategory.EVAL_TRIGGER: ValidationLane(
            argvs=(EVAL_TRIGGERS_ARGV,), reason=EVAL_REASON
        ),
        PathCategory.EVAL_PROMPT: ValidationLane(
            argvs=(EVAL_PROMPTS_ARGV,), reason=EVAL_REASON
        ),
        PathCategory.EVIDENCE_LINK: ValidationLane(
            argvs=(EVAL_LINKS_ARGV,), reason=EVIDENCE_LINK_REASON
        ),
    }
)

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
    real_agent_codex: bool = False

    @property
    def real_agent_codex_reason(self) -> str:
        return (
            REAL_AGENT_CODEX_INCLUDED_REASON
            if self.real_agent_codex
            else REAL_AGENT_CODEX_EXCLUDED_REASON
        )

    @property
    def steps(self) -> tuple[Step, ...]:
        return tuple(item.step for item in self.selected_steps)


@dataclass(frozen=True)
class ChangedPath:
    """One changed path with its git status preserved."""

    path: str
    status: str


class GitDiscoveryError(RuntimeError):
    """A git path-discovery command failed before the gate could select steps."""

    def __init__(self, command: Sequence[str], result: GitCommandResult) -> None:
        self.command: tuple[str, ...] = tuple(command)
        self.returncode = result.returncode
        self.stdout = result.stdout
        self.stderr = result.stderr
        super().__init__(self.message)

    @property
    def command_text(self) -> str:
        return " ".join(self.command)

    @property
    def message(self) -> str:
        base_message = (
            f"{GIT_DISCOVERY_ERROR_PREFIX}: {self.command_text} "
            f"exited {self.returncode}"
        )
        diagnostic = self.diagnostic_text
        if not diagnostic:
            return base_message
        return f"{base_message}: {diagnostic}"

    @property
    def diagnostic_text(self) -> str:
        return "\n".join(
            output for output in (self.stdout.strip(), self.stderr.strip()) if output
        )


class BaseRefDiscoveryError(RuntimeError):
    """The selected gate cannot resolve the remote default branch."""


class InfrastructureIndexRequired(ValueError):
    """A test-infrastructure path changed but no reach index was supplied."""

    def __init__(self, paths: Sequence[str]) -> None:
        self.paths: tuple[str, ...] = tuple(paths)
        super().__init__(
            "test-infrastructure paths need a reach index: " + ", ".join(self.paths)
        )


class ChangesetScopeModule(Protocol):
    """Typed subset of the canonical changeset-scope helper."""

    BaseRefNotConfiguredError: type[RuntimeError]

    def detect_base_ref(self, repo: Path) -> str: ...

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


def deleted_paths_after_status_resolution(
    entries: Sequence[ChangedPath],
    *,
    repo: Path | None = None,
) -> tuple[str, ...]:
    """Return paths with any deletion status in the gathered entry set."""

    statuses_by_path: dict[str, set[str]] = {}
    for entry in entries:
        statuses_by_path.setdefault(entry.path, set()).add(entry.status)
    return tuple(
        sorted(
            path
            for path, statuses in statuses_by_path.items()
            if any(status.startswith(DELETED_GIT_STATUS_PREFIX) for status in statuses)
            and (repo is None or not (repo / path).exists())
        )
    )


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
    test_infrastructure: InfrastructureIndex | None = None,
) -> SelectedGatePlan:
    """Build the selected local gate plan for changed paths.

    ``test_infrastructure`` is required whenever a changed path lies under
    the test-infrastructure package; its reach decides between the tests that
    import the changed module and the full surface.
    """

    normalized = tuple(sorted(set(changed_paths)))
    if not normalized:
        return SelectedGatePlan(changed_paths=(), selected_steps=(), full_gate=False)

    categories = changed_path_categories(normalized)
    real_agent_codex = PathCategory.AGENT_DEFINITION in categories
    if PathCategory.FULL_GATE in categories:
        return _full_surface_plan(
            normalized, reason=FULL_GATE_REASON, real_agent_codex=real_agent_codex
        )

    infrastructure_paths = tuple(
        path for path in normalized if _is_test_infrastructure_path(path)
    )
    reached_tests: set[str] = set()
    if infrastructure_paths:
        if test_infrastructure is None:
            raise InfrastructureIndexRequired(infrastructure_paths)
        for report in (test_infrastructure.reach(p) for p in infrastructure_paths):
            if report.kind is InfrastructureReach.SHARED:
                return _full_surface_plan(
                    normalized,
                    reason=SHARED_TEST_INFRASTRUCTURE_REASON,
                    real_agent_codex=real_agent_codex,
                )
            if report.kind is InfrastructureReach.UNTRACEABLE:
                return _full_surface_plan(
                    normalized,
                    reason=UNTRACEABLE_TEST_INFRASTRUCTURE_REASON,
                    real_agent_codex=real_agent_codex,
                )
            reached_tests.update(report.tests)

    reasons: dict[tuple[str, ...], str] = {}
    for category, lane in VALIDATION_LANES.items():
        if category in categories:
            for argv in lane.argvs:
                reasons[argv] = lane.reason
    selected_argvs = set(reasons)

    selected_steps = [
        SelectedGateStep(step=step, reason=reasons[step.argv])
        for step in VALIDATION_STEPS
        if step.argv in selected_argvs
    ]
    deleted_path_set = set(deleted_paths)
    changed_test_paths = tuple(
        path
        for path in normalized
        if _is_python_assertion_test(path) and path not in deleted_path_set
    )
    reached_only = reached_tests - set(changed_test_paths) - deleted_path_set
    test_path_set = set(changed_test_paths) | reached_only
    real_agent_module_targeted = REAL_AGENT_CODEX_TEST_MODULE in {
        path.split(PYTEST_NODE_ID_SEPARATOR, maxsplit=1)[0] for path in test_path_set
    }
    if real_agent_codex and not real_agent_module_targeted:
        test_path_set.update(REAL_AGENT_CODEX_TESTS)
    test_paths = tuple(sorted(test_path_set))
    if test_paths:
        test_reasons = (
            *((TEST_REASON,) if changed_test_paths else ()),
            *((REACHED_TESTS_REASON,) if reached_only else ()),
            *((REAL_AGENT_CODEX_INCLUDED_REASON,) if real_agent_codex else ()),
        )
        exclusion = (
            REAL_AGENT_CODEX_EXCLUSION
            if real_agent_module_targeted and not real_agent_codex
            else ()
        )
        selected_steps.append(
            SelectedGateStep(
                step=Step(
                    label=TEST_RECIPE.steps[0].label,
                    argv=(*PYTEST_ARGV, *test_paths, *exclusion),
                ),
                reason=REASON_SEPARATOR.join(test_reasons),
            )
        )
    return SelectedGatePlan(
        changed_paths=normalized,
        selected_steps=tuple(selected_steps),
        full_gate=False,
        real_agent_codex=real_agent_codex,
    )


def build_full_gate_plan(changed_paths: tuple[str, ...]) -> SelectedGatePlan:
    """Build the explicit full gate plan for changed paths.

    The plan carries the complete validation-plus-test recipe set; the changed
    paths decide only whether its pytest steps run the real-agent Codex tests.
    """

    normalized = tuple(sorted(set(changed_paths)))
    return _full_surface_plan(
        normalized,
        reason=FULL_CHECK_REASON,
        real_agent_codex=PathCategory.AGENT_DEFINITION
        in changed_path_categories(normalized),
    )


def changed_path_categories(paths: Sequence[str]) -> frozenset[PathCategory]:
    """Return every category in which at least one of ``paths`` lies."""

    candidates = tuple(paths)
    return frozenset(
        category
        for category, patterns in PATH_CATEGORY_PATTERNS.items()
        if _matches_any(candidates, patterns)
    )


def _full_surface_plan(
    changed_paths: tuple[str, ...],
    *,
    reason: str,
    real_agent_codex: bool,
) -> SelectedGatePlan:
    return SelectedGatePlan(
        changed_paths=changed_paths,
        selected_steps=tuple(
            SelectedGateStep(
                step=_full_surface_step(step, real_agent_codex), reason=reason
            )
            for recipe in CHECK_RECIPES
            for step in recipe.steps
        ),
        full_gate=True,
        real_agent_codex=real_agent_codex,
    )


def _full_surface_step(step: Step, real_agent_codex: bool) -> Step:
    if real_agent_codex or step.argv[: len(PYTEST_ARGV)] != PYTEST_ARGV:
        return step
    return replace(step, argv=(*step.argv, *REAL_AGENT_CODEX_EXCLUSION))


def _full_surface_recipes(plan: SelectedGatePlan) -> tuple[Recipe, ...]:
    return tuple(
        replace(
            recipe,
            steps=tuple(
                _full_surface_step(step, plan.real_agent_codex) for step in recipe.steps
            ),
        )
        for recipe in CHECK_RECIPES
    )


def run_selected_check(
    *,
    spawner: ProcessSpawner,
    sink: TextIO,
    repo: Path,
    base_ref: str | None = None,
    runner: GitRunner = run_git_command,
) -> int:
    """Run the selected local check through the recipe orchestrator."""

    try:
        changed_path_entries = collect_changed_path_entries(
            repo,
            base_ref=base_ref,
            runner=runner,
        )
    except GitDiscoveryError as exc:
        _write_git_discovery_error(sink, exc)
        return GIT_DISCOVERY_FAILURE_EXIT_CODE
    except BaseRefDiscoveryError as exc:
        sink.write(f"{GIT_DISCOVERY_ERROR_PREFIX}: {exc}\n")
        sink.flush()
        return GIT_DISCOVERY_FAILURE_EXIT_CODE
    changed_paths = tuple(entry.path for entry in changed_path_entries)
    plan = build_selected_gate_plan(
        changed_paths,
        deleted_paths=deleted_paths_after_status_resolution(
            changed_path_entries,
            repo=repo,
        ),
        test_infrastructure=(
            index_test_infrastructure(repo)
            if any(_is_test_infrastructure_path(path) for path in changed_paths)
            else None
        ),
    )
    _write_plan(sink, plan)
    if plan.full_gate:
        return run_check(
            spawner=spawner, sink=sink, recipes=_full_surface_recipes(plan)
        )
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


def run_full_check(
    *,
    spawner: ProcessSpawner,
    sink: TextIO,
    repo: Path,
    base_ref: str | None = None,
    runner: GitRunner = run_git_command,
) -> int:
    """Run the explicit full gate, selecting real-agent Codex tests by changeset."""

    resolved_base_ref = (
        base_ref if base_ref is not None else resolve_full_gate_base_ref(repo)
    )
    try:
        changed_paths = collect_changed_paths(
            repo,
            base_ref=resolved_base_ref,
            runner=runner,
        )
    except GitDiscoveryError as exc:
        _write_git_discovery_error(sink, exc)
        return GIT_DISCOVERY_FAILURE_EXIT_CODE
    plan = build_full_gate_plan(changed_paths)
    _write_plan(sink, plan, changeset_base=resolved_base_ref)
    return run_check(spawner=spawner, sink=sink, recipes=_full_surface_recipes(plan))


def resolve_full_gate_base_ref(repo: Path) -> str:
    """Return the default base ref, or the first parent where none is configured."""

    try:
        return resolve_default_base_ref(repo)
    except BaseRefDiscoveryError:
        return FIRST_PARENT_BASE_REF


def resolve_default_base_ref(repo: Path) -> str:
    """Return the canonical remote-tracking base ref for this repository."""

    changeset_scope = _load_changeset_scope()
    try:
        bare_base = changeset_scope.detect_base_ref(repo)
    except changeset_scope.BaseRefNotConfiguredError as exc:
        raise BaseRefDiscoveryError(str(exc)) from exc
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


def render_plan(plan: SelectedGatePlan, *, changeset_base: str | None = None) -> str:
    """Return the plan text the gate prints before it runs any step.

    ``changeset_base`` names the ref the changed paths were discovered
    against; a first-parent fallback carries a note saying why.
    """

    lines = [SELECTED_CHECK_PLAN_HEADER]
    if changeset_base is not None:
        note = (
            f" ({FIRST_PARENT_BASE_NOTE})"
            if changeset_base == FIRST_PARENT_BASE_REF
            else ""
        )
        lines.append(
            f"{PLAN_LINE_INDENT}{CHANGESET_BASE_LABEL}: {changeset_base}{note}"
        )
    if not plan.changed_paths and not plan.full_gate:
        lines.append(f"No gate steps selected: {NO_CHANGED_PATHS_REASON}.")
        return "\n".join(lines) + "\n"
    lines.extend(
        f"{PLAN_LINE_INDENT}{item.step.label}: {item.reason}"
        for item in plan.selected_steps
    )
    lines.append(f"{PLAN_LINE_INDENT}{plan.real_agent_codex_reason}")
    return "\n".join(lines) + "\n"


def _write_plan(
    sink: TextIO, plan: SelectedGatePlan, *, changeset_base: str | None = None
) -> None:
    sink.write(render_plan(plan, changeset_base=changeset_base))
    sink.flush()


def _write_git_discovery_error(sink: TextIO, exc: GitDiscoveryError) -> None:
    sink.write(f"{exc.message}\n")
    stdout = exc.stdout.strip()
    stderr = exc.stderr.strip()
    if stdout:
        sink.write(f"{GIT_DISCOVERY_STDOUT_LABEL}:\n{stdout}\n")
    if stderr:
        sink.write(f"{GIT_DISCOVERY_STDERR_LABEL}:\n{stderr}\n")
    sink.flush()


def _matches_any(paths: tuple[str, ...], patterns: tuple[str, ...]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in patterns
    )


def _is_python_assertion_test(path: str) -> bool:
    return _matches_any(
        (path,), PATH_CATEGORY_PATTERNS[PathCategory.PYTHON_ASSERTION_TEST]
    )


def _is_test_infrastructure_path(path: str) -> bool:
    return _matches_any(
        (path,), PATH_CATEGORY_PATTERNS[PathCategory.TEST_INFRASTRUCTURE]
    )


def _changed_path_entries_from_output(
    command: tuple[str, ...],
    output: str,
) -> tuple[ChangedPath, ...]:
    entries: list[ChangedPath] = []
    status_output = command != GIT_LS_UNTRACKED_ARGV
    for line in output.splitlines():
        if not line:
            continue
        if status_output:
            entries.extend(_parse_name_status_line(line))
        else:
            entries.append(ChangedPath(path=line, status="A"))
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
