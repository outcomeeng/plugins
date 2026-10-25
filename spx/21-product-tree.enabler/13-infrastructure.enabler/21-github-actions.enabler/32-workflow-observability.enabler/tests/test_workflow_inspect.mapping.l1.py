"""Mapping evidence: each `workflow_inspect.py` subcommand maps wrong-shape `gh` JSON to a located error."""

from __future__ import annotations

import json

import pytest

from outcomeeng_testing.harnesses.workflow_inspect import GhReply, run_cli

# Subcommand argv, the JSON shape `gh` must not return for it, and the located prefix and gh name
# the spec's error contract names for it.
WRONG_SHAPE_CASES = (
    (["runs"], "{}", "runs: gh run list returned dict, not a list. Next: "),
    (["run", "9001"], "[]", "run 9001: gh run view returned no run object. Next: "),
    (["jobs", "9001"], "[]", "jobs 9001: gh run view returned no jobs object. Next: "),
    (
        ["checks", "42"],
        "[]",
        "checks 42: gh pr view returned no pull request object. Next: ",
    ),
    (
        ["artifacts", "9001"],
        "[]",
        "artifacts 9001: gh api returned no artifacts object. Next: ",
    ),
    (
        ["workflow-files"],
        "{}",
        "workflow-files: gh workflow list returned no list. Next: ",
    ),
)


@pytest.mark.parametrize(
    ("argv", "gh_stdout", "expected_prefix"),
    WRONG_SHAPE_CASES,
    ids=[" ".join(case[0]) for case in WRONG_SHAPE_CASES],
)
def test_wrong_shape_json_maps_to_a_located_error_and_exit_one(
    argv: list[str], gh_stdout: str, expected_prefix: str
) -> None:
    observed = run_cli(argv, GhReply(0, gh_stdout))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert payload["error"].startswith(expected_prefix)
    assert payload["error"].endswith(".")
