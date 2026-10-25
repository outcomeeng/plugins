"""Compliance: the marketplace's test-infrastructure home is placed per the PDR.

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` places every test-infrastructure
implementation (harnesses, generators, fixtures) outside `spx/` and outside any
`tests/` directory; for Python the home is the `<package>_testing/` package at
the repository root. This verifies the locally decidable subset against the
repository's git-tracked files AND against generated violating placements, so the
check proves enforcement rather than only observing the current clean state.
`tests/` filename-shape conformance is verified separately
(`spx/15-test-language.adr.md` and the validator under `spx/15-validation.enabler/`),
not here.
"""

from __future__ import annotations

import outcomeeng
from outcomeeng.validation.infrastructure_placement import (
    TEST_INFRASTRUCTURE_PACKAGE_SUFFIX,
    misplaced_test_infrastructure,
)
from outcomeeng_testing.generators.infrastructure_placement import (
    allowed_placements,
    misplaced_placements,
)
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
    marketplace_tracked_files,
)


def _tracked_files() -> list[str]:
    return marketplace_tracked_files(marketplace_root_for_spec_tree_root_test(__file__))


class TestHomeIsPlacedAtRoot:
    """The `<package>_testing/` home is tracked at the repository root."""

    def test_home_is_tracked_at_repository_root(self) -> None:
        home = f"{outcomeeng.__name__}{TEST_INFRASTRUCTURE_PACKAGE_SUFFIX}"
        home_files = [path for path in _tracked_files() if path.startswith(f"{home}/")]
        assert home_files, (
            f"no tracked files under {home}/ — the Python "
            "test-infrastructure home is absent or not at the repository root"
        )


class TestNoMisplacedTestInfrastructure:
    """No test-infrastructure package is tracked under spx/ or within any tests/ dir."""

    def test_repository_has_no_misplaced_test_infrastructure(self) -> None:
        misplaced = misplaced_test_infrastructure(_tracked_files())
        assert misplaced == (), (
            "test-infrastructure package files must live outside spx/ and outside "
            f"any tests/ directory; misplaced tracked files: {misplaced}"
        )

    def test_rule_flags_every_package_under_spx_or_inside_a_tests_directory(
        self,
    ) -> None:
        violating = misplaced_placements()

        assert violating
        assert misplaced_test_infrastructure(violating) == violating

    def test_rule_allows_the_root_home_and_ordinary_test_files(self) -> None:
        compliant = allowed_placements()

        assert compliant
        assert misplaced_test_infrastructure(compliant) == ()
