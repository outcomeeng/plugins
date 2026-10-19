"""Scenario evidence for the agent-tokens data file the review-result module loads."""

from __future__ import annotations

import json
import pathlib

import pytest

from outcomeeng.distribution.contracts import AGENT_TOKEN_DATA_FILENAME
from outcomeeng_testing.generators.agent_tokens_load import (
    LoadFailureCase,
    load_failure_cases,
)
from outcomeeng_testing.harnesses import reviewing_changes as harness

MODULE = harness.load_review_result_module()
RENDERED_TOKENS_PATH = harness.SCRIPTS_DIR / AGENT_TOKEN_DATA_FILENAME


def test_the_module_reads_the_file_the_build_renders_beside_it() -> None:
    assert MODULE.AGENT_TOKENS_PATH == RENDERED_TOKENS_PATH
    assert MODULE.load_agent_tokens(RENDERED_TOKENS_PATH) == json.loads(
        RENDERED_TOKENS_PATH.read_text(encoding="utf-8")
    )


def test_the_citation_candidates_derive_from_the_rendered_tokens() -> None:
    rendered = json.loads(RENDERED_TOKENS_PATH.read_text(encoding="utf-8"))

    assert MODULE.GENERATED_TREE_AGENT_TOKENS == tuple(
        rendered[key] for key in MODULE.AGENT_TOKENS_REQUIRED_KEYS
    )


@pytest.mark.parametrize(
    "case", load_failure_cases(MODULE), ids=lambda case: case.case_id
)
def test_the_module_reports_a_load_failure_as_an_error_line_with_exit_two(
    tmp_path: pathlib.Path, case: LoadFailureCase
) -> None:
    result = harness.run_review_result_with_agent_tokens_file(
        tmp_path, tokens=case.tokens, make_directory=case.make_directory
    )

    assert result.returncode == MODULE.AGENT_TOKENS_LOAD_FAILURE_EXIT_CODE
    assert harness.TRACEBACK_HEADER not in result.stderr
    assert result.stderr.startswith(case.expected_fragment)
    assert result.stderr.count("\n") == 1
    assert result.stdout == ""
