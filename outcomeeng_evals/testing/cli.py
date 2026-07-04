"""Test infrastructure for exercising the eval Click CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from click.testing import CliRunner

from outcomeeng_evals.cli.commands.run import RUNNER_FACTORY_KEY
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.runner import ModelRunner
from outcomeeng_evals.testing.fakes import RecordingRunner, StubModelRunner


@dataclass(frozen=True)
class RunCliHarness:
    """Temporary run-command fixture with an injectable recording runner."""

    eval_toml: Path
    plugin_dir: Path
    runner: CliRunner
    recorder: RecordingRunner
    models: list[str] = field(default_factory=list)

    @property
    def runner_context(self) -> dict[str, object]:
        def runner_factory(
            *,
            plugin_dir: Path,
            model: str,
            max_budget_usd: float,
            timeout_seconds: int,
        ) -> ModelRunner:
            del plugin_dir, max_budget_usd, timeout_seconds
            self.models.append(model)
            return self.recorder

        return {RUNNER_FACTORY_KEY: runner_factory}


def build_run_cli_harness(
    tmp_path: Path,
    *,
    cases_jsonl: str,
    prompt_template: str = "Case {case_id}: {input_json}",
    model: str | None = None,
) -> RunCliHarness:
    """Create a temporary eval suite wired to a recording model runner."""
    eval_dir = tmp_path / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    model_line = f'model = "{model}"\n' if model is not None else ""
    (eval_dir / EVAL_TOML_FILENAME).write_text(
        f'title = "rule"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n{model_line}',
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text(cases_jsonl, encoding="utf-8")
    (eval_dir / "prompt.md").write_text(prompt_template, encoding="utf-8")
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    recorder = RecordingRunner(inner=StubModelRunner(response='{"ok": true}'))
    return RunCliHarness(
        eval_toml=eval_dir / EVAL_TOML_FILENAME,
        plugin_dir=plugin_dir,
        runner=CliRunner(),
        recorder=recorder,
    )
