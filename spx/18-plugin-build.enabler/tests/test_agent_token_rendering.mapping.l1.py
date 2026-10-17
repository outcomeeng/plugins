"""Mapping evidence that a build renders the agent tokens beside each spec-tree script that reads them."""

from __future__ import annotations

from outcomeeng.distribution.contracts import (
    AGENT_TOKEN_DATA_FILENAME,
    AGENT_TOKEN_READING_PLUGIN_NAME,
    Target,
)
from outcomeeng_testing.harnesses.agent_tokens import (
    TOKEN_READING_SCRIPT,
    build_sample_agent_token_tree,
    owner_source_tokens,
)


def test_a_data_file_stands_beside_the_reading_script_in_every_target_tree() -> None:
    built = build_sample_agent_token_tree()
    expected = {
        (
            target.value,
            AGENT_TOKEN_READING_PLUGIN_NAME
            / TOKEN_READING_SCRIPT.parent
            / AGENT_TOKEN_DATA_FILENAME,
        )
        for target in Target
    }
    assert {
        (file.target_directory, file.path) for file in built.token_files
    } == expected


def test_every_rendered_data_file_equals_the_owner_declaration() -> None:
    built = build_sample_agent_token_tree()
    assert built.token_files
    declaration = owner_source_tokens()
    for rendered in built.token_files:
        assert rendered.document == declaration, rendered
