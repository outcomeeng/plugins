"""Mapping evidence that the build's per-agent tables and generated trees follow the Target members."""

from __future__ import annotations

from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses.agent_tokens import (
    build_agent_keyed_tables,
    build_module_token_literals,
    build_sample_agent_token_tree,
)


def test_every_per_agent_table_is_keyed_by_exactly_the_target_members() -> None:
    for table in build_agent_keyed_tables():
        assert all(isinstance(key, Target) for key in table.keys), table.name
        assert set(table.keys) == set(Target), table.name


def test_a_build_emits_one_generated_tree_per_target_value() -> None:
    assert build_sample_agent_token_tree().tree_directories == {
        target.value for target in Target
    }


def test_no_build_module_spells_a_generated_tree_name() -> None:
    target_values = {target.value for target in Target}
    spelled = {literal.value for literal in build_module_token_literals()}
    assert spelled.isdisjoint(target_values)
