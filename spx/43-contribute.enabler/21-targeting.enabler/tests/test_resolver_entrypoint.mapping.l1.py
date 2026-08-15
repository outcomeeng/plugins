"""Level-1 mapping evidence that every consuming entrypoint reaches the resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    SCRIPT,
    consumer_entrypoints,
    observe_entrypoint,
)

ENTRYPOINTS = consumer_entrypoints()


def test_the_plugin_declares_target_resolving_skills() -> None:
    """An empty domain would make every case below vacuously true."""
    assert ENTRYPOINTS, f"no skill grants an entrypoint beside {SCRIPT}"


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS, ids=lambda p: p.parent.parent.name)
def test_each_target_resolving_skill_carries_its_entrypoint(entrypoint: Path) -> None:
    """The skill granted this path; a grant naming nothing is the failure here."""
    assert entrypoint.is_file(), (
        f"{entrypoint.parent.parent.name} grants {entrypoint.name} but ships none"
    )


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS, ids=lambda p: p.parent.parent.name)
def test_each_entrypoint_loads_the_one_shared_resolver(entrypoint: Path) -> None:
    observation = observe_entrypoint(entrypoint)

    assert observation.error is None, observation.error
    assert observation.resolver_file == SCRIPT
