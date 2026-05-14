"""Harnesses for marketplace Spec Tree structure tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

from outcomeeng.spec_tree_structure import (
    SPEC_TREE_ROOT_DIRECTORY,
    iter_node_directories_from_tracked_paths,
)

MARKETPLACE_ROOT_SENTINEL_FILE = "pyproject.toml"
MARKETPLACE_ROOT_REQUIRED_DIRECTORY = Path("plugins/spec-tree")


def marketplace_root_for_spec_tree_root_test(test_file: str) -> Path:
    for candidate in Path(test_file).resolve().parents:
        if (candidate / MARKETPLACE_ROOT_SENTINEL_FILE).is_file() and (
            candidate / MARKETPLACE_ROOT_REQUIRED_DIRECTORY
        ).is_dir():
            return candidate

    msg = (
        f"Unable to locate marketplace root from {test_file}; expected "
        f"{MARKETPLACE_ROOT_SENTINEL_FILE} and {MARKETPLACE_ROOT_REQUIRED_DIRECTORY}"
    )
    raise FileNotFoundError(msg)


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
