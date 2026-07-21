"""Validate the spec-tree foundation-resource manifest in every generated tree.

The spec-tree plugin identifies its methodology resource surface through
``skills/understand/manifest.json``: an integer ``schema_version``, exactly one
package-relative core entry naming the consolidated foundation document, and
the references, templates, and examples catalogs as ordered arrays of
package-relative paths. This validator parses each shipped manifest, rejects
shapes outside that contract, requires every declared path to resolve to a
file, forbids duplicate paths, and requires every file under the understand
skill's catalog directories to be declared — so the manifest and the shipped
resource set never drift.

Usage::

    python3 -m outcomeeng.validation.foundation_manifest [ROOT ...]

Each ROOT is a repository root whose ``dist/{claude,codex}`` trees carry the
spec-tree plugin; the current directory is the default.

Exit codes:
    0 - every checked manifest satisfies the contract
    1 - one or more manifests violate the contract
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    Target,
)

SPEC_TREE_PLUGIN_NAME: Final = "spec-tree"
UNDERSTAND_SKILL_NAME: Final = "understand"
UNDERSTAND_SKILL_RELATIVE_DIR: Final = f"{SKILLS_SUBDIR_NAME}/{UNDERSTAND_SKILL_NAME}"
MANIFEST_FILENAME: Final = "manifest.json"
MANIFEST_RELATIVE_PATH: Final = f"{UNDERSTAND_SKILL_RELATIVE_DIR}/{MANIFEST_FILENAME}"
CORE_DOCUMENT_RELATIVE_PATH: Final = f"{UNDERSTAND_SKILL_RELATIVE_DIR}/{SKILL_FILENAME}"

SCHEMA_VERSION_FIELD: Final = "schema_version"
CORE_FIELD: Final = "core"
REFERENCES_FIELD: Final = "references"
TEMPLATES_FIELD: Final = "templates"
EXAMPLES_FIELD: Final = "examples"
CATALOG_FIELDS: Final = (REFERENCES_FIELD, TEMPLATES_FIELD, EXAMPLES_FIELD)
MANIFEST_FIELDS: Final = (SCHEMA_VERSION_FIELD, CORE_FIELD, *CATALOG_FIELDS)
SUPPORTED_SCHEMA_VERSION: Final = 1

# Catalog field -> plugin-relative directory whose files that catalog declares.
# The directories are named for their fields, so the mapping is derived, not
# a second spelling of the vocabulary.
CATALOG_DIRECTORIES: Final[dict[str, str]] = {
    field: f"{UNDERSTAND_SKILL_RELATIVE_DIR}/{field}" for field in CATALOG_FIELDS
}


@dataclass(frozen=True)
class FoundationManifest:
    """Parsed foundation-resource manifest."""

    schema_version: int
    core: str
    references: tuple[str, ...]
    templates: tuple[str, ...]
    examples: tuple[str, ...]

    def catalog(self, field: str) -> tuple[str, ...]:
        """The declared catalog for one of ``CATALOG_FIELDS``."""
        catalogs: dict[str, tuple[str, ...]] = {
            REFERENCES_FIELD: self.references,
            TEMPLATES_FIELD: self.templates,
            EXAMPLES_FIELD: self.examples,
        }
        return catalogs[field]

    @property
    def declared_paths(self) -> tuple[str, ...]:
        """Every declared path — the core entry first, then each catalog in order."""
        return (
            self.core,
            *self.references,
            *self.templates,
            *self.examples,
        )


def _catalog_entries(payload: dict[str, object], field: str) -> tuple[str, ...]:
    entries = payload[field]
    if not isinstance(entries, list) or not all(
        isinstance(entry, str) for entry in entries
    ):
        message = f"{field} must be an array of package-relative path strings"
        raise ValueError(message)
    return tuple(entries)


def parse_foundation_manifest(text: str) -> FoundationManifest:
    """Parse manifest JSON, rejecting any shape outside the declared contract."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        message = f"manifest is not valid JSON: {error}"
        raise ValueError(message) from error
    if not isinstance(payload, dict):
        message = "manifest top level must be a JSON object"
        raise ValueError(message)
    unknown = sorted(set(payload) - set(MANIFEST_FIELDS))
    if unknown:
        message = (
            "manifest carries paths and schema metadata only; "
            f"unknown fields: {', '.join(unknown)}"
        )
        raise ValueError(message)
    missing = [field for field in MANIFEST_FIELDS if field not in payload]
    if missing:
        message = f"manifest is missing fields: {', '.join(missing)}"
        raise ValueError(message)
    schema_version = payload[SCHEMA_VERSION_FIELD]
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        message = f"{SCHEMA_VERSION_FIELD} must be an integer"
        raise ValueError(message)
    core = payload[CORE_FIELD]
    if not isinstance(core, str) or not core:
        message = f"{CORE_FIELD} must be exactly one package-relative path string"
        raise ValueError(message)
    return FoundationManifest(
        schema_version=schema_version,
        core=core,
        references=_catalog_entries(payload, REFERENCES_FIELD),
        templates=_catalog_entries(payload, TEMPLATES_FIELD),
        examples=_catalog_entries(payload, EXAMPLES_FIELD),
    )


def _shipped_catalog_files(plugin_root: Path, field: str) -> tuple[str, ...]:
    directory = plugin_root / CATALOG_DIRECTORIES[field]
    if not directory.is_dir():
        return ()
    return tuple(
        sorted(
            path.relative_to(plugin_root).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        )
    )


def manifest_violations(plugin_root: Path) -> list[str]:
    """Every package-check violation for the manifest shipped in ``plugin_root``."""
    manifest_path = plugin_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        return [f"{MANIFEST_RELATIVE_PATH}: manifest file is missing"]
    try:
        manifest = parse_foundation_manifest(manifest_path.read_text(encoding="utf-8"))
    except ValueError as error:
        return [f"{MANIFEST_RELATIVE_PATH}: {error}"]

    violations: list[str] = []
    if manifest.schema_version != SUPPORTED_SCHEMA_VERSION:
        violations.append(
            f"{MANIFEST_RELATIVE_PATH}: unsupported {SCHEMA_VERSION_FIELD} "
            f"{manifest.schema_version} (supported: {SUPPORTED_SCHEMA_VERSION})"
        )

    seen: set[str] = set()
    for declared in manifest.declared_paths:
        if declared in seen:
            violations.append(
                f"{MANIFEST_RELATIVE_PATH}: duplicate declared path {declared}"
            )
        seen.add(declared)
        if not (plugin_root / declared).is_file():
            violations.append(
                f"{MANIFEST_RELATIVE_PATH}: declared path does not resolve "
                f"to a file: {declared}"
            )

    for field in CATALOG_FIELDS:
        declared_in_catalog = set(manifest.catalog(field))
        for shipped in _shipped_catalog_files(plugin_root, field):
            if shipped not in declared_in_catalog:
                violations.append(
                    f"{MANIFEST_RELATIVE_PATH}: shipped {field} file is not "
                    f"declared: {shipped}"
                )
    return violations


def iter_tree_violations(repo_root: Path) -> list[str]:
    """Check the spec-tree plugin's manifest in each generated tree under a root."""
    violations: list[str] = []
    for target in sorted(Target):
        plugin_root = repo_root / DIST_DIR_NAME / target.value / SPEC_TREE_PLUGIN_NAME
        violations.extend(
            f"{plugin_root.relative_to(repo_root).as_posix()}/{violation}"
            for violation in manifest_violations(plugin_root)
        )
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the shipped manifests under each given repository root."""
    roots = [Path(arg) for arg in (argv if argv is not None else sys.argv[1:])] or [
        Path()
    ]
    violations: list[str] = []
    for root in roots:
        violations.extend(f"{root}/{issue}" for issue in iter_tree_violations(root))
    for violation in violations:
        print(violation, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
