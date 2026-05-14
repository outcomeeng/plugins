from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.spec_tree_structure import (
    NODE_KIND_ENABLER,
    SPEC_TREE_ROOT_DIRECTORY,
    is_valid_node_index,
    node_directory_name,
    node_spec_file,
)
from outcomeeng_testing.harnesses.spec_tree import (
    MARKETPLACE_ROOT_REQUIRED_DIRECTORY,
    MARKETPLACE_ROOT_SENTINEL_FILE,
    MarketplaceRootNotFoundError,
    marketplace_root_for_spec_tree_root_test,
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


def test_marketplace_root_detection_skips_consumer_pyproject_files(
    tmp_path: Path,
) -> None:
    consumer_root = tmp_path / SPEC_TREE_ROOT_DIRECTORY
    consumer_root.mkdir()
    (consumer_root / MARKETPLACE_ROOT_SENTINEL_FILE).write_text("")
    (tmp_path / MARKETPLACE_ROOT_SENTINEL_FILE).write_text("")
    (tmp_path / MARKETPLACE_ROOT_REQUIRED_DIRECTORY).mkdir(parents=True)

    assert (
        marketplace_root_for_spec_tree_root_test(
            str(consumer_root / Path(__file__).name)
        )
        == tmp_path
    )


def test_marketplace_root_detection_reports_configuration_errors(
    tmp_path: Path,
) -> None:
    consumer_root = tmp_path / SPEC_TREE_ROOT_DIRECTORY
    consumer_root.mkdir()
    test_file = consumer_root / Path(__file__).name

    with pytest.raises(MarketplaceRootNotFoundError):
        marketplace_root_for_spec_tree_root_test(str(test_file))
