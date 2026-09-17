"""Generated cases over the artifact registry's declared detections."""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.distribution.artifact_registry import (
    ARTIFACT_KINDS,
    GLOB_ANY_SEGMENTS,
    Artifact,
    ArtifactKind,
    registry_extensions,
)
from outcomeeng.distribution.contracts import TEXT_FILE_SUFFIXES

# Segment names the construction substitutes for glob wildcards. They are
# incidental: any segment satisfies ``**`` and any stem satisfies ``*``.
_WILDCARD_SEGMENT = "node"
_SUBJECT_STEM = "subject"


@dataclass(frozen=True)
class DetectedArtifact:
    """One registered artifact that carries a detection, with its owning kind."""

    kind: ArtifactKind
    artifact: Artifact

    @property
    def case_id(self) -> str:
        return f"{self.kind.name}-{self.artifact.role}"


def detected_artifacts() -> tuple[DetectedArtifact, ...]:
    """Return every registered artifact a path can select through its detection."""
    return tuple(
        DetectedArtifact(kind=kind, artifact=artifact)
        for kind in ARTIFACT_KINDS
        for artifact in kind.artifacts
        if artifact.detection is not None
    )


def path_matching(detected: DetectedArtifact) -> str:
    """Construct one path from the artifact's own detection record.

    The construction law is the detection grammar the registry declares: the
    first extension under the first path glob, with ``**`` standing for one
    directory segment and the final wildcard standing for the file itself; a
    detection without a path glob yields a bare file.
    """
    detection = detected.artifact.detection
    if detection is None:
        raise ValueError(f"{detected.case_id} carries no detection")
    filename = f"{_SUBJECT_STEM}.{detection.extensions[0]}"
    if not detection.path_globs:
        return filename
    segments = detection.path_globs[0].split("/")
    directories = [
        _WILDCARD_SEGMENT if segment == GLOB_ANY_SEGMENTS else segment
        for segment in segments[:-1]
    ]
    return "/".join([*directories, filename])


def unregistered_path() -> str:
    """Return one path whose extension no registered artifact declares."""
    unregistered = sorted(
        TEXT_FILE_SUFFIXES - {f".{ext}" for ext in registry_extensions()}
    )
    return f"{_SUBJECT_STEM}{unregistered[0]}"


def two_match_cases() -> tuple[DetectedArtifact, ...]:
    """Return every detected artifact whose path a sibling of its kind also matches.

    A sibling matches by extension alone; the case artifact adds a path glob, so
    its own path matches both and the precedence rule decides between them.
    """
    return tuple(
        detected
        for detected in detected_artifacts()
        if detected.artifact.detection is not None
        and detected.artifact.detection.path_globs
        and any(
            sibling.detection is not None
            and not sibling.detection.path_globs
            and set(sibling.detection.extensions)
            & set(detected.artifact.detection.extensions)
            for sibling in detected.kind.artifacts
            if sibling is not detected.artifact
        )
    )


@dataclass(frozen=True)
class RegisteredSkill:
    """One skill a registered artifact names, with its owning kind and artifact."""

    kind: ArtifactKind
    artifact: Artifact
    skill: str

    @property
    def case_id(self) -> str:
        return f"{self.kind.name}-{self.artifact.role}-{self.skill}"


def registered_skills() -> tuple[RegisteredSkill, ...]:
    """Return every skill every registered artifact names — the complete finite domain."""
    return tuple(
        RegisteredSkill(kind=kind, artifact=artifact, skill=skill)
        for kind in ARTIFACT_KINDS
        for artifact in kind.artifacts
        for skill in artifact.skill_names()
    )
