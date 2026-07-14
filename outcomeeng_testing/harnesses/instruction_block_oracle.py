"""Fixture-backed expected results for instruction-block harness evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from outcomeeng_testing.harnesses import instruction_block as harness

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "instruction_block"


def _fixture_files(name: str) -> dict[str, str]:
    payload = json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
    return cast(dict[str, str], payload["files"])


def _shared_bodies(body: str) -> harness.RootInstructionBodies:
    return harness.RootInstructionBodies(claude=body, agents=body)


def only_claude_topology_mapping() -> harness.RootInstructionBodies:
    files = _fixture_files(harness.TOPOLOGY_ONLY_CLAUDE)
    return _shared_bodies(files[harness.INSTRUCTION_CLAUDE])


def only_agents_topology_mapping() -> harness.RootInstructionBodies:
    files = _fixture_files(harness.TOPOLOGY_ONLY_AGENTS)
    return _shared_bodies(files[harness.INSTRUCTION_AGENTS])


def separate_topology_mapping() -> harness.RootInstructionBodies:
    files = _fixture_files(harness.TOPOLOGY_SEPARATE)
    return harness.RootInstructionBodies(
        claude=files[harness.INSTRUCTION_CLAUDE],
        agents=files[harness.INSTRUCTION_AGENTS],
    )


def claude_symlink_topology_mapping() -> harness.RootInstructionBodies:
    files = _fixture_files(harness.TOPOLOGY_CLAUDE_SYMLINK)
    return _shared_bodies(files[harness.INSTRUCTION_AGENTS])


def agents_symlink_topology_mapping() -> harness.RootInstructionBodies:
    files = _fixture_files(harness.TOPOLOGY_AGENTS_SYMLINK)
    return _shared_bodies(files[harness.INSTRUCTION_CLAUDE])


def _regular_shared_state(body: str) -> harness.MaterializedRootInstructionState:
    bodies = _shared_bodies(body)
    return harness.MaterializedRootInstructionState(
        paths=harness.RootInstructionFileStates(
            claude=harness.REGULAR_INSTRUCTION_FILE_STATE,
            agents=harness.REGULAR_INSTRUCTION_FILE_STATE,
        ),
        files=bodies,
        mapping=bodies,
    )


def claude_symlink_materialization() -> harness.MaterializedRootInstructionState:
    files = _fixture_files(harness.TOPOLOGY_CLAUDE_SYMLINK)
    return _regular_shared_state(files[harness.INSTRUCTION_AGENTS])


def agents_symlink_materialization() -> harness.MaterializedRootInstructionState:
    files = _fixture_files(harness.TOPOLOGY_AGENTS_SYMLINK)
    return _regular_shared_state(files[harness.INSTRUCTION_CLAUDE])
