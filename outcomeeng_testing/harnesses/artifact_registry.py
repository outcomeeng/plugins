"""Filesystem access for artifact-registry node evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import cast

from outcomeeng.distribution.artifact_registry import (
    ARTIFACT_REGISTRY_PROVIDER,
    RegistryField,
    artifact_registry_render_variables,
)
from outcomeeng.distribution.build import render_text
from outcomeeng.distribution.shipped_scripts import load_shipped_module
from outcomeeng.distribution.contracts import (
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/artifact_registry.py``.
REPO_ROOT = Path(__file__).resolve().parents[2]


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


def _document(raw: object, path: Path) -> Mapping[str, object]:
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return cast(dict[str, object], raw)
