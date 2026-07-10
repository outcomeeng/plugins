"""Harnesses for eval CI trigger-path evidence.

The harness materializes a real eval tree and a real workflow file on disk, so
the assertions exercise `outcomeeng_evals.ci_triggers` against the filesystem
contract it actually reads rather than an in-memory stand-in. Every temporary
directory is created and removed by the context manager that owns it.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from click.testing import CliRunner, Result
from hypothesis import given, seed, settings

from outcomeeng_evals.ci_plan import UNIVERSAL_OWNED_PATHS, matches
from outcomeeng_evals.ci_triggers import (
    BEGIN_MARKER,
    END_MARKER,
    EXPECTED_BLOCK_COUNT,
    ci_trigger_paths,
    minimal_patterns,
)
from outcomeeng_evals.cli import EXIT_SUCCESS, main
from outcomeeng_evals.definition import CiPolicy
from outcomeeng_testing.generators.ci_triggers import probe_paths, trigger_pattern_sets

MINIMIZATION_PROPERTY_SEED = 20260709
MINIMIZATION_PROPERTY_EXAMPLES = 80
CI_TRIGGERS_PROPERTY_TEST_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/"
    "tests/test_ci_triggers.property.l1.py::"
)

_EVAL_DIR_GLOB_SUFFIX = "/**"
_WORKFLOW_INDENT = " " * 6

# Probe fixtures: arbitrary representatives of a suite slug, a path an eval
# owns, and a path no eval owns. Named once so a reader sees which literal
# carries which role.
_PROBE_SUITE = "suite"
_PROBE_OWNED_PATH = "spx/a.md"
_PROBE_UNOWNED_PATH = "spx/orphan.md"


@dataclass(frozen=True)
class EvalTriggerRepo:
    """A temporary repository holding eval definitions and a workflow file."""

    repo_root: Path
    root: Path
    workflow: Path

    def eval_dir_glob(self, suite: str) -> str:
        return f"{self.root.name}/evals/{suite}{_EVAL_DIR_GLOB_SUFFIX}"

    def workflow_text(self) -> str:
        return self.workflow.read_text(encoding="utf-8")


@contextmanager
def eval_trigger_repo(
    suites: Mapping[str, tuple[CiPolicy, Sequence[str]]],
) -> Iterator[EvalTriggerRepo]:
    """Create an eval tree plus a marker-bearing workflow; remove it on exit.

    ``suites`` maps a suite slug to its CI policy and declared ``owned_paths``.
    The eval root is named ``spx`` so a derived eval-directory glob is
    repository-relative in the same shape the product's tree produces.
    """

    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        root = base / "spx"
        for suite, (policy, owned) in suites.items():
            eval_dir = root / "evals" / suite
            eval_dir.mkdir(parents=True)
            (eval_dir / "cases.jsonl").write_text(
                json.dumps({"id": "only", "input": {}, "expect": {}}) + "\n",
                encoding="utf-8",
            )
            (eval_dir / "prompt.md").write_text("{case_id}\n", encoding="utf-8")
            owned_toml = "".join(f'  "{path}",\n' for path in owned)
            (eval_dir / "eval.toml").write_text(
                f'title = "{suite}"\n'
                'cases = "cases.jsonl"\n'
                'prompt = "prompt.md"\n'
                'plugin_dir = "dist/claude/spec-tree"\n'
                f"owned_paths = [\n{owned_toml}]\n"
                f'ci_policy = "{policy.value}"\n',
                encoding="utf-8",
            )
        workflow = base / "workflow.yml"
        workflow.write_text(_workflow_skeleton(), encoding="utf-8")
        yield EvalTriggerRepo(repo_root=base, root=root, workflow=workflow)


def assert_ci_policy_controls_trigger_contribution(policy: CiPolicy) -> None:
    """Assert a suite's CI policy decides whether it contributes trigger paths."""

    owned = ("src/plugins/example/**", "spx/example.md")
    with eval_trigger_repo({_PROBE_SUITE: (policy, owned)}) as repo:
        derived = ci_trigger_paths(repo.root, repo_root=repo.repo_root)
        contributes = policy is not CiPolicy.MANUAL

        for owned_path in owned:
            assert (owned_path in derived) is contributes
        assert (repo.eval_dir_glob(_PROBE_SUITE) in derived) is contributes


def assert_universal_paths_always_contribute() -> None:
    """Assert the universal surfaces trigger CI regardless of suite ownership."""

    with eval_trigger_repo({_PROBE_SUITE: (CiPolicy.MANUAL, ())}) as repo:
        derived = ci_trigger_paths(repo.root, repo_root=repo.repo_root)

    for universal in UNIVERSAL_OWNED_PATHS:
        assert universal in derived


def _invoke_cli(repo: EvalTriggerRepo, *, check: bool) -> Result:
    """Invoke `outcomeeng-evals materialize-ci-triggers` against the temp repo.

    The compliance assertion names the CLI invocation, so the evidence drives
    the Click command and reads its exit code rather than the library function
    the command wraps.
    """

    argv = [
        "materialize-ci-triggers",
        str(repo.root),
        "--workflow",
        str(repo.workflow),
        "--repo-root",
        str(repo.repo_root),
    ]
    if check:
        argv.append("--check")
    return CliRunner().invoke(main, argv)


def assert_check_passes_when_workflow_is_current() -> None:
    """Assert the drift check exits successfully against a freshly written file."""

    with eval_trigger_repo(
        {_PROBE_SUITE: (CiPolicy.FULL, (_PROBE_OWNED_PATH,))}
    ) as repo:
        assert _invoke_cli(repo, check=False).exit_code == EXIT_SUCCESS

        result = _invoke_cli(repo, check=True)

        assert result.exit_code == EXIT_SUCCESS


def assert_check_fails_when_a_trigger_path_is_removed() -> None:
    """Assert the drift check rejects a hand-edited workflow missing a path."""

    with eval_trigger_repo(
        {_PROBE_SUITE: (CiPolicy.FULL, (_PROBE_OWNED_PATH,))}
    ) as repo:
        _invoke_cli(repo, check=False)
        tampered = "\n".join(
            line
            for line in repo.workflow_text().splitlines()
            if f'"{_PROBE_OWNED_PATH}"' not in line
        )
        repo.workflow.write_text(tampered + "\n", encoding="utf-8")

        result = _invoke_cli(repo, check=True)

        assert result.exit_code != EXIT_SUCCESS
        assert str(repo.workflow) in result.output


def assert_check_fails_when_an_unowned_trigger_path_is_added() -> None:
    """Assert the drift check rejects a trigger path no eval suite owns."""

    with eval_trigger_repo(
        {_PROBE_SUITE: (CiPolicy.FULL, (_PROBE_OWNED_PATH,))}
    ) as repo:
        _invoke_cli(repo, check=False)
        tampered = repo.workflow_text().replace(
            f"{_WORKFLOW_INDENT}{END_MARKER}",
            f'{_WORKFLOW_INDENT}- "{_PROBE_UNOWNED_PATH}"\n{_WORKFLOW_INDENT}{END_MARKER}',
            1,
        )
        repo.workflow.write_text(tampered, encoding="utf-8")

        result = _invoke_cli(repo, check=True)

        assert result.exit_code != EXIT_SUCCESS
        assert str(repo.workflow) in result.output


def assert_every_trigger_block_receives_the_same_paths() -> None:
    """Assert each declared trigger event renders an identical path list."""

    with eval_trigger_repo(
        {_PROBE_SUITE: (CiPolicy.FULL, (_PROBE_OWNED_PATH,))}
    ) as repo:
        assert _invoke_cli(repo, check=False).exit_code == EXIT_SUCCESS
        expected = ci_trigger_paths(repo.root, repo_root=repo.repo_root)
        blocks = _rendered_blocks(repo.workflow_text())

        assert len(blocks) == EXPECTED_BLOCK_COUNT
        for block in blocks:
            assert block == expected


def assert_minimization_preserves_coverage() -> None:
    """Assert minimizing a pattern set selects exactly the same paths."""

    @_minimization_property(replay_test_name="test_minimization_preserves_coverage")
    def assertion(patterns: set[str], probe: str) -> None:
        before = any(matches(probe, pattern) for pattern in patterns)
        after = any(matches(probe, pattern) for pattern in minimal_patterns(patterns))

        assert before == after

    assertion()


def assert_minimization_is_a_subset_of_its_input() -> None:
    """Assert minimization only ever removes patterns, never invents them."""

    @_minimization_property(
        replay_test_name="test_minimization_is_a_subset_of_its_input"
    )
    def assertion(patterns: set[str], probe: str) -> None:
        del probe
        minimized = minimal_patterns(patterns)

        assert set(minimized) <= patterns
        assert list(minimized) == sorted(minimized)

    assertion()


def _minimization_property(
    *,
    replay_test_name: str,
) -> Callable[[Callable[[set[str], str], None]], Callable[[], None]]:
    replay_path = f"{CI_TRIGGERS_PROPERTY_TEST_PATH}{replay_test_name}"

    def decorator(test_func: Callable[[set[str], str], None]) -> Callable[[], None]:
        configured = seed(MINIMIZATION_PROPERTY_SEED)(
            settings(max_examples=MINIMIZATION_PROPERTY_EXAMPLES, deadline=None)(
                given(patterns=trigger_pattern_sets(), probe=probe_paths())(test_func)
            )
        )

        def wrapper() -> None:
            try:
                configured()
            except AssertionError as error:
                error.add_note(f"Hypothesis seed: {MINIMIZATION_PROPERTY_SEED}")
                error.add_note(f"Replay path: {replay_path}")
                raise

        return wrapper

    return decorator


def _workflow_skeleton() -> str:
    block = f"{_WORKFLOW_INDENT}{BEGIN_MARKER}\n{_WORKFLOW_INDENT}{END_MARKER}\n"
    return (
        "on:\n"
        "  pull_request:\n"
        "    paths:\n"
        f"{block}"
        "  push:\n"
        "    branches: [main]\n"
        "    paths:\n"
        f"{block}"
    )


def _rendered_blocks(workflow_text: str) -> tuple[tuple[str, ...], ...]:
    blocks: list[tuple[str, ...]] = []
    current: list[str] | None = None
    for line in workflow_text.splitlines():
        stripped = line.strip()
        if stripped == BEGIN_MARKER:
            current = []
        elif stripped == END_MARKER and current is not None:
            blocks.append(tuple(current))
            current = None
        elif current is not None:
            current.append(stripped.removeprefix('- "').removesuffix('"'))
    return tuple(blocks)
