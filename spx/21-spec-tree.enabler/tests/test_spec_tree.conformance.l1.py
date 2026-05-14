from __future__ import annotations

from outcomeeng.spec_tree_structure import node_spec_file
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_tracked_spx_node_directories,
)


def test_every_spec_tree_node_directory_has_its_slug_spec_file() -> None:
    missing_spec_files = [
        node_directory
        for node_directory in marketplace_tracked_spx_node_directories(__file__)
        if not node_spec_file(node_directory).is_file()
    ]

    assert not missing_spec_files
