"""Compliance evidence for the manifests step over registered artifact skills."""

import pytest

from outcomeeng.distribution.artifact_registry import RegisteredSkill, registered_skills
from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    observe_registry_skill_removal,
    registry_skill_surface_errors_on_live_surfaces,
)


@pytest.mark.parametrize(
    "registered",
    registered_skills(),
    ids=lambda r: f"{r.kind}-{r.role}-{r.skill}",
)
def test_a_registered_artifact_naming_an_unshipped_skill_is_rejected_by_name(
    registered: RegisteredSkill,
) -> None:
    errors = observe_registry_skill_removal(registered.kind, registered.skill)
    assert any(
        registered.kind in error
        and registered.role.value in error
        and registered.skill in error
        for error in errors
    ), errors


def test_every_committed_surface_ships_every_skill_the_registry_names() -> None:
    errors = registry_skill_surface_errors_on_live_surfaces()
    assert all(surface_errors == [] for surface_errors in errors), errors
