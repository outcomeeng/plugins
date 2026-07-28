"""Compliance: the marketplace's test-infrastructure home is placed per the PDR.

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` places every test-infrastructure
implementation (harnesses, generators, fixtures) outside `spx/` and outside any
`tests/` directory; for Python the home is the `<package>_testing/` package at
the repository root. This verifies the locally decidable subset against the
repository's git-tracked files AND against synthetic violating placements, so the
check proves enforcement rather than only observing the current clean state.
`tests/` filename-shape conformance is verified separately
(`spx/15-test-language.adr.md` and the validator under `spx/15-validation.enabler/`),
not here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import outcomeeng
from outcomeeng_testing.harnesses.spec_tree import marketplace_tracked_files

REPO_ROOT: Final = Path(__file__).resolve().parents[4]

# The PDR places the Python test-infrastructure home at `<package>_testing/`,
# where `<package>` is the product's importable package. Derive it from the
# package itself so the home tracks a rename rather than a copied literal.
TEST_INFRA_HOME: Final = f"{outcomeeng.__name__}_testing"

# A path segment named `<something>_testing` marks a test-infrastructure package.
_PACKAGE_SEGMENT: Final = "_testing/"


def _misplaced_test_infra(tracked: list[str]) -> list[str]:
    """Tracked test-infrastructure package files that violate the placement rule.

    A file is misplaced when it sits inside a `*_testing/` package AND lives under
    `spx/` or within any `tests/` directory.
    """
    return [
        path
        for path in tracked
        if _PACKAGE_SEGMENT in path
        and (path.startswith("spx/") or path.startswith("tests/") or "/tests/" in path)
    ]


def _tracked_files() -> list[str]:
    return marketplace_tracked_files(REPO_ROOT)


class TestHomeIsPlacedAtRoot:
    """The `<package>_testing/` home is tracked at the repository root."""

    def test_home_is_tracked_at_repository_root(self) -> None:
        home_files = [
            path for path in _tracked_files() if path.startswith(f"{TEST_INFRA_HOME}/")
        ]
        assert home_files, (
            f"no tracked files under {TEST_INFRA_HOME}/ — the Python "
            "test-infrastructure home is absent or not at the repository root"
        )


class TestNoMisplacedTestInfrastructure:
    """No test-infrastructure package is tracked under spx/ or within any tests/ dir."""

    def test_repository_has_no_misplaced_test_infrastructure(self) -> None:
        misplaced = _misplaced_test_infra(_tracked_files())
        assert not misplaced, (
            "test-infrastructure package files must live outside spx/ and outside "
            f"any tests/ directory; misplaced tracked files: {misplaced}"
        )

    def test_rule_flags_a_package_under_spx(self) -> None:
        violating = [f"spx/55-example.enabler/{TEST_INFRA_HOME}/harnesses/cli.py"]
        assert _misplaced_test_infra(violating) == violating

    def test_rule_flags_a_package_inside_a_tests_directory(self) -> None:
        violating = ["spx/55-example.enabler/tests/sample_testing/fixtures.py"]
        assert _misplaced_test_infra(violating) == violating

    def test_rule_allows_the_root_home_and_ordinary_test_files(self) -> None:
        compliant = [
            f"{TEST_INFRA_HOME}/harnesses/cli.py",
            "spx/55-example.enabler/tests/test_x.scenario.l1.py",
        ]
        assert _misplaced_test_infra(compliant) == []
