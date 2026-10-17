"""Mapping evidence that the build's per-agent tables and generated trees follow the Target members."""

from __future__ import annotations

from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses.agent_tokens import (
    build_agent_keyed_tables,
    generated_tree_directory_names,
)


def test_every_per_agent_table_is_keyed_by_exactly_the_target_members() -> None:
    for table in build_agent_keyed_tables():
        assert all(isinstance(key, Target) for key in table.keys), table.name
        assert set(table.keys) == set(Target), table.name


def test_every_generated_tree_directory_is_named_by_a_target_value() -> None:
    assert generated_tree_directory_names() == {target.value for target in Target}
