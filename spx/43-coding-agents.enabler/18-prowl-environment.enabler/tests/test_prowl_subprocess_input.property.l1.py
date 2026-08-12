import json

from outcomeeng_testing.harnesses.prowl_environment import (
    run_subprocess_input_probe,
    run_subprocess_input_property,
)


def test_default_subprocess_input_property() -> None:
    absent = run_subprocess_input_probe(None)
    assert absent.returncode == 0
    assert absent.stderr == ""
    assert json.loads(absent.stdout) == {"isCharDevice": True, "input": ""}

    def assert_explicit_input(input_text: str) -> None:
        explicit = run_subprocess_input_probe(input_text)
        assert explicit.returncode == 0
        assert explicit.stderr == ""
        assert json.loads(explicit.stdout) == {
            "isCharDevice": False,
            "input": input_text,
        }

    run_subprocess_input_property(assert_explicit_input)
