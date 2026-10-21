"""Mapping evidence for the agent tokens the review-result module takes from its data file."""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.generators.agent_tokens_load import staged_tokens_document
from outcomeeng_testing.harnesses import reviewing_changes as harness

MODULE = harness.load_review_result_module()


def test_each_citation_candidate_token_maps_to_the_value_the_staged_data_file_holds(
    tmp_path: pathlib.Path,
) -> None:
    """Candidates follow the data file beside the module, so none is declared in it.

    A module that declares its own tokens, or reads them from anywhere but the
    file beside it, yields candidates that differ from the staged file's values
    and fails this check.
    """
    staged = staged_tokens_document(MODULE)
    copy = harness.load_review_result_with_agent_tokens(tmp_path, tokens=staged)

    expected = tuple(json.loads(staged)[key] for key in copy.AGENT_TOKENS_REQUIRED_KEYS)
    assert copy.GENERATED_TREE_AGENT_TOKENS == expected
