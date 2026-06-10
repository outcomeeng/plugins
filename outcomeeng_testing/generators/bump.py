"""Generators for bump tests.

Provides domain-shaped input construction for manifest text, manifest
relative paths, resolution of inert manifest fixtures, and Hypothesis
strategies for diff-path domains. Generators emit canonical-form JSON
and `src/plugins/{name}/...` paths so test files do not duplicate the
construction logic; the fixture resolver returns absolute paths into
`outcomeeng_testing/fixtures/bump/` so tests can read real-shaped
manifest payloads by path; the path strategies vary, compose, and
shrink across the change-detection input space.

All vocabulary (`SOURCE_PLUGINS_DIR`, `CLAUDE_MANIFEST`, `CODEX_MANIFEST`) comes
from the source module `outcomeeng.distribution.bump`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import outcomeeng_testing
from hypothesis import strategies as st

from outcomeeng.distribution.bump import (
    CLAUDE_MANIFEST,
    SOURCE_PLUGINS_DIR,
    ChangedPath,
    FileStatus,
)

_FIXTURES_ROOT: Path = Path(outcomeeng_testing.__file__).parent / "fixtures" / "bump"


def manifest_relpath(plugin: str, manifest: str) -> str:
    """Return the repository-relative manifest path for `plugin`/`manifest`."""
    return f"{SOURCE_PLUGINS_DIR}/{plugin}/{manifest}"


def manifest_text(name: str, version: str) -> str:
    """Return canonical-form plugin manifest JSON with the given version."""
    return json.dumps({"name": name, "version": version}, indent=2) + "\n"


def version_of(manifest_text: str) -> str:
    """Return the `version` field parsed from a manifest's text."""
    return cast(str, json.loads(manifest_text)["version"])


def manifest_fixture_path(name: str) -> Path:
    """Return the absolute path to an inert manifest fixture under `bump/`.

    The returned path is consumed by reading the file or copying it into
    a temporary product; the fixture is never imported as a Python module.
    """
    return _FIXTURES_ROOT / name


def patch_change(plugin: str) -> tuple[ChangedPath, ...]:
    """Single MODIFIED manifest change — `auto_segment` yields PATCH."""
    return (
        ChangedPath(
            status=FileStatus.MODIFIED,
            path=manifest_relpath(plugin, CLAUDE_MANIFEST),
        ),
    )


def minor_change(plugin: str, *, slug: str = "new-skill") -> tuple[ChangedPath, ...]:
    """Single ADDED SKILL.md change — `auto_segment` yields MINOR."""
    return (
        ChangedPath(
            status=FileStatus.ADDED,
            path=f"{SOURCE_PLUGINS_DIR}/{plugin}/skills/{slug}/SKILL.md",
        ),
    )


def patch_changes(*plugins: str) -> dict[str, tuple[ChangedPath, ...]]:
    """Build a `ChangeProbe`-shaped mapping where each plugin gets a
    single MODIFIED change (auto-detected segment: PATCH).
    """
    return {plugin: patch_change(plugin) for plugin in plugins}


def plugin_names() -> st.SearchStrategy[str]:
    """Non-empty path segments suitable for use as a plugin directory name.

    Excludes `/` (would split into multiple segments) and the NUL byte
    (rejected by filesystems and most diff tools). Spans whitespace,
    Unicode, and punctuation otherwise — the path-prefix discipline
    treats every non-empty `/`-free segment as a candidate plugin name,
    not just kebab-case identifiers.
    """
    return st.text(
        alphabet=st.characters(blacklist_characters=("/", "\x00")),
        min_size=1,
    )


def relative_subpaths() -> st.SearchStrategy[str]:
    """Non-empty relative subpaths to nest under a plugin directory.

    May contain `/`, enabling deep nesting like `skills/x/SKILL.md`.
    Empty subpath is excluded so the resulting `src/plugins/<name>/<subpath>`
    is always a real file path, not a directory.
    """
    return st.text(
        alphabet=st.characters(blacklist_characters=("\x00",)),
        min_size=1,
    )


def arbitrary_diff_paths() -> st.SearchStrategy[str]:
    """Arbitrary text representing diff paths — including pathological cases.

    Covers any string a `git diff --name-only` line might carry: paths
    outside `src/plugins/`, paths with empty segments (`src/plugins//foo`),
    paths that equal the prefix without a name (`src/plugins/`, `src/plugins`),
    and paths under the prefix with valid plugin names.
    """
    return st.text(alphabet=st.characters(blacklist_characters=("\x00",)))


__all__ = [
    "arbitrary_diff_paths",
    "manifest_fixture_path",
    "manifest_relpath",
    "manifest_text",
    "minor_change",
    "patch_change",
    "patch_changes",
    "plugin_names",
    "relative_subpaths",
    "version_of",
]
