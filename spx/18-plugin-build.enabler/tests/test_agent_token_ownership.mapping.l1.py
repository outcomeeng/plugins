"""Mapping evidence that every generated-output target is a token of the agent-token owner."""

from __future__ import annotations

from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses.agent_tokens import declared_agent_tokens


def test_every_target_takes_its_value_from_the_owner_token_of_the_same_name() -> None:
    owner_tokens = declared_agent_tokens()
    for target in Target:
        assert owner_tokens.get(target.name) == target.value, target
