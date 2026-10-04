"""Filesystem access and observations for artifact-registry node evidence."""

from __future__ import annotations

import io
import json
import os
from collections.abc import Mapping
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2, copytree, rmtree
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import cast

from outcomeeng.distribution.artifact_registry import (
    ARTIFACT_REGISTRY_PROVIDER,
    RegisteredSkill,
    RegistryField,
    artifact_registry_render_variables,
)
from outcomeeng.distribution.build import render_text
from outcomeeng.distribution.contracts import (
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng.distribution.orchestration import (
    CATALOG_PATHS,
    CLAUDE_DIST_PLUGINS_DIR,
)
from outcomeeng.distribution.shipped_scripts import load_shipped_module
from outcomeeng.validation.audit_artifacts import (
    PLUGIN_SURFACE_PATHS,
    SKILLS_DIR_NAME,
)
from outcomeeng.validation.plugins import main
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.plugin_manifest import RecordingValidationRunner

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/artifact_registry.py``.
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ManifestsStepObservation:
    """The exit status and the error output of one run of the manifests step."""

    exit_code: int
    stderr: str


def authored_registry_path() -> Path:
    """Return the authored data file the provider ships."""
    return (
        REPO_ROOT
        / SOURCE_ROOT_NAME
        / PLUGINS_DIR_NAME
        / ARTIFACT_REGISTRY_PROVIDER.relative_path
    )


def rendered_registry_document() -> Mapping[str, object]:
    """Render the provider's authored data file through the build's template pass."""
    rendered = render_text(
        authored_registry_path().read_text(encoding="utf-8"),
        variables=artifact_registry_render_variables(),
    )
    return _document(json.loads(rendered), authored_registry_path())


def shipped_registry_document(target: Target) -> Mapping[str, object]:
    """Parse the committed data file one target's tree carries beside the provider."""
    path = (
        DistTreeReader(REPO_ROOT).target_root(target)
        / ARTIFACT_REGISTRY_PROVIDER.relative_path
    )
    return _document(json.loads(path.read_text(encoding="utf-8")), path)


def load_select_artifacts_module() -> ModuleType:
    """Load the provider's shipped reader to reach its pure selection seam."""
    path = (
        DistTreeReader(REPO_ROOT).target_root(Target.CLAUDE)
        / ARTIFACT_REGISTRY_PROVIDER.script_relative_path
    )
    return load_shipped_module("select_artifacts", path)


def kind_entries(document: Mapping[str, object]) -> Mapping[str, object]:
    """Project a registry document to its kind entries keyed by kind name."""
    kinds = document[RegistryField.KINDS]
    if not isinstance(kinds, list):
        raise TypeError(f"{RegistryField.KINDS} is not a list")
    entries: dict[str, object] = {}
    for entry in kinds:
        if not isinstance(entry, dict):
            raise TypeError("a kind entry is not an object")
        typed = cast(dict[str, object], entry)
        entries[str(typed[RegistryField.NAME])] = typed
    return entries


def observe_manifests_step(
    removing: RegisteredSkill | None = None,
) -> ManifestsStepObservation:
    """Run the manifests step over a copy of the committed plugin surfaces.

    ``removing`` names one registered skill whose directory the copy of the
    Claude Code generated surface does not carry. The copy hard-links every
    committed file it can, so removing a directory never touches the repository.
    """
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        for relative in (*PLUGIN_SURFACE_PATHS, *CATALOG_PATHS.values()):
            _link_tree(REPO_ROOT / relative, root / relative)
        if removing is not None:
            claude_surface = root / CLAUDE_DIST_PLUGINS_DIR
            rmtree(claude_surface / removing.plugin / SKILLS_DIR_NAME / removing.skill)
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            exit_code = main([str(root)], runner=RecordingValidationRunner())
        return ManifestsStepObservation(exit_code, stderr.getvalue())


def _link_tree(source: Path, destination: Path) -> None:
    """Copy ``source`` to ``destination``, hard-linking files where the volume allows."""
    if source.is_dir():
        copytree(source, destination, copy_function=_link_or_copy)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    _link_or_copy(source, destination)


def _link_or_copy(source: str | Path, destination: str | Path) -> None:
    try:
        os.link(source, destination)
    except OSError:
        copy2(source, destination)


def _document(raw: object, path: Path) -> Mapping[str, object]:
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return cast(dict[str, object], raw)
