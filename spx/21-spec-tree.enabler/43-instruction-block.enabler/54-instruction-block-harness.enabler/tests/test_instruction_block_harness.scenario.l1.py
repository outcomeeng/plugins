"""Scenario evidence for root instruction-file topology materialization."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.instruction_block import (
    INSTRUCTION_AGENTS,
    INSTRUCTION_CLAUDE,
    ROOT_SHARED_BODY,
    materialize_root_instruction_topology,
    root_instruction_topology_symlinked,
)


def test_symlinked_harness_instruction_files_materialize_as_regular_files(
    tmp_path: pathlib.Path,
) -> None:
    topology = root_instruction_topology_symlinked()
    materialized = materialize_root_instruction_topology(tmp_path, topology)

    claude_path = tmp_path / INSTRUCTION_CLAUDE
    agents_path = tmp_path / INSTRUCTION_AGENTS

    assert claude_path.is_file()
    assert agents_path.is_file()
    assert not claude_path.is_symlink()
    assert not agents_path.is_symlink()
    assert claude_path.read_text(encoding="utf-8") == ROOT_SHARED_BODY
    assert agents_path.read_text(encoding="utf-8") == ROOT_SHARED_BODY
    assert materialized[INSTRUCTION_CLAUDE] == ROOT_SHARED_BODY
    assert materialized[INSTRUCTION_AGENTS] == ROOT_SHARED_BODY
