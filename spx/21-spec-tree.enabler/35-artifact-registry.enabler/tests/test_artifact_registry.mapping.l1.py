"""Mapping evidence for the artifact registry's render and per-path selection."""

import pytest

from outcomeeng.distribution.artifact_registry import (
    ARTIFACT_KINDS,
    ArtifactKind,
    artifact_registry_document,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.generators.artifact_registry import (
    DetectedArtifact,
    detected_artifacts,
    path_matching,
    two_match_cases,
    unregistered_paths,
)
from outcomeeng_testing.harnesses.artifact_registry import (
    kind_entries,
    load_select_artifacts_module,
    rendered_registry_document,
    shipped_registry_document,
)

PROVIDER = load_select_artifacts_module()
FIELD = PROVIDER.SelectionField


def _selected(path: str) -> list[tuple[str, str, str]]:
    """Project the provider's selection for one path to (kind, role, audit) tuples."""
    return [
        (entry[FIELD.KIND], entry[FIELD.ROLE], entry[FIELD.AUDIT])
        for entry in PROVIDER.select_artifacts(path, artifact_registry_document())
    ]


@pytest.mark.parametrize("kind", ARTIFACT_KINDS, ids=lambda k: k.name)
def test_each_kind_renders_into_the_provider_data_file(kind: ArtifactKind) -> None:
    assert kind_entries(rendered_registry_document())[kind.name] == kind.as_json()


@pytest.mark.parametrize("target", tuple(Target), ids=lambda t: t.value)
def test_each_shipped_data_file_equals_a_fresh_render(target: Target) -> None:
    assert shipped_registry_document(target) == rendered_registry_document()


@pytest.mark.parametrize("detected", detected_artifacts(), ids=lambda d: d.case_id)
def test_a_path_matching_a_detection_selects_that_artifact_and_its_kind_artifacts(
    detected: DetectedArtifact,
) -> None:
    kind, artifact = detected.kind, detected.artifact
    expected = [
        (kind.name, artifact.role, artifact.audit),
        *(
            (kind.name, sibling.role, sibling.audit)
            for sibling in kind.artifacts
            if sibling.detection is None
        ),
    ]
    assert _selected(path_matching(detected)) == expected


@pytest.mark.parametrize("case", two_match_cases(), ids=lambda c: c.case_id)
def test_a_path_matching_two_artifacts_of_one_kind_selects_the_most_specific(
    case: DetectedArtifact,
) -> None:
    detected_roles = [
        role
        for kind, role, _audit in _selected(path_matching(case))
        if kind == case.kind.name
        and next(a for a in case.kind.artifacts if a.role == role).detection is not None
    ]
    assert detected_roles == [case.artifact.role]


@pytest.mark.parametrize("path", unregistered_paths())
def test_a_path_matching_no_registered_artifact_selects_nothing(path: str) -> None:
    assert _selected(path) == []
