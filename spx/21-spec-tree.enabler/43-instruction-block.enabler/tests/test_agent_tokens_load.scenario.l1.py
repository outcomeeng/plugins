"""Scenario evidence for the generator's agent-tokens data file load failures."""

from __future__ import annotations

import json
import pathlib

import pytest

from outcomeeng.distribution.contracts import (
    AGENT_TOKEN_DATA_FILENAME,
    declared_agent_tokens,
)
from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()
USAGE_ERROR_EXIT_CODE = MODULE.AGENT_TOKENS_LOAD_FAILURE_EXIT_CODE
ERROR_PREFIX = MODULE.AGENT_TOKENS_ERROR_PREFIX
ADVICE = MODULE.AGENT_TOKENS_REINSTALL_ADVICE
VALID_TOKENS = declared_agent_tokens()
NON_OBJECT_DOCUMENT = json.dumps(list(VALID_TOKENS.values()))
PARTIAL_DOCUMENT_ROWS = [
    (
        json.dumps({key: token for key, token in VALID_TOKENS.items() if key != missing}),
        False,
        f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_LACKS_KEYS} {missing}: ",
    )
    for missing in MODULE.AGENT_TOKENS_REQUIRED_KEYS
]
PARTIAL_DOCUMENT_IDS = [
    f"no-{VALID_TOKENS[missing]}" for missing in MODULE.AGENT_TOKENS_REQUIRED_KEYS
]


def _load_error(path: pathlib.Path) -> str:
    with pytest.raises(MODULE.AgentTokensLoadError) as raised:
        MODULE.load_agent_tokens(path)
    return str(raised.value)


def test_a_complete_file_loads_its_tokens(tmp_path: pathlib.Path) -> None:
    path = tmp_path / AGENT_TOKEN_DATA_FILENAME
    path.write_text(json.dumps(VALID_TOKENS), encoding="utf-8")

    assert MODULE.load_agent_tokens(path) == VALID_TOKENS


def test_an_absent_file_names_its_path_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / AGENT_TOKEN_DATA_FILENAME

    message = _load_error(path)

    assert message.startswith(
        f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_NOT_FOUND}{path}"
    )
    assert message.endswith(ADVICE)


def test_an_unreadable_file_names_its_path_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / AGENT_TOKEN_DATA_FILENAME
    path.mkdir()

    message = _load_error(path)

    assert message.startswith(
        f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_UNREADABLE}{path}"
    )
    assert message.endswith(ADVICE)


def test_malformed_json_names_its_path_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / AGENT_TOKEN_DATA_FILENAME
    path.write_text("{not json", encoding="utf-8")

    message = _load_error(path)

    assert message.startswith(
        f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_NOT_VALID_JSON}{path}"
    )
    assert message.endswith(ADVICE)


def test_a_non_object_value_names_its_type_and_the_fix(tmp_path: pathlib.Path) -> None:
    path = tmp_path / AGENT_TOKEN_DATA_FILENAME
    path.write_text(NON_OBJECT_DOCUMENT, encoding="utf-8")

    message = _load_error(path)

    found_type = type(json.loads(NON_OBJECT_DOCUMENT)).__name__
    assert message.startswith(
        f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_NOT_AN_OBJECT}{path}"
    )
    assert f"{MODULE.AGENT_TOKENS_FOUND_TYPE_OPEN}{found_type}" in message
    assert message.endswith(ADVICE)


@pytest.mark.parametrize("missing", MODULE.AGENT_TOKENS_REQUIRED_KEYS)
def test_a_missing_required_key_names_it_and_the_keys_found(
    tmp_path: pathlib.Path, missing: str
) -> None:
    path = tmp_path / AGENT_TOKEN_DATA_FILENAME
    kept = {key: token for key, token in VALID_TOKENS.items() if key != missing}
    path.write_text(json.dumps(kept), encoding="utf-8")

    message = _load_error(path)

    assert message.startswith(
        f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_LACKS_KEYS} {missing}: {path}"
    )
    assert (
        f"{MODULE.AGENT_TOKENS_KEYS_FOUND_OPEN}{', '.join(sorted(kept))}" in message
    )
    assert message.endswith(ADVICE)


def test_an_empty_object_names_every_required_key_and_no_keys_found(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / AGENT_TOKEN_DATA_FILENAME
    path.write_text("{}", encoding="utf-8")

    message = _load_error(path)

    required = ", ".join(MODULE.AGENT_TOKENS_REQUIRED_KEYS)
    assert f"{MODULE.AGENT_TOKENS_LACKS_KEYS} {required}" in message
    assert f"{MODULE.AGENT_TOKENS_KEYS_FOUND_OPEN}{MODULE.AGENT_TOKENS_NO_KEYS}" in message


@pytest.mark.parametrize(
    ("tokens", "make_directory", "expected_fragment"),
    [
        (None, False, f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_NOT_FOUND}"),
        (None, True, f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_UNREADABLE}"),
        ("{not json", False, f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_NOT_VALID_JSON}"),
        (
            NON_OBJECT_DOCUMENT,
            False,
            f"{ERROR_PREFIX} {MODULE.AGENT_TOKENS_NOT_AN_OBJECT}",
        ),
        *PARTIAL_DOCUMENT_ROWS,
    ],
    ids=["absent", "unreadable", "malformed", "non-object", *PARTIAL_DOCUMENT_IDS],
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
    assert harness.TRACEBACK_HEADER not in result.stderr
    assert result.stderr.startswith(expected_fragment)
    assert result.stderr.count("\n") == 1
    assert result.stdout == ""
