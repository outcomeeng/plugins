"""Level 1 properties for plugin manifest validation."""

from __future__ import annotations

from outcomeeng_testing.harnesses.plugin_manifest import (
    manifest_version_parity_is_symmetric,
)


def test_manifest_version_parity_is_symmetric() -> None:
    assert manifest_version_parity_is_symmetric()
