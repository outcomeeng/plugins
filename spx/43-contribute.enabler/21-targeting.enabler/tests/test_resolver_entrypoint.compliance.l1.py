"""Level-1 compliance evidence that an absent provider fails loudly at load."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    consumer_entrypoints,
    observe_entrypoint_without_provider,
)

ENTRYPOINTS = consumer_entrypoints()


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS, ids=lambda p: p.parent.parent.name)
def test_a_missing_provider_raises_and_names_the_path(entrypoint: Path) -> None:
    """The whole point of the import: a moved provider raises here, not later.

    A grant that walked into the provider's directory would instead stop matching
    and degrade to a permission prompt, which is silent. This proves the failure
    is an exception naming the path it looked for.
    """
    observation = observe_entrypoint_without_provider(entrypoint)

    assert observation.resolver_file is None
    assert observation.error is not None
    assert "resolve_target.py" in observation.error
