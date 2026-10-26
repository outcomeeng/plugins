"""Generated tracked-file placements for the test-infrastructure placement rule.

Every placement composes the source-owned Product Tree directory, tests directory,
and package suffix; the violating placements put a ``*_testing`` package file
under the Product Tree or inside a tests directory, and the compliant placements
put it at the root or put a test file in a tests directory without a package.
"""

from __future__ import annotations

from typing import Final

import outcomeeng
from outcomeeng.validation.infrastructure_placement import (
    PRODUCT_TREE_DIRECTORY,
    TEST_INFRASTRUCTURE_PACKAGE_SUFFIX,
    TESTS_DIRECTORY,
)

PACKAGES: Final = (
    f"{outcomeeng.__name__}{TEST_INFRASTRUCTURE_PACKAGE_SUFFIX}",
    f"sample{TEST_INFRASTRUCTURE_PACKAGE_SUFFIX}",
)
MODULES: Final = ("cli.py", "harnesses/cli.py", "generators/nested/paths.py")
NODE_DIRECTORIES: Final = ("55-example.enabler", "21-parent.enabler/32-child.enabler")
# Directories above a tests directory: none, one, and two levels.
PARENT_DIRECTORIES: Final = ("", "lib/", "src/plugins/")
TEST_FILE: Final = "test_example.scenario.l1.py"


def misplaced_placements() -> tuple[str, ...]:
    """Return package files under the Product Tree and inside a tests directory."""

    under_product_tree = tuple(
        f"{PRODUCT_TREE_DIRECTORY}/{node}/{package}/{module}"
        for node in NODE_DIRECTORIES
        for package in PACKAGES
        for module in MODULES
    )
    inside_tests = tuple(
        f"{parent}{TESTS_DIRECTORY}/{package}/{module}"
        for parent in PARENT_DIRECTORIES
        for package in PACKAGES
        for module in MODULES
    )
    return under_product_tree + inside_tests


def allowed_placements() -> tuple[str, ...]:
    """Return root package files and test files outside any package."""

    root_packages = tuple(
        f"{package}/{module}" for package in PACKAGES for module in MODULES
    )
    test_files = tuple(
        f"{PRODUCT_TREE_DIRECTORY}/{node}/{TESTS_DIRECTORY}/{TEST_FILE}"
        for node in NODE_DIRECTORIES
    ) + tuple(f"{parent}{TESTS_DIRECTORY}/{TEST_FILE}" for parent in PARENT_DIRECTORIES)
    return root_packages + test_files
