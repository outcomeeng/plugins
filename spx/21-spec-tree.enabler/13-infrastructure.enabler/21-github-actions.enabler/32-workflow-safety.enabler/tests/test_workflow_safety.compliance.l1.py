"""Compliance evidence for GitHub Actions workflow safety policy."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Final, cast

# PyYAML ships without inline types; this test casts parsed workflow structure below.
import yaml  # type: ignore[import-untyped]

REPO_ROOT: Final = Path(__file__).resolve().parents[6]
WORKFLOWS_DIR: Final = REPO_ROOT / ".github" / "workflows"
FULL_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")


def _walk_uses(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in cast("dict[str, object]", value).items():
            if key == "uses" and isinstance(nested, str):
                yield nested
            else:
                yield from _walk_uses(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_uses(nested)


def _workflow_documents() -> Iterator[dict[str, Any]]:
    for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
        yield cast(
            "dict[str, Any]", yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
        )


def _external_uses() -> Iterator[str]:
    for document in _workflow_documents():
        for uses in _walk_uses(document):
            if not uses.startswith("./"):
                yield uses


def test_external_workflow_uses_are_pinned_to_full_commit_sha() -> None:
    for uses in _external_uses():
        _, _, ref = uses.partition("@")

        assert FULL_SHA_RE.fullmatch(ref), uses
