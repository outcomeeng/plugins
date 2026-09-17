"""Select the registered artifacts a changed path names, from the rendered registry.

The artifact registry the build renders beside this script declares every
artifact kind the marketplace ships, the artifacts each kind produces, the
features that detect each artifact in a path, and the skills that govern it.
This module is the one reader of that document: sibling skills' scripts reach
it through the marketplace skill-co-located ``__file__``-relative import and
carry no reader or field vocabulary of their own.

Tested before this script is bundled by the artifact-registry node's
``test_artifact_registry.mapping.l1.py`` (every rendered consumer file equals
the declaration; one path per registered artifact selecting it and its kind's
detection-less artifacts; the most specific of two matches; every unregistered
suffix selecting nothing) and, through the implementation-audit resolver, by
the audit node's ``test_implementation_scope.compliance.l1.py``.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import PurePosixPath

ARTIFACT_REGISTRY_FILENAME = "artifact-registry.json"
ERROR_PREFIX = "error: artifact selection failed"
EXIT_COMMAND_FAILURE = 2


class RegistryField(StrEnum):
    """Fields of the rendered artifact registry."""

    KINDS = "kinds"
    NAME = "name"
    ARTIFACTS = "artifacts"
    ROLE = "role"
    DETECTION = "detection"
    EXTENSIONS = "extensions"
    PATH_GLOBS = "path_globs"
    FILENAMES = "filenames"
    AUDIT = "audit"


class SelectionField(StrEnum):
    """Fields of the per-path selection this module emits."""

    PATH = "path"
    ARTIFACTS = "artifacts"
    KIND = "kind"
    ROLE = "role"
    AUDIT = "audit"


def load_artifact_registry() -> Mapping[str, object]:
    """Read the rendered artifact registry beside this script."""
    path = pathlib.Path(__file__).resolve().parent / ARTIFACT_REGISTRY_FILENAME
    with path.open(encoding="utf-8") as handle:
        registry = json.load(handle)
    if not isinstance(registry, dict) or not isinstance(
        registry.get(RegistryField.KINDS), list
    ):
        raise ValueError(f"{path} is not a rendered artifact registry")
    return registry


def _strings(record: Mapping[str, object], field: str) -> tuple[str, ...]:
    """Return the string list ``record`` carries under ``field``, or nothing."""
    values = record.get(field)
    return tuple(str(v) for v in values) if isinstance(values, list) else ()


def _records(record: Mapping[str, object], field: str) -> list[Mapping[str, object]]:
    """Return the object list ``record`` carries under ``field``, or nothing."""
    values = record.get(field)
    return (
        [v for v in values if isinstance(v, dict)] if isinstance(values, list) else []
    )


def _detection(artifact: Mapping[str, object]) -> Mapping[str, object] | None:
    """Return the artifact's detection record, or ``None`` for a kind-selected artifact."""
    detection = artifact.get(RegistryField.DETECTION)
    return detection if isinstance(detection, dict) else None


def _detection_matches(path: str, detection: Mapping[str, object]) -> bool:
    """Return whether ``path`` carries a declared extension or filename under every glob."""
    posix = PurePosixPath(path)
    if posix.suffix.lstrip(".") not in _strings(
        detection, RegistryField.EXTENSIONS
    ) and posix.name not in _strings(detection, RegistryField.FILENAMES):
        return False
    return all(
        posix.full_match(glob) for glob in _strings(detection, RegistryField.PATH_GLOBS)
    )


def _specificity(detection: Mapping[str, object]) -> int:
    """Rank a matched detection: every path glob it carries makes it more specific."""
    return len(_strings(detection, RegistryField.PATH_GLOBS))


def select_artifacts(path: str, registry: Mapping[str, object]) -> list[dict[str, str]]:
    """Return the registered artifacts ``path`` selects, most specific first.

    Within one kind the most specific matching detection wins; a kind with a
    match then selects each of its detection-less artifacts in declaration
    order. A path matching no detection selects nothing.
    """
    selection: list[dict[str, str]] = []
    for kind in _records(registry, RegistryField.KINDS):
        artifacts = _records(kind, RegistryField.ARTIFACTS)
        matched = [
            (detection, artifact)
            for artifact in artifacts
            if (detection := _detection(artifact)) is not None
            and _detection_matches(path, detection)
        ]
        if not matched:
            continue
        winner = max(matched, key=lambda match: _specificity(match[0]))[1]
        selected = [winner, *(a for a in artifacts if _detection(a) is None)]
        selection.extend(
            {
                SelectionField.KIND: str(kind.get(RegistryField.NAME)),
                SelectionField.ROLE: str(artifact.get(RegistryField.ROLE)),
                SelectionField.AUDIT: str(artifact.get(RegistryField.AUDIT)),
            }
            for artifact in selected
        )
    return selection


def kind_by_extension(registry: Mapping[str, object]) -> dict[str, str]:
    """Map each extension a registered artifact's detection declares to its kind.

    The registry declares each extension under exactly one kind; a rendered
    registry declaring one under two kinds is malformed and is rejected rather
    than tie-broken.
    """
    mapping: dict[str, str] = {}
    for kind in _records(registry, RegistryField.KINDS):
        name = str(kind.get(RegistryField.NAME))
        for artifact in _records(kind, RegistryField.ARTIFACTS):
            detection = _detection(artifact)
            if detection is None:
                continue
            for extension in _strings(detection, RegistryField.EXTENSIONS):
                owner = mapping.setdefault(extension, name)
                if owner != name:
                    raise ValueError(
                        f"extension {extension!r} is declared under kinds "
                        f"{owner!r} and {name!r}"
                    )
    return mapping


def selection_for_paths(
    paths: Sequence[str], registry: Mapping[str, object]
) -> list[dict[str, object]]:
    """Return one selection record per path, in the supplied order."""
    return [
        {
            SelectionField.PATH: path,
            SelectionField.ARTIFACTS: select_artifacts(path, registry),
        }
        for path in paths
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths", nargs="+", help="repository-relative paths to select for"
    )
    args = parser.parse_args(argv)
    try:
        registry = load_artifact_registry()
    except (OSError, ValueError) as exc:
        print(f"{ERROR_PREFIX}: {exc}", file=sys.stderr)
        return EXIT_COMMAND_FAILURE
    print(json.dumps(selection_for_paths(args.paths, registry), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
