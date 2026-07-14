"""Mapping harness evidence for root instruction-file topology seed resolution."""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.instruction_block import (
    INSTRUCTION_AGENTS,
    INSTRUCTION_CLAUDE,
    ROOT_AGENTS_BODY,
    ROOT_CLAUDE_BODY,
    ROOT_SHARED_BODY,
    RootInstructionTopology,
    materialize_root_instruction_topology,
    root_instruction_topology_only_agents,
    root_instruction_topology_only_claude,
    root_instruction_topology_separate,
    root_instruction_topology_symlinked,
)


@pytest.mark.parametrize(
    ("topology", "expected"),
    [
        (
            root_instruction_topology_only_claude(),
            {
                INSTRUCTION_CLAUDE: ROOT_CLAUDE_BODY,
                INSTRUCTION_AGENTS: ROOT_CLAUDE_BODY,
            },
        ),
        (
            root_instruction_topology_only_agents(),
            {
                INSTRUCTION_CLAUDE: ROOT_AGENTS_BODY,
                INSTRUCTION_AGENTS: ROOT_AGENTS_BODY,
            },
        ),
        (
            root_instruction_topology_separate(),
            {
                INSTRUCTION_CLAUDE: ROOT_CLAUDE_BODY,
                INSTRUCTION_AGENTS: ROOT_AGENTS_BODY,
            },
        ),
        (
            root_instruction_topology_symlinked(),
            {
                INSTRUCTION_CLAUDE: ROOT_SHARED_BODY,
                INSTRUCTION_AGENTS: ROOT_SHARED_BODY,
            },
        ),
    ],
)
def test_root_instruction_topology_maps_to_harness_seed_bodies(
    tmp_path: pathlib.Path,
    topology: RootInstructionTopology,
    expected: dict[str, str],
) -> None:
    assert materialize_root_instruction_topology(tmp_path, topology) == expected
