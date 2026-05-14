"""Harnesses for marketplace Spec Tree structure tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

from outcomeeng.spec_tree_structure import (
    SPEC_TREE_ROOT_DIRECTORY,
    iter_node_directories_from_tracked_paths,
)

SPEC_TREE_ROOT_TEST_FILE_TO_MARKETPLACE_ROOT_DEPTH = 3


def marketplace_root_for_spec_tree_root_test(test_file: str) -> Path:
    return (
        Path(test_file)
        .resolve()
        .parents[SPEC_TREE_ROOT_TEST_FILE_TO_MARKETPLACE_ROOT_DEPTH]
    )


def marketplace_spx_root_for_spec_tree_root_test(test_file: str) -> Path:
    return (
        marketplace_root_for_spec_tree_root_test(test_file) / SPEC_TREE_ROOT_DIRECTORY
    )


def marketplace_tracked_spx_node_directories(test_file: str) -> list[Path]:
    product_root = marketplace_root_for_spec_tree_root_test(test_file)
    result = subprocess.run(
        ["git", "ls-files", SPEC_TREE_ROOT_DIRECTORY],
        cwd=product_root,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked_paths = [product_root / line for line in result.stdout.splitlines() if line]
    return list(iter_node_directories_from_tracked_paths(product_root, tracked_paths))
