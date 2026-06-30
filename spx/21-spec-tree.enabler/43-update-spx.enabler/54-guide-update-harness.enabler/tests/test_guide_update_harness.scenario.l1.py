"""Scenario evidence for root guide topology materialization."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.update_spx import (
    GUIDE_AGENTS,
    GUIDE_CLAUDE,
    ROOT_GUIDE_SHARED_BODY,
    materialize_root_guide_topology,
    root_guide_topology_symlinked,
)


def test_symlinked_harness_guides_materialize_as_regular_files(
    tmp_path: pathlib.Path,
) -> None:
    topology = root_guide_topology_symlinked()
    materialized = materialize_root_guide_topology(tmp_path, topology)

    claude_path = tmp_path / GUIDE_CLAUDE
    agents_path = tmp_path / GUIDE_AGENTS

    assert claude_path.is_file()
    assert agents_path.is_file()
    assert not claude_path.is_symlink()
    assert not agents_path.is_symlink()
    assert claude_path.read_text(encoding="utf-8") == ROOT_GUIDE_SHARED_BODY
    assert agents_path.read_text(encoding="utf-8") == ROOT_GUIDE_SHARED_BODY
    assert materialized[GUIDE_CLAUDE] == ROOT_GUIDE_SHARED_BODY
    assert materialized[GUIDE_AGENTS] == ROOT_GUIDE_SHARED_BODY
