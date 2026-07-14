"""Property evidence for build determinism and idempotence."""

from __future__ import annotations

import pytest

from outcomeeng.distribution.build import IMPLEMENTED
from outcomeeng_testing.harnesses.plugin_build import (
    canonical_build_is_deterministic,
    canonical_build_is_idempotent,
)


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


def test_same_source_produces_byte_identical_outputs() -> None:
    assert canonical_build_is_deterministic()


def test_running_build_twice_produces_no_second_pass_change() -> None:
    assert canonical_build_is_idempotent()
