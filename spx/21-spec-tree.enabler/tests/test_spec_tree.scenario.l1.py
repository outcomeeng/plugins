from __future__ import annotations

from outcomeeng.spec_tree_structure import (
    NODE_KIND_ENABLER,
    is_valid_node_index,
    node_directory_name,
    node_spec_file,
)
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_tracked_spx_node_directories,
)


def test_spec_tree_enabler_directories_have_slug_spec_files() -> None:
    missing_spec_files = [
        node_directory
        for node_directory in marketplace_tracked_spx_node_directories(__file__)
        if node_directory_name(node_directory).kind == NODE_KIND_ENABLER
        and not node_spec_file(node_directory).is_file()
    ]

    assert not missing_spec_files


def test_spec_tree_node_prefixes_are_valid_indices() -> None:
    invalid_node_directories = [
        node_directory
        for node_directory in marketplace_tracked_spx_node_directories(__file__)
        if not is_valid_node_index(node_directory_name(node_directory).index)
    ]

    assert not invalid_node_directories
