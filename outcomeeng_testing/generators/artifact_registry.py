"""Generated cases over the artifact registry's declared detections."""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.distribution.artifact_registry import (
    ARTIFACT_KINDS,
    GLOB_ANY_SEGMENTS,
    Artifact,
    ArtifactKind,
)
from outcomeeng.distribution.contracts import TEXT_FILE_SUFFIXES

# Segment names the construction substitutes for glob wildcards. They are
# incidental: any segment satisfies ``**`` and any stem satisfies ``*``.
_WILDCARD_SEGMENT = "node"
_SUBJECT_STEM = "subject"
_STEM_WILDCARD = "*"


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
    file is named from the first declared extension, or from the first declared
    filename when the detection declares no extension; under the first path
    glob, ``**`` stands for one directory segment, a final ``**`` stands for
    that file, and a final segment carrying ``*`` takes the subject stem in
    its place; a detection without a path glob yields a bare file.
    """
    detection = detected.artifact.detection
    if detection is None:
        raise ValueError(f"{detected.case_id} carries no detection")
    filename = (
        f"{_SUBJECT_STEM}.{detection.extensions[0]}"
        if detection.extensions
        else detection.filenames[0]
    )
    if not detection.path_globs:
        return filename
    segments = detection.path_globs[0].split("/")
    directories = [
        _WILDCARD_SEGMENT if segment == GLOB_ANY_SEGMENTS else segment
        for segment in segments[:-1]
    ]
    final = segments[-1]
    name = (
        filename
        if final == GLOB_ANY_SEGMENTS
        else final.replace(_STEM_WILDCARD, _SUBJECT_STEM)
    )
    return "/".join([*directories, name])


def registered_extensions() -> frozenset[str]:
    """Return every file extension a registered artifact's detection declares."""
    return frozenset(
        extension
        for kind in ARTIFACT_KINDS
        for artifact in kind.artifacts
        if artifact.detection is not None
        for extension in artifact.detection.extensions
    )


def unregistered_suffixes() -> tuple[str, ...]:
    """Return every text suffix the build distributes that no registered artifact declares.

    The domain is the complete finite complement, sorted: every text-file suffix
    the build distributes minus every extension the registry declares.
    """
    return tuple(
        sorted(TEXT_FILE_SUFFIXES - {f".{ext}" for ext in registered_extensions()})
    )


def pattern_bound_extensions() -> frozenset[str]:
    """Return every registered extension no extension-only detection declares.

    A bare file of such an extension sits under none of the path patterns that
    select its artifacts, so it selects nothing although the extension is
    registered.
    """
    extension_only = frozenset(
        extension
        for kind in ARTIFACT_KINDS
        for artifact in kind.artifacts
        if artifact.detection is not None and not artifact.detection.path_globs
        for extension in artifact.detection.extensions
    )
    return registered_extensions() - extension_only


def unregistered_paths() -> tuple[str, ...]:
    """Return one path per unregistered suffix, and one bare file per pattern-bound extension."""
    return (
        *(f"{_SUBJECT_STEM}{suffix}" for suffix in unregistered_suffixes()),
        *(f"{_SUBJECT_STEM}.{ext}" for ext in sorted(pattern_bound_extensions())),
    )


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
