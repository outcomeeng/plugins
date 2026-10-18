"""Scenario evidence for the generator's agent-tokens data file load failures."""

from __future__ import annotations

import json
import pathlib

import pytest

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()
USAGE_ERROR_EXIT_CODE = 2
ERROR_PREFIX = "error: agent tokens file"
TRACEBACK_MARKER = "Traceback"
ADVICE = MODULE.AGENT_TOKENS_REINSTALL_ADVICE
VALID_TOKENS = {"CLAUDE": "claude", "CODEX": "codex"}


def _load_error(path: pathlib.Path) -> str:
    with pytest.raises(MODULE.AgentTokensLoadError) as raised:
        MODULE.load_agent_tokens(path)
    return str(raised.value)


def test_a_complete_file_loads_its_tokens(tmp_path: pathlib.Path) -> None:
    path = tmp_path / harness.AGENT_TOKENS_FILENAME
    path.write_text(json.dumps(VALID_TOKENS), encoding="utf-8")

    assert MODULE.load_agent_tokens(path) == VALID_TOKENS


def test_an_absent_file_names_its_path_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / harness.AGENT_TOKENS_FILENAME

    message = _load_error(path)

    assert message.startswith(f"{ERROR_PREFIX} not found: {path}")
    assert message.endswith(ADVICE)


def test_an_unreadable_file_names_its_path_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / harness.AGENT_TOKENS_FILENAME
    path.mkdir()

    message = _load_error(path)

    assert message.startswith(f"{ERROR_PREFIX} unreadable: {path}")
    assert message.endswith(ADVICE)


def test_malformed_json_names_its_path_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / harness.AGENT_TOKENS_FILENAME
    path.write_text("{not json", encoding="utf-8")

    message = _load_error(path)

    assert message.startswith(f"{ERROR_PREFIX} is not valid JSON: {path}")
    assert message.endswith(ADVICE)


def test_a_non_object_value_names_its_type_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / harness.AGENT_TOKENS_FILENAME
    path.write_text(json.dumps(["CLAUDE", "CODEX"]), encoding="utf-8")

    message = _load_error(path)

    assert message.startswith(f"{ERROR_PREFIX} must hold a JSON object: {path}")
    assert "(found list)" in message
    assert message.endswith(ADVICE)


@pytest.mark.parametrize("missing", MODULE.AGENT_TOKENS_REQUIRED_KEYS)
def test_a_missing_required_key_names_it_and_the_keys_found(
    tmp_path: pathlib.Path, missing: str
) -> None:
    path = tmp_path / harness.AGENT_TOKENS_FILENAME
    kept = {key: key.lower() for key in VALID_TOKENS if key != missing}
    path.write_text(json.dumps(kept), encoding="utf-8")

    message = _load_error(path)

    assert message.startswith(f"{ERROR_PREFIX} lacks required key(s) {missing}: {path}")
    assert f"(keys found: {', '.join(sorted(kept))})" in message
    assert message.endswith(ADVICE)


def test_an_empty_object_names_every_required_key_and_no_keys_found(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / harness.AGENT_TOKENS_FILENAME
    path.write_text("{}", encoding="utf-8")

    message = _load_error(path)

    required = ", ".join(MODULE.AGENT_TOKENS_REQUIRED_KEYS)
    assert f"lacks required key(s) {required}" in message
    assert "(keys found: none)" in message


@pytest.mark.parametrize(
    ("tokens", "make_directory", "expected_fragment"),
    [
        (None, False, f"{ERROR_PREFIX} not found: "),
        (None, True, f"{ERROR_PREFIX} unreadable: "),
        ("{not json", False, f"{ERROR_PREFIX} is not valid JSON: "),
        ("[]", False, f"{ERROR_PREFIX} must hold a JSON object: "),
        (
            '{"CLAUDE": "claude"}',
            False,
            f"{ERROR_PREFIX} lacks required key(s) CODEX: ",
        ),
        ('{"CODEX": "codex"}', False, f"{ERROR_PREFIX} lacks required key(s) CLAUDE: "),
    ],
    ids=["absent", "unreadable", "malformed", "non-object", "no-codex", "no-claude"],
)
def test_the_script_reports_a_load_failure_as_an_error_line_with_exit_two(
    tmp_path: pathlib.Path,
    tokens: str | None,
    make_directory: bool,
    expected_fragment: str,
) -> None:
    result = harness.run_script_with_agent_tokens_file(
        tmp_path, tokens=tokens, make_directory=make_directory
    )

    assert result.returncode == USAGE_ERROR_EXIT_CODE
    assert TRACEBACK_MARKER not in result.stderr
    assert result.stderr.startswith(expected_fragment)
    assert result.stderr.count("\n") == 1
    assert result.stdout == ""
