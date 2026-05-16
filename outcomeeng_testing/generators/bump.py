"""Generators for bump tests.

Provides domain-shaped input construction for manifest text, manifest
relative paths, resolution of inert manifest fixtures, and Hypothesis
strategies for diff-path domains. Generators emit canonical-form JSON
and `plugins/{name}/...` paths so test files do not duplicate the
construction logic; the fixture resolver returns absolute paths into
`outcomeeng_testing/fixtures/bump/` so tests can read real-shaped
manifest payloads by path; the path strategies vary, compose, and
shrink across the change-detection input space.

All vocabulary (`PLUGINS_DIR`, `CLAUDE_MANIFEST`, `CODEX_MANIFEST`) comes
from the source module `outcomeeng.distribution.bump`.
"""

from __future__ import annotations

import json
from pathlib import Path

import outcomeeng_testing
from hypothesis import strategies as st

from outcomeeng.distribution.bump import PLUGINS_DIR

_FIXTURES_ROOT: Path = Path(outcomeeng_testing.__file__).parent / "fixtures" / "bump"


def manifest_relpath(plugin: str, manifest: str) -> str:
    """Return the repository-relative manifest path for `plugin`/`manifest`."""
    return f"{PLUGINS_DIR}/{plugin}/{manifest}"


def manifest_text(name: str, version: str) -> str:
    """Return canonical-form plugin manifest JSON with the given version."""
    return json.dumps({"name": name, "version": version}, indent=2) + "\n"


def version_of(manifest_text: str) -> str:
    """Return the `version` field parsed from a manifest's text."""
    return json.loads(manifest_text)["version"]


def manifest_fixture_path(name: str) -> Path:
    """Return the absolute path to an inert manifest fixture under `bump/`.

    The returned path is consumed by reading the file or copying it into
    a temporary product; the fixture is never imported as a Python module.
    """
    return _FIXTURES_ROOT / name


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
    Empty subpath is excluded so the resulting `plugins/<name>/<subpath>`
    is always a real file path, not a directory.
    """
    return st.text(
        alphabet=st.characters(blacklist_characters=("\x00",)),
        min_size=1,
    )


def arbitrary_diff_paths() -> st.SearchStrategy[str]:
    """Arbitrary text representing diff paths — including pathological cases.

    Covers any string a `git diff --name-only` line might carry: paths
    outside `plugins/`, paths with empty segments (`plugins//foo`),
    paths that equal the prefix without a name (`plugins/`, `plugins`),
    and paths under the prefix with valid plugin names.
    """
    return st.text(alphabet=st.characters(blacklist_characters=("\x00",)))


__all__ = [
    "arbitrary_diff_paths",
    "manifest_fixture_path",
    "manifest_relpath",
    "manifest_text",
    "plugin_names",
    "relative_subpaths",
    "version_of",
]
