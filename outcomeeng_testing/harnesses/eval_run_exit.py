"""Mapping harness for the eval run command's threshold exit contract."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from click.testing import CliRunner

from outcomeeng_evals.cli import EXIT_SUCCESS
from outcomeeng_evals.cli.commands.run import (
    PLUGIN_DIR_OPTION,
    RUNNER_FACTORY_KEY,
    run_command,
)
from outcomeeng_evals.runner import ModelRunner
from outcomeeng_evals.testing.fakes import StubModelRunner

_FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures/evals/run_exit"


def assert_run_command_exit_follows_definition_threshold() -> None:
    """Drive the real command against passing and below-threshold fixture runs."""

    responses = _load_responses()
    with TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        eval_dir = workspace / "eval"
        copytree(_FIXTURE_ROOT, eval_dir)
        plugin_dir = workspace / "plugin"
        plugin_dir.mkdir()

        passing = _invoke(
            eval_dir / "eval.toml", plugin_dir, iter(responses["passing"])
        )
        failing = _invoke(
            eval_dir / "eval.toml", plugin_dir, iter(responses["failing"])
        )
        default_rejects_configured_boundary = _invoke(
            eval_dir / "eval_default.toml",
            plugin_dir,
            iter(responses["passing"]),
        )
        default_passing = _invoke(
            eval_dir / "eval_default.toml",
            plugin_dir,
            iter(responses["all_passing"]),
        )

    assert passing == EXIT_SUCCESS
    assert failing != EXIT_SUCCESS
    assert default_rejects_configured_boundary != EXIT_SUCCESS
    assert default_passing == EXIT_SUCCESS


@contextmanager
def configured_threshold_run() -> Iterator[Path]:
    """Run the real command at the fixture's configured passing threshold."""

    responses = _load_responses()
    with TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        eval_dir = workspace / "eval"
        copytree(_FIXTURE_ROOT, eval_dir)
        plugin_dir = workspace / "plugin"
        plugin_dir.mkdir()

        exit_code = _invoke(
            eval_dir / "eval.toml", plugin_dir, iter(responses["passing"])
        )
        assert exit_code == EXIT_SUCCESS
        yield eval_dir


def _invoke(eval_toml: Path, plugin_dir: Path, responses: Iterator[str]) -> int:
    def runner_factory(
        *,
        plugin_dir: Path,
        model: str,
        max_budget_usd: float,
        timeout_seconds: int,
    ) -> ModelRunner:
        del plugin_dir, model, max_budget_usd, timeout_seconds
        return StubModelRunner(responder=lambda _prompt: next(responses))

    result = CliRunner().invoke(
        run_command,
        [str(eval_toml), PLUGIN_DIR_OPTION, str(plugin_dir)],
        obj={RUNNER_FACTORY_KEY: runner_factory},
    )
    return result.exit_code


def _load_responses() -> dict[str, tuple[str, ...]]:
    with (_FIXTURE_ROOT / "responses.json").open(encoding="utf-8") as fixture_file:
        response_paths = json.load(fixture_file)
    return {
        name: tuple(
            (_FIXTURE_ROOT / response_path).read_text(encoding="utf-8")
            for response_path in paths
        )
        for name, paths in response_paths.items()
    }
