"""Mapping tests from each eval profile to the Claude model and effort the runner passes."""

from __future__ import annotations

import pytest

from outcomeeng.models import EVAL_PROFILE_MODELS, AgentProfile
from outcomeeng_evals.runner import EFFORT_FLAG, MODEL_FLAG
from outcomeeng_testing.harnesses.eval_runner import record_profile_invocation


@pytest.mark.parametrize("profile", tuple(AgentProfile))
def test_runner_passes_profile_model_and_effort(profile: AgentProfile) -> None:
    argv = record_profile_invocation(profile).argv

    assert argv[argv.index(MODEL_FLAG) + 1] == EVAL_PROFILE_MODELS[profile].model
    assert argv[argv.index(EFFORT_FLAG) + 1] == EVAL_PROFILE_MODELS[profile].effort
