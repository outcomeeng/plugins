"""Evidence harness for the eval model-runner boundary.

Exposes the captured process-contract fixture, recording runners, and the
runner's private projections as observations; every verdict lives in the
linked tests.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_evals.runner import (
    ClaudeCliRunner,
    RunMetadata,
    _metadata_from_envelope,
    _subprocess_env,
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


def process_fixture() -> ModelProcessFixture:
    """Load the captured claude process contract."""

    return load_model_process_fixture(_FIXTURE_PATH)


def subprocess_environment(environment: dict[str, str]) -> dict[str, str]:
    """Return the environment the runner passes to the claude subprocess."""

    return _subprocess_env(environment)


def metadata_from_envelope(envelope: dict[str, object]) -> RunMetadata:
    """Return the trial metadata the runner parses from a claude envelope."""

    return _metadata_from_envelope(envelope)


def recording_runner(
    fixture: ModelProcessFixture,
    *,
    environment: dict[str, str] | None = None,
    bare: bool | None = None,
    returncode: int | None = None,
) -> tuple[ClaudeCliRunner, RecordingModelProcessLauncher]:
    """Build a real runner over a launcher that records the process invocation."""

    recorder = (
        make_recording_model_process_launcher(fixture)
        if returncode is None
        else make_recording_model_process_launcher(fixture, returncode=returncode)
    )
    runner = ClaudeCliRunner(
        plugin_dir=Path.cwd(),
        model=fixture.explicit_model,
        environment={} if environment is None else environment,
        bare=bare,
        process_launcher=recorder,
    )
    return runner, recorder
