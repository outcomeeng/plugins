"""Mapping evidence that the build takes its agent tokens from the coding-agents owner and declares none."""

from __future__ import annotations

from outcomeeng.distribution.contracts import Target, declared_agent_tokens
from outcomeeng_testing.harnesses.agent_tokens import (
    build_module_token_literals,
    owner_source_tokens,
)


def test_the_build_loads_the_tokens_the_owner_source_declares() -> None:
    assert declared_agent_tokens() == owner_source_tokens()


def test_every_target_takes_its_value_from_the_owner_token_of_the_same_name() -> None:
    owner_tokens = owner_source_tokens()
    for target in Target:
        assert owner_tokens.get(target.name) == target.value, target


def test_no_build_module_spells_an_agent_token() -> None:
    assert build_module_token_literals() == ()
