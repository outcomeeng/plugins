"""Compliance evidence for the manifests step over registered artifact skills."""

import pytest

from outcomeeng.distribution.artifact_registry import (
    ARTIFACT_KINDS,
    Artifact,
    ArtifactKind,
)
from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    observe_registry_skill_removal,
    registry_skill_surface_errors_on_live_surfaces,
)


@pytest.mark.parametrize(
    ("kind", "artifact"),
    [(kind, artifact) for kind in ARTIFACT_KINDS for artifact in kind.artifacts],
    ids=lambda value: value.name if isinstance(value, ArtifactKind) else value.role,
)
def test_a_registered_artifact_naming_an_unshipped_skill_is_rejected_by_name(
    kind: ArtifactKind, artifact: Artifact
) -> None:
    errors = observe_registry_skill_removal(kind, artifact)
    assert any(
        kind.name in error and artifact.role in error and artifact.audit in error
        for error in errors
    ), errors


def test_every_committed_surface_ships_every_skill_the_registry_names() -> None:
    errors = registry_skill_surface_errors_on_live_surfaces()
    assert all(surface_errors == [] for surface_errors in errors), errors
