"""Mapping evidence that each rendered agent-token file equals the declaration it renders."""

from __future__ import annotations

from outcomeeng_testing.harnesses.agent_tokens import (
    declared_agent_tokens,
    rendered_agent_token_files,
)


def test_each_reading_script_has_a_rendered_file_equal_to_the_declaration() -> None:
    declaration = declared_agent_tokens()
    observations = rendered_agent_token_files()
    assert observations
    for observed in observations:
        assert observed.document == declaration, (observed.target, observed.script)
