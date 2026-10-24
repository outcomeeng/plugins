"""Compliance evidence: the package checks reject every violating foundation manifest.

Each governing rule is exercised against a violating plugin tree and a clean one,
so enforcement is neither trivially always-failing nor blind to a real defect.
Manifest vocabulary — field names, the supported schema version, catalog
directories — is imported from the validation module that owns it; only the
violating values are synthesized here, because each violating case is the rule
under enforcement.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from outcomeeng.validation.foundation_manifest import (
    CATALOG_DIRECTORIES,
    CORE_DOCUMENT_RELATIVE_PATH,
    CORE_FIELD,
    EXAMPLES_FIELD,
    MANIFEST_RELATIVE_PATH,
    REFERENCES_FIELD,
    SCHEMA_VERSION_FIELD,
    SUPPORTED_SCHEMA_VERSION,
    TEMPLATES_FIELD,
    manifest_violations,
)


def _payload(
    *,
    references: tuple[str, ...],
    templates: tuple[str, ...],
    examples: tuple[str, ...],
    core: object = CORE_DOCUMENT_RELATIVE_PATH,
    schema_version: object = SUPPORTED_SCHEMA_VERSION,
) -> dict[str, object]:
    return {
        SCHEMA_VERSION_FIELD: schema_version,
        CORE_FIELD: core,
        REFERENCES_FIELD: list(references),
        TEMPLATES_FIELD: list(templates),
        EXAMPLES_FIELD: list(examples),
    }


def _write_plugin(
    root: Path,
    manifest_text: str,
    *,
    files: tuple[str, ...] = (),
) -> Path:
    manifest_path = root / MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    for directory in CATALOG_DIRECTORIES.values():
        (root / directory).mkdir(parents=True, exist_ok=True)
    for relative in files:
        file_path = root / relative
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("", encoding="utf-8")
    return root


def _reference(name: str) -> str:
    return f"{CATALOG_DIRECTORIES[REFERENCES_FIELD]}/{name}"


def _valid_plugin(root: Path) -> Path:
    reference = _reference("guide.md")
    payload = _payload(references=(reference,), templates=(), examples=())
    return _write_plugin(
        root,
        json.dumps(payload),
        files=(CORE_DOCUMENT_RELATIVE_PATH, reference),
    )


def test_valid_plugin_tree_passes(tmp_path: Path) -> None:
    assert manifest_violations(_valid_plugin(tmp_path)) == []


def test_missing_manifest_file_is_flagged(tmp_path: Path) -> None:
    assert manifest_violations(tmp_path)


def test_malformed_json_is_flagged(tmp_path: Path) -> None:
    root = _write_plugin(tmp_path, "{not json", files=(CORE_DOCUMENT_RELATIVE_PATH,))
    assert manifest_violations(root)


def test_unsupported_schema_version_is_flagged(tmp_path: Path) -> None:
    payload = _payload(
        references=(),
        templates=(),
        examples=(),
        schema_version=SUPPORTED_SCHEMA_VERSION + 1,
    )
    root = _write_plugin(
        tmp_path, json.dumps(payload), files=(CORE_DOCUMENT_RELATIVE_PATH,)
    )
    assert manifest_violations(root)


def test_non_integer_schema_version_is_flagged(tmp_path: Path) -> None:
    payload = _payload(references=(), templates=(), examples=(), schema_version="one")
    root = _write_plugin(
        tmp_path, json.dumps(payload), files=(CORE_DOCUMENT_RELATIVE_PATH,)
    )
    assert manifest_violations(root)


def test_missing_core_entry_is_flagged(tmp_path: Path) -> None:
    payload: Mapping[str, object] = {
        key: value
        for key, value in _payload(references=(), templates=(), examples=()).items()
        if key != CORE_FIELD
    }
    root = _write_plugin(tmp_path, json.dumps(dict(payload)))
    assert manifest_violations(root)


def test_more_than_one_core_entry_is_flagged(tmp_path: Path) -> None:
    # NEVER: more than one core — a list-valued core is not a single document.
    payload = _payload(
        references=(),
        templates=(),
        examples=(),
        core=[CORE_DOCUMENT_RELATIVE_PATH, "skills/understand/other.md"],
    )
    root = _write_plugin(
        tmp_path, json.dumps(payload), files=(CORE_DOCUMENT_RELATIVE_PATH,)
    )
    assert manifest_violations(root)


def test_content_bearing_extra_field_is_flagged(tmp_path: Path) -> None:
    # NEVER: the manifest carries content beyond paths and schema metadata.
    payload = _payload(references=(), templates=(), examples=())
    payload["body"] = "TRUTH FLOWS DOWN."
    root = _write_plugin(
        tmp_path, json.dumps(payload), files=(CORE_DOCUMENT_RELATIVE_PATH,)
    )
    assert manifest_violations(root)


def test_unresolved_declared_path_is_flagged(tmp_path: Path) -> None:
    payload = _payload(references=(_reference("absent.md"),), templates=(), examples=())
    root = _write_plugin(
        tmp_path, json.dumps(payload), files=(CORE_DOCUMENT_RELATIVE_PATH,)
    )
    assert manifest_violations(root)


def test_duplicate_path_within_a_catalog_is_flagged(tmp_path: Path) -> None:
    reference = _reference("guide.md")
    payload = _payload(references=(reference, reference), templates=(), examples=())
    root = _write_plugin(
        tmp_path,
        json.dumps(payload),
        files=(CORE_DOCUMENT_RELATIVE_PATH, reference),
    )
    assert manifest_violations(root)


def test_duplicate_path_across_catalogs_is_flagged(tmp_path: Path) -> None:
    reference = _reference("guide.md")
    payload = _payload(references=(reference,), templates=(reference,), examples=())
    root = _write_plugin(
        tmp_path,
        json.dumps(payload),
        files=(CORE_DOCUMENT_RELATIVE_PATH, reference),
    )
    assert manifest_violations(root)


def test_omitted_shipped_resource_is_flagged(tmp_path: Path) -> None:
    # ALWAYS: every file under the catalog directories is declared.
    root = _valid_plugin(tmp_path)
    undeclared = tmp_path / _reference("undeclared.md")
    undeclared.write_text("", encoding="utf-8")
    assert manifest_violations(root)


def test_missing_core_document_file_is_flagged(tmp_path: Path) -> None:
    reference = _reference("guide.md")
    payload = _payload(references=(reference,), templates=(), examples=())
    root = _write_plugin(tmp_path, json.dumps(payload), files=(reference,))
    assert manifest_violations(root)
