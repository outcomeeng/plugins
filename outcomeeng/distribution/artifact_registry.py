"""The registry of artifact kinds the marketplace ships.

One declaration names, for every kind, the artifacts that kind produces, the
features that detect each artifact in a changed path, and the author, audit,
and standards skills that govern it. The build renders the declaration into
one data file beside the shipped reader that owns it, so a shipped consumer
knows every artifact the marketplace ships without importing this package and
without keeping its own copy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from outcomeeng.distribution.contracts import (
    MARKDOWN_FILE_SUFFIX,
    SCRIPTS_SUBDIR_NAME,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng.validation.implementation_audit_contract import SPEC_TREE_PLUGIN_NAME

INSTRUCTIONS_PLUGIN_NAME: Final = "instructions"
PROSE_PLUGIN_NAME: Final = "prose"


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
    AUTHOR = "author"
    AUDIT = "audit"
    STANDARD = "standard"
    CONTRACT = "contract"


class ArtifactRole(StrEnum):
    """The artifacts the registered kinds produce."""

    IMPLEMENTATION = "implementation"
    TESTS = "tests"
    ARCHITECTURE = "architecture"
    ADR = "adr"
    PDR = "pdr"
    SPEC = "spec"
    SKILL = "skill"
    SUBAGENT = "subagent"
    PROSE = "prose"
    CHANGE = "change"


class AuditContract(StrEnum):
    """The output contract an artifact's audit skill follows.

    A concern skill is dispatched by the implementation audit and claims the
    paths it audits; an artifact-type skill is invoked by its own auditor and
    is accounted for by the implementation audit under the skill's name.
    """

    CONCERN = "concern"
    ARTIFACT_TYPE = "artifact-type"


# The glob segment standing for any number of directory segments; a path glob is
# matched against a changed path with ``PurePosixPath.full_match``.
GLOB_ANY_SEGMENTS: Final = "**"
MARKDOWN_EXTENSION: Final = MARKDOWN_FILE_SUFFIX.lstrip(".")
# Every test file the methodology governs sits under a node's ``tests/``
# directory below the spec tree root.
SPEC_TESTS_PATH_GLOB: Final = f"spx/{GLOB_ANY_SEGMENTS}/tests/{GLOB_ANY_SEGMENTS}"
SPEC_TREE_ROOT_GLOB: Final = f"spx/{GLOB_ANY_SEGMENTS}"
ADR_PATH_GLOB: Final = f"{SPEC_TREE_ROOT_GLOB}/*.adr.md"
PDR_PATH_GLOB: Final = f"{SPEC_TREE_ROOT_GLOB}/*.pdr.md"
SPEC_PATH_GLOB: Final = f"{SPEC_TREE_ROOT_GLOB}/*.spec.md"
SUBAGENT_PATH_GLOB: Final = f"{GLOB_ANY_SEGMENTS}/agents/*.md"
PROSE_PATH_GLOB: Final = f"docs/{GLOB_ANY_SEGMENTS}/*.md"
CHANGE_DRAFT_PATH_GLOB: Final = f"{GLOB_ANY_SEGMENTS}/change-drafts/*.md"
FOUNDATION_SKILL_NAME: Final = "understand"


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
    ``audit`` is ``None`` for an artifact no audit skill governs.
    """

    role: ArtifactRole
    detection: Detection | None
    author: str
    audit: str | None
    standard: str
    contract: AuditContract = AuditContract.ARTIFACT_TYPE

    def skill_names(self) -> tuple[str, ...]:
        """Return every skill this artifact names, in declaration order."""
        return tuple(
            name
            for name in (self.author, self.audit, self.standard)
            if name is not None
        )

    def as_json(self) -> dict[str, object]:
        return {
            RegistryField.ROLE: self.role.value,
            RegistryField.DETECTION: (
                None if self.detection is None else self.detection.as_json()
            ),
            RegistryField.AUTHOR: self.author,
            RegistryField.AUDIT: self.audit,
            RegistryField.STANDARD: self.standard,
            RegistryField.CONTRACT: self.contract.value,
        }


@dataclass(frozen=True)
class ArtifactKind:
    """One kind of artifact the marketplace ships, with the plugin that owns it."""

    name: str
    plugin: str
    artifacts: tuple[Artifact, ...]

    def as_json(self) -> dict[str, object]:
        return {
            RegistryField.NAME: self.name,
            RegistryField.PLUGIN: self.plugin,
            RegistryField.ARTIFACTS: [
                artifact.as_json() for artifact in self.artifacts
            ],
        }


@dataclass(frozen=True)
class RegisteredSkill:
    """One skill a registered artifact names, with the plugin that must ship it."""

    kind: str
    role: ArtifactRole
    plugin: str
    skill: str


def _code_kind(name: str, extension: str) -> ArtifactKind:
    """Declare the three artifacts every code kind produces."""
    return ArtifactKind(
        name=name,
        plugin=name,
        artifacts=(
            Artifact(
                role=ArtifactRole.IMPLEMENTATION,
                detection=Detection(extensions=(extension,)),
                author=f"code-{name}",
                audit=f"audit-{name}-code",
                standard=f"{name}-standards",
                contract=AuditContract.CONCERN,
            ),
            Artifact(
                role=ArtifactRole.TESTS,
                detection=Detection(
                    extensions=(extension,),
                    path_globs=(SPEC_TESTS_PATH_GLOB,),
                ),
                author=f"test-{name}",
                audit=f"audit-{name}-tests",
                standard=f"{name}-test-standards",
                contract=AuditContract.CONCERN,
            ),
            Artifact(
                role=ArtifactRole.ARCHITECTURE,
                detection=None,
                author=f"architect-{name}",
                audit=f"audit-{name}-architecture",
                standard=f"{name}-architecture-standards",
                contract=AuditContract.CONCERN,
            ),
        ),
    )


def _markdown_detection(path_glob: str) -> Detection:
    """Declare a Markdown artifact selected by where it sits."""
    return Detection(extensions=(MARKDOWN_EXTENSION,), path_globs=(path_glob,))


ARTIFACT_KINDS: Final = (
    _code_kind("python", "py"),
    _code_kind("typescript", "ts"),
    _code_kind("rust", "rs"),
    _code_kind("go", "go"),
    ArtifactKind(
        name="decisions",
        plugin=SPEC_TREE_PLUGIN_NAME,
        artifacts=(
            Artifact(
                role=ArtifactRole.ADR,
                detection=_markdown_detection(ADR_PATH_GLOB),
                author="author",
                audit="audit-adr",
                standard=FOUNDATION_SKILL_NAME,
            ),
            Artifact(
                role=ArtifactRole.PDR,
                detection=_markdown_detection(PDR_PATH_GLOB),
                author="author",
                audit="audit-pdr",
                standard=FOUNDATION_SKILL_NAME,
            ),
        ),
    ),
    ArtifactKind(
        name="specs",
        plugin=SPEC_TREE_PLUGIN_NAME,
        artifacts=(
            Artifact(
                role=ArtifactRole.SPEC,
                detection=_markdown_detection(SPEC_PATH_GLOB),
                author="author",
                audit="audit-specs",
                standard=FOUNDATION_SKILL_NAME,
            ),
        ),
    ),
    ArtifactKind(
        name="skills",
        plugin=INSTRUCTIONS_PLUGIN_NAME,
        artifacts=(
            Artifact(
                role=ArtifactRole.SKILL,
                detection=Detection(filenames=(SKILL_FILENAME,)),
                author="create-skill",
                audit="audit-skill",
                standard="skill-standards",
            ),
        ),
    ),
    ArtifactKind(
        name="subagents",
        plugin=INSTRUCTIONS_PLUGIN_NAME,
        artifacts=(
            Artifact(
                role=ArtifactRole.SUBAGENT,
                detection=_markdown_detection(SUBAGENT_PATH_GLOB),
                author="create-subagent",
                audit="audit-subagent",
                standard="subagent-standards",
            ),
        ),
    ),
    ArtifactKind(
        name="prose",
        plugin=PROSE_PLUGIN_NAME,
        artifacts=(
            Artifact(
                role=ArtifactRole.PROSE,
                detection=_markdown_detection(PROSE_PATH_GLOB),
                author="author-prose",
                audit="audit-prose",
                standard="prose-standards",
            ),
        ),
    ),
    ArtifactKind(
        name="changes",
        plugin=SPEC_TREE_PLUGIN_NAME,
        artifacts=(
            Artifact(
                role=ArtifactRole.CHANGE,
                detection=_markdown_detection(CHANGE_DRAFT_PATH_GLOB),
                author="author-change",
                audit="audit-change",
                standard="change-standards",
            ),
        ),
    ),
)


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


def registered_skills() -> tuple[RegisteredSkill, ...]:
    """Return every skill a registered artifact names, with the plugin that owns it."""
    return tuple(
        RegisteredSkill(
            kind=kind.name, role=artifact.role, plugin=kind.plugin, skill=skill
        )
        for kind in ARTIFACT_KINDS
        for artifact in kind.artifacts
        for skill in artifact.skill_names()
    )
