import json

from outcomeeng_testing.generators.prowl_environment import subprocess_input_text
from outcomeeng_testing.harnesses.prowl_environment import (
    run_subprocess_input_probe,
    verify_prowl_mappings,
)


def test_prowl_environment_mappings() -> None:
    assert verify_prowl_mappings() == []


def test_default_subprocess_input_mapping() -> None:
    explicit_input = subprocess_input_text(1)

    absent = run_subprocess_input_probe(None)
    explicit = run_subprocess_input_probe(explicit_input)

    assert absent.returncode == 0
    assert absent.stderr == ""
    assert json.loads(absent.stdout) == {"isCharDevice": True, "input": ""}
    assert explicit.returncode == 0
    assert explicit.stderr == ""
    assert json.loads(explicit.stdout) == {
        "isCharDevice": False,
        "input": explicit_input,
    }
