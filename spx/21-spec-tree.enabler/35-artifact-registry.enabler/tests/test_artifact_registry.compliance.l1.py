"""Compliance evidence for the manifests step over registered artifact skills."""

import pytest

from outcomeeng.distribution.artifact_registry import RegisteredSkill, registered_skills
from outcomeeng.validation.plugins import (
    ARTIFACT_REGISTRY_ERROR_LABEL,
    contract_error_line,
)
from outcomeeng_testing.harnesses.artifact_registry import observe_manifests_step


@pytest.mark.parametrize(
    "registered",
    registered_skills(),
    ids=lambda r: f"{r.kind}-{r.role}-{r.skill}",
)
def test_a_registered_artifact_naming_an_unshipped_skill_is_rejected_by_name(
    registered: RegisteredSkill,
) -> None:
    observed = observe_manifests_step(removing=registered)
    registry_prefix = contract_error_line(ARTIFACT_REGISTRY_ERROR_LABEL, "")
    registry_lines = [
        line
        for line in observed.stderr.splitlines()
        if line.startswith(registry_prefix)
    ]
    assert observed.exit_code != 0, observed.stderr
    assert any(
        registered.kind in line
        and registered.role.value in line
        and registered.skill in line
        for line in registry_lines
    ), observed.stderr


def test_every_committed_surface_ships_every_skill_the_registry_names() -> None:
    observed = observe_manifests_step()
    assert observed.exit_code == 0, observed.stderr
