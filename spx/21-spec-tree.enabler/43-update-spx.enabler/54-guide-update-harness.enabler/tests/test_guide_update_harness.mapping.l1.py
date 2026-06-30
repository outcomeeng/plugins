"""Mapping evidence for root guide topology seed resolution."""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.update_spx import (
    GUIDE_AGENTS,
    GUIDE_CLAUDE,
    ROOT_GUIDE_AGENTS_BODY,
    ROOT_GUIDE_CLAUDE_BODY,
    ROOT_GUIDE_SHARED_BODY,
    RootGuideTopology,
    materialize_root_guide_topology,
    root_guide_topology_only_agents,
    root_guide_topology_only_claude,
    root_guide_topology_separate,
    root_guide_topology_symlinked,
)


@pytest.mark.parametrize(
    ("topology", "expected"),
    [
        (
            root_guide_topology_only_claude(),
            {
                GUIDE_CLAUDE: ROOT_GUIDE_CLAUDE_BODY,
                GUIDE_AGENTS: ROOT_GUIDE_CLAUDE_BODY,
            },
        ),
        (
            root_guide_topology_only_agents(),
            {
                GUIDE_CLAUDE: ROOT_GUIDE_AGENTS_BODY,
                GUIDE_AGENTS: ROOT_GUIDE_AGENTS_BODY,
            },
        ),
        (
            root_guide_topology_separate(),
            {
                GUIDE_CLAUDE: ROOT_GUIDE_CLAUDE_BODY,
                GUIDE_AGENTS: ROOT_GUIDE_AGENTS_BODY,
            },
        ),
        (
            root_guide_topology_symlinked(),
            {
                GUIDE_CLAUDE: ROOT_GUIDE_SHARED_BODY,
                GUIDE_AGENTS: ROOT_GUIDE_SHARED_BODY,
            },
        ),
    ],
)
def test_root_guide_topology_maps_to_runtime_seed_bodies(
    tmp_path: pathlib.Path,
    topology: RootGuideTopology,
    expected: dict[str, str],
) -> None:
    assert materialize_root_guide_topology(tmp_path, topology) == expected
