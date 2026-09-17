"""The registry of artifact kinds the marketplace ships.

One declaration names, for every kind, the artifacts that kind produces, the
features that detect each artifact in a changed path, and the architect,
author, and audit skills and the shared standard that govern it. The build
renders the declaration into one data file beside the shipped reader that
owns it, so a shipped consumer knows every artifact the marketplace ships
without importing this package and without keeping its own copy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from outcomeeng.distribution.contracts import SCRIPTS_SUBDIR_NAME, SKILLS_SUBDIR_NAME
from outcomeeng.validation.implementation_audit_contract import SPEC_TREE_PLUGIN_NAME


class RegistryField(StrEnum):
    """Field names of the rendered registry document."""

    KINDS = "kinds"
    NAME = "name"
    PLUGIN = "plugin"
    ARTIFACTS = "artifacts"
    ROLE = "role"
    DETECTION = "detection"
    EXTENSIONS = "extensions"
    PATH_GLOBS = "path_globs"
    FILENAMES = "filenames"
    ARCHITECT = "architect"
    AUTHOR = "author"
    AUDIT = "audit"
    STANDARD = "standard"


class ArtifactRole(StrEnum):
    """The artifacts a code kind produces."""

    IMPLEMENTATION = "implementation"
    TESTS = "tests"
    ARCHITECTURE = "architecture"


# The glob segment standing for any number of directory segments; a path glob is
# matched against a changed path with ``PurePosixPath.full_match``.
GLOB_ANY_SEGMENTS: Final = "**"
# Every test file the methodology governs sits under a node's ``tests/``
# directory below the spec tree root.
SPEC_TESTS_PATH_GLOB: Final = f"spx/{GLOB_ANY_SEGMENTS}/tests/{GLOB_ANY_SEGMENTS}"


@dataclass(frozen=True)
class Detection:
    """The features that select an artifact from a changed path.

    A path matches when its extension or filename is declared and every path
    glob, if any, matches. A detection carrying a path glob is more specific
    than one carrying extensions or filenames alone.
    """

    extensions: tuple[str, ...] = ()
    path_globs: tuple[str, ...] = ()
    filenames: tuple[str, ...] = ()

    def as_json(self) -> dict[str, object]:
        return {
            RegistryField.EXTENSIONS: list(self.extensions),
            RegistryField.PATH_GLOBS: list(self.path_globs),
            RegistryField.FILENAMES: list(self.filenames),
        }


@dataclass(frozen=True)
class Artifact:
    """One artifact a kind produces and the skills that govern it.

    ``detection`` is ``None`` for an artifact selected through its kind: it is
    selected whenever the same changeset selects another artifact of the kind.
    """

    role: ArtifactRole
    detection: Detection | None
    architect: str | None
    author: str | None
    audit: str
    standard: str

    def skill_names(self) -> tuple[str, ...]:
        """Return every skill this artifact names, in declaration order."""
        return tuple(
            name
            for name in (self.architect, self.author, self.audit, self.standard)
            if name is not None
        )

    def as_json(self) -> dict[str, object]:
        return {
            RegistryField.ROLE: self.role.value,
            RegistryField.DETECTION: (
                None if self.detection is None else self.detection.as_json()
            ),
            RegistryField.ARCHITECT: self.architect,
            RegistryField.AUTHOR: self.author,
            RegistryField.AUDIT: self.audit,
            RegistryField.STANDARD: self.standard,
        }


@dataclass(frozen=True)
class ArtifactKind:
    """One kind of artifact the marketplace ships, with the plugin that owns it."""

    name: str
    plugin: str
    artifacts: tuple[Artifact, ...]

    def skill_names(self) -> tuple[str, ...]:
        """Return every distinct skill the kind's artifacts name, in declaration order."""
        return tuple(
            dict.fromkeys(
                name for artifact in self.artifacts for name in artifact.skill_names()
            )
        )

    def as_json(self) -> dict[str, object]:
        return {
            RegistryField.NAME: self.name,
            RegistryField.PLUGIN: self.plugin,
            RegistryField.ARTIFACTS: [
                artifact.as_json() for artifact in self.artifacts
            ],
        }


def _code_kind(name: str, extension: str) -> ArtifactKind:
    """Declare the three artifacts every code kind produces."""
    return ArtifactKind(
        name=name,
        plugin=name,
        artifacts=(
            Artifact(
                role=ArtifactRole.IMPLEMENTATION,
                detection=Detection(extensions=(extension,)),
                architect=f"architect-{name}",
                author=f"code-{name}",
                audit=f"audit-{name}-code",
                standard=f"{name}-standards",
            ),
            Artifact(
                role=ArtifactRole.TESTS,
                detection=Detection(
                    extensions=(extension,),
                    path_globs=(SPEC_TESTS_PATH_GLOB,),
                ),
                architect=None,
                author=f"test-{name}",
                audit=f"audit-{name}-tests",
                standard=f"{name}-test-standards",
            ),
            Artifact(
                role=ArtifactRole.ARCHITECTURE,
                detection=None,
                architect=f"architect-{name}",
                author=None,
                audit=f"audit-{name}-architecture",
                standard=f"{name}-architecture-standards",
            ),
        ),
    )


ARTIFACT_KINDS: Final = (
    _code_kind("python", "py"),
    _code_kind("typescript", "ts"),
    _code_kind("rust", "rs"),
    _code_kind("go", "go"),
)


def _extension_owners(kinds: tuple[ArtifactKind, ...]) -> dict[str, str]:
    """Map each declared extension to the one kind declaring it.

    An extension declared under two kinds is a malformed declaration: every
    reader of the registry resolves an extension to exactly one kind, so the
    declaration is rejected at construction rather than tie-broken by a reader.
    """
    owners: dict[str, str] = {}
    for kind in kinds:
        for artifact in kind.artifacts:
            if artifact.detection is None:
                continue
            for extension in artifact.detection.extensions:
                owner = owners.setdefault(extension, kind.name)
                if owner != kind.name:
                    raise ValueError(
                        f"extension {extension!r} is declared under kinds "
                        f"{owner!r} and {kind.name!r}"
                    )
    return owners


# Extension -> owning kind name; constructing it enforces that each declared
# extension belongs to exactly one kind.
EXTENSION_OWNERS: Final = _extension_owners(ARTIFACT_KINDS)


ARTIFACT_REGISTRY_FILENAME: Final = "artifact-registry.json"
ARTIFACT_REGISTRY_VARIABLE: Final = "artifact_registry_json"
SELECT_ARTIFACTS_SCRIPT_FILENAME: Final = "select_artifacts.py"


@dataclass(frozen=True)
class ArtifactRegistryProvider:
    """The shipped skill whose script owns the rendered registry and its reader.

    The build renders the one data file beside this reader; sibling skills'
    scripts reach the reader by import and carry no copy of the document or
    its vocabulary.
    """

    plugin: str
    skill: str

    @property
    def scripts_path(self) -> Path:
        """Return the skill's scripts directory relative to a plugin surface root."""
        return Path(self.plugin) / SKILLS_SUBDIR_NAME / self.skill / SCRIPTS_SUBDIR_NAME

    @property
    def relative_path(self) -> Path:
        """Return the data file's path relative to a plugin surface root."""
        return self.scripts_path / ARTIFACT_REGISTRY_FILENAME

    @property
    def script_relative_path(self) -> Path:
        """Return the reader script's path relative to a plugin surface root."""
        return self.scripts_path / SELECT_ARTIFACTS_SCRIPT_FILENAME


ARTIFACT_REGISTRY_PROVIDER: Final = ArtifactRegistryProvider(
    plugin=SPEC_TREE_PLUGIN_NAME, skill="select-artifacts"
)


def artifact_registry_document() -> dict[str, object]:
    """Return the registry as the document the build renders."""
    return {RegistryField.KINDS: [kind.as_json() for kind in ARTIFACT_KINDS]}


def artifact_registry_render_variables() -> dict[str, object]:
    """Return the build variable carrying the rendered registry document."""
    return {
        ARTIFACT_REGISTRY_VARIABLE: json.dumps(
            artifact_registry_document(), indent=2, sort_keys=False
        )
    }


def registry_extensions() -> frozenset[str]:
    """Return every file extension a registered artifact's detection declares."""
    return frozenset(EXTENSION_OWNERS)


def kind_by_extension() -> dict[str, str]:
    """Return each declared extension mapped to the name of the kind declaring it."""
    return dict(EXTENSION_OWNERS)


def kinds_with_role(role: ArtifactRole) -> tuple[ArtifactKind, ...]:
    """Return every kind producing an artifact of ``role``, in declaration order."""
    return tuple(
        kind
        for kind in ARTIFACT_KINDS
        if any(artifact.role is role for artifact in kind.artifacts)
    )
