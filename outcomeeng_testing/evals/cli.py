"""Test infrastructure for exercising the eval Click CLI.

Builders here arrange eval suites and invoke the real Click commands; they
return the invocation results and recorded observations, and the linked tests
own every predicate.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import chdir, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from click.testing import CliRunner, Result

from outcomeeng.models import AgentProfile
from outcomeeng_evals.case import (
    CASE_ID_FIELD,
    CASE_INPUT_FIELD,
    EXPECTED_VERDICT_FIELD,
    MUST_CONTAIN_FIELD,
)
from outcomeeng_evals.ci_plan import CiMode
from outcomeeng_evals.cli import main
from outcomeeng_evals.cli.commands.plan import plan_command
from outcomeeng_evals.cli.commands.run import (
    PLUGIN_DIR_OPTION,
    RUNNER_FACTORY_KEY,
    run_command,
)
from outcomeeng_evals.definition import (
    CASES_FIELD,
    DEFAULT_PROFILE,
    EVAL_TOML_FILENAME,
    PROFILE_FIELD,
    PROMPT_FIELD,
    RUNS_DIRNAME,
    TITLE_FIELD,
    CiPolicy,
)
from outcomeeng_evals.history import HISTORY_FILENAME
from outcomeeng_evals.report import JSON_REPORT_SUFFIX
from outcomeeng_evals.runner import ModelRunner
from outcomeeng_evals.settings import DEFAULT_MAX_BUDGET_USD, DEFAULT_TIMEOUT_SECONDS
from outcomeeng_testing.evals.factories import (
    EVAL_CASES_FILENAME,
    EVAL_PROMPT_FILENAME,
    make_eval_dir,
)
from outcomeeng_testing.evals.fakes import RecordingRunner, StubModelRunner

PLAN_PLUGIN_DIR: Final = "dist/claude/spec-tree"
PLAN_OWNED_PATH_PATTERN: Final = "src/plugins/spec-tree/skills/manage-pr/**"
PLAN_MANUAL_OWNED_PATH_PATTERN: Final = "src/plugins/spec-tree/skills/review-changes/**"
PLAN_SMOKE_CASE_ID: Final = "happy-path"
PLAN_OWNED_PATH_CHANGE: Final = "src/plugins/spec-tree/skills/manage-pr/SKILL.md\n"
PLAN_RENAMED_OWNED_PATH_CHANGE: Final = (
    "R100\tsrc/plugins/spec-tree/skills/manage-pr/SKILL.md\tdocs/manage-pr.md\n"
)
PLAN_HARNESS_PATH_CHANGE: Final = "outcomeeng_evals/suite.py\n"
PLAN_TEST_GENERATOR_PATH_CHANGE: Final = "outcomeeng_testing/generators/gate.py\n"
PLAN_TEST_HARNESS_PATH_CHANGE: Final = "outcomeeng_testing/harnesses/gate.py\n"
PLAN_COPIED_HARNESS_PATH_CHANGE: Final = (
    "C100\toutcomeeng_evals/suite.py\tdocs/copied-suite.py\n"
)
PLAN_OWNED_AND_HARNESS_PATH_CHANGE: Final = (
    f"{PLAN_OWNED_PATH_CHANGE}{PLAN_HARNESS_PATH_CHANGE}"
)
PLAN_UNRELATED_PATH_CHANGE: Final = "README.md\n"
PLAN_RELATIVE_EVAL_ROOT: Final = "spx"
PLAN_MANUAL_CASE_ID: Final = "manual-smoke"
PLAN_CHANGED_PATHS_FILENAME: Final = "changed.txt"
DISCOVER_RULE: Final = "rule-one"

RUN_PROMPT_PREFIX: Final = "Case "
RUN_PROMPT_TEMPLATE: Final = f"{RUN_PROMPT_PREFIX}{{case_id}}: {{input_json}}"
RUN_STUB_RESPONSE: Final = '{"ok": true}'
RUN_CASE_ALPHA_ID: Final = "alpha"
RUN_CASE_BETA_ID: Final = "beta"
RUN_CASE_GAMMA_ID: Final = "gamma"
RUN_UNKNOWN_CASE_ID: Final = "missing"
RUN_CONFIGURED_MAX_BUDGET_USD: Final = DEFAULT_MAX_BUDGET_USD * 2
RUN_CONFIGURED_TIMEOUT_SECONDS: Final = DEFAULT_TIMEOUT_SECONDS * 2


def _run_case_record(case_id: str, ordinal: int) -> str:
    """Render one eval case record whose verdict the stub runner's response satisfies."""

    return json.dumps(
        {
            CASE_ID_FIELD: case_id,
            CASE_INPUT_FIELD: {"x": ordinal},
            EXPECTED_VERDICT_FIELD: {
                MUST_CONTAIN_FIELD: [json.loads(RUN_STUB_RESPONSE)]
            },
        },
        separators=(",", ":"),
    )


RUN_CASE_ALPHA: Final = _run_case_record(RUN_CASE_ALPHA_ID, 1)
RUN_CASE_BETA: Final = _run_case_record(RUN_CASE_BETA_ID, 2)
RUN_CASE_GAMMA: Final = _run_case_record(RUN_CASE_GAMMA_ID, 3)
RUN_DEFINITION_PROFILE: Final = next(
    profile for profile in AgentProfile if profile is not DEFAULT_PROFILE
)
RUN_OVERRIDE_PROFILE: Final = next(
    profile
    for profile in AgentProfile
    if profile not in (DEFAULT_PROFILE, RUN_DEFINITION_PROFILE)
)
HISTORY_VERSION_1_COMPATIBILITY_FIXTURE: Final = (
    Path(__file__).parents[2]
    / "outcomeeng_testing/fixtures/evals/history_version_1_compatibility.jsonl"
)
HISTORY_ROWS_FIXTURE: Final = (
    Path(__file__).parents[2] / "outcomeeng_testing/fixtures/evals/history_rows.json"
)


@dataclass(frozen=True)
class RunCliHarness:
    """Temporary run-command fixture with an injectable recording runner."""

    eval_toml: Path
    plugin_dir: Path
    runner: CliRunner
    recorder: RecordingRunner
    profiles: list[AgentProfile] = field(default_factory=list)
    max_budgets_usd: list[float] = field(default_factory=list)
    timeouts_seconds: list[int] = field(default_factory=list)

    @property
    def runner_context(self) -> dict[str, object]:
        def runner_factory(
            *,
            plugin_dir: Path,
            profile: AgentProfile,
            max_budget_usd: float,
            timeout_seconds: int,
        ) -> ModelRunner:
            del plugin_dir
            self.profiles.append(profile)
            self.max_budgets_usd.append(max_budget_usd)
            self.timeouts_seconds.append(timeout_seconds)
            return self.recorder

        return {RUNNER_FACTORY_KEY: runner_factory}

    def invoke_run(self, *extra_args: str) -> Result:
        """Invoke ``run`` on this suite with the recording runner factory."""

        return self.runner.invoke(
            main,
            [
                str(run_command.name),
                str(self.eval_toml),
                PLUGIN_DIR_OPTION,
                str(self.plugin_dir),
                *extra_args,
            ],
            obj=self.runner_context,
        )

    def recorded_prompts(self) -> tuple[str, ...]:
        """Return every prompt the recording runner received, in call order."""

        return tuple(prompt for prompt, _result in self.recorder.transcripts)

    def recorded_case_ids(self) -> tuple[str, ...]:
        """Return the case id each recorded prompt was rendered for, in call order."""

        return tuple(
            prompt.removeprefix(RUN_PROMPT_PREFIX).split(":", 1)[0]
            for prompt in self.recorded_prompts()
        )

    def result_payloads(self) -> tuple[dict[str, object], ...]:
        """Return every JSON results document the runs wrote for this suite."""

        runs_dir = self.eval_toml.parent / RUNS_DIRNAME
        return tuple(
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(runs_dir.glob(f"*{JSON_REPORT_SUFFIX}"))
        )

    def history_rows(self) -> tuple[dict[str, object], ...]:
        """Return every row the runs appended to this suite's history file."""

        history_path = self.eval_toml.parent / HISTORY_FILENAME
        return tuple(
            json.loads(line)
            for line in history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )


def build_run_cli_harness(
    tmp_path: Path,
    *,
    cases_jsonl: str,
    prompt_template: str = RUN_PROMPT_TEMPLATE,
    profile: AgentProfile | None = None,
) -> RunCliHarness:
    """Create a temporary eval suite wired to a recording model runner."""
    eval_dir = tmp_path / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    profile_line = f'{PROFILE_FIELD} = "{profile}"\n' if profile is not None else ""
    (eval_dir / EVAL_TOML_FILENAME).write_text(
        f'{TITLE_FIELD} = "rule"\n{CASES_FIELD} = "{EVAL_CASES_FILENAME}"\n'
        f'{PROMPT_FIELD} = "{EVAL_PROMPT_FILENAME}"\n{profile_line}',
        encoding="utf-8",
    )
    (eval_dir / EVAL_CASES_FILENAME).write_text(cases_jsonl, encoding="utf-8")
    (eval_dir / EVAL_PROMPT_FILENAME).write_text(prompt_template, encoding="utf-8")
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    recorder = RecordingRunner(inner=StubModelRunner(response=RUN_STUB_RESPONSE))
    return RunCliHarness(
        eval_toml=eval_dir / EVAL_TOML_FILENAME,
        plugin_dir=plugin_dir,
        runner=CliRunner(),
        recorder=recorder,
    )


def invoke_run_with_workers(tmp_path: Path, workers: int) -> Result:
    """Invoke ``run`` with a worker count against an empty eval definition."""

    eval_toml = tmp_path / EVAL_TOML_FILENAME
    eval_toml.write_text("", encoding="utf-8")
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    return CliRunner().invoke(
        main,
        [
            str(run_command.name),
            str(eval_toml),
            PLUGIN_DIR_OPTION,
            str(plugin_dir),
            "--workers",
            str(workers),
        ],
    )


def make_discoverable_eval(root: Path) -> Path:
    """Write one eval definition nested below ``root`` and return its path."""

    return make_eval_dir(
        root / "subtree" / "evals" / DISCOVER_RULE, title=DISCOVER_RULE
    )


def make_plan_eval_dir(root: Path) -> Path:
    """Write the owned-path suite PR planning selects from and return its path."""

    return make_eval_dir(
        root / "evals" / "rule",
        title="rule",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=(PLAN_OWNED_PATH_PATTERN,),
        smoke_case_ids=(PLAN_SMOKE_CASE_ID,),
    )


def make_mixed_policy_plan_evals(root: Path) -> Path:
    """Write one automatic and one manual suite and return the automatic one."""

    automatic_eval = make_eval_dir(
        root / "evals" / "automatic",
        title="automatic",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=(PLAN_OWNED_PATH_PATTERN,),
        smoke_case_ids=(PLAN_SMOKE_CASE_ID,),
    )
    make_eval_dir(
        root / "evals" / "manual",
        title="manual",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=(PLAN_MANUAL_OWNED_PATH_PATTERN,),
        smoke_case_ids=(PLAN_MANUAL_CASE_ID,),
        ci_policy=CiPolicy.MANUAL.value,
    )
    return automatic_eval


def write_changed_paths(directory: Path, changed_paths_text: str) -> Path:
    """Write a changed-paths file under ``directory`` and return its path."""

    changed_paths = directory / PLAN_CHANGED_PATHS_FILENAME
    changed_paths.write_text(changed_paths_text, encoding="utf-8")
    return changed_paths


def invoke_plan(
    root: Path,
    *,
    mode: CiMode,
    changed_paths_file: Path | None = None,
) -> Result:
    """Invoke ``plan`` over ``root`` in ``mode`` with optional changed paths."""

    changed_paths_args = (
        ("--changed-paths-file", str(changed_paths_file))
        if changed_paths_file is not None
        else ()
    )
    return CliRunner().invoke(
        main,
        [str(plan_command.name), str(root), "--mode", mode.value, *changed_paths_args],
    )


@dataclass(frozen=True)
class RelativePlanSuite:
    """A plan suite addressed by paths relative to the working directory."""

    eval_root: Path
    eval_toml: Path
    changed_paths_file: Path


@contextmanager
def relative_plan_suite(workspace: Path) -> Iterator[RelativePlanSuite]:
    """Work inside ``workspace`` with a suite whose case file is the changed path."""

    with chdir(workspace):
        eval_root = Path(PLAN_RELATIVE_EVAL_ROOT)
        eval_toml = make_plan_eval_dir(eval_root)
        changed_paths_file = write_changed_paths(
            Path(),
            f"{eval_toml.parent.as_posix()}/{EVAL_CASES_FILENAME}\n",
        )
        yield RelativePlanSuite(
            eval_root=eval_root,
            eval_toml=eval_toml,
            changed_paths_file=changed_paths_file,
        )
