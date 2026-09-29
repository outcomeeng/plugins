"""Evidence harness for the eval model-runner boundary.

The harness builds runners around the captured model-process fixture and
returns what they record; the linked tests own every predicate.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from outcomeeng.models import AgentProfile
from outcomeeng_evals.runner import (
    ClaudeCliRunner,
    ModelProcessInvocation,
    RunResult,
)
from outcomeeng_testing.evals.factories import (
    ModelProcessFixture,
    load_model_process_fixture,
    make_recording_model_process_launcher,
)
from outcomeeng_testing.evals.fakes import RecordingModelProcessLauncher

_FIXTURE_PATH = (
    Path(__file__).parents[1] / "fixtures/evals/claude_process_contract.json"
)


@dataclass(frozen=True)
class CapturedProcessReplay:
    """Observations from one default Claude runner replaying the captured envelope."""

    fixture: ModelProcessFixture
    runner: ClaudeCliRunner
    result: RunResult
    invocations: tuple[ModelProcessInvocation, ...]


def captured_process_fixture() -> ModelProcessFixture:
    """Return the captured model-process contract fixture."""

    return load_model_process_fixture(_FIXTURE_PATH)


def recording_runner(
    fixture: ModelProcessFixture,
    *,
    environment: dict[str, str] | None = None,
    bare: bool | None = None,
    returncode: int = os.EX_OK,
) -> tuple[ClaudeCliRunner, RecordingModelProcessLauncher]:
    """Return a default Claude runner whose process boundary records and replays."""

    recorder = make_recording_model_process_launcher(fixture, returncode=returncode)
    runner = ClaudeCliRunner(
        plugin_dir=Path.cwd(),
        environment={} if environment is None else environment,
        bare=bare,
        process_launcher=recorder,
    )
    return runner, recorder


def replay_captured_process_contract() -> CapturedProcessReplay:
    """Run a default Claude runner against the captured envelope and record it."""

    fixture = captured_process_fixture()
    runner, recorder = recording_runner(fixture)
    result = runner.run(fixture.prompt)
    return CapturedProcessReplay(
        fixture=fixture,
        runner=runner,
        result=result,
        invocations=tuple(recorder.invocations),
    )


def record_profile_invocation(profile: AgentProfile) -> ModelProcessInvocation:
    """Run a Claude runner for ``profile`` and return its one recorded invocation."""

    fixture = captured_process_fixture()
    recorder = make_recording_model_process_launcher(fixture)
    runner = ClaudeCliRunner(
        plugin_dir=Path.cwd(),
        profile=profile,
        environment={},
        process_launcher=recorder,
    )
    runner.run(fixture.prompt)
    (invocation,) = recorder.invocations
    return invocation
