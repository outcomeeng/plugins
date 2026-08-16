"""Generators for bump tests.

Provides domain-shaped input construction for manifest text, manifest
relative paths, resolution of inert manifest fixtures, and Hypothesis
strategies for diff-path domains. Generators emit canonical-form JSON
and recognized distribution-surface paths so test files do not duplicate
the construction logic; the fixture resolver returns absolute paths into
`outcomeeng_testing/fixtures/bump/` so tests can read real-shaped
manifest payloads by path; the path strategies vary, compose, and
shrink across the change-detection input space.

All vocabulary (`SOURCE_PLUGINS_DIR`, `DIST_CLAUDE_PLUGINS_DIR`,
`DIST_CODEX_PLUGINS_DIR`, `CLAUDE_MANIFEST`, `CODEX_MANIFEST`) comes from
the source module `outcomeeng.distribution.bump`.
"""

from __future__ import annotations

from collections.abc import Mapping

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import outcomeeng_testing
from hypothesis import strategies as st

from outcomeeng.distribution.bump import (
    CLAUDE_MANIFEST,
    DIST_CLAUDE_PLUGINS_DIR,
    DIST_CODEX_PLUGINS_DIR,
    SOURCE_PLUGINS_DIR,
    ChangedPath,
    FileStatus,
)

_FIXTURES_ROOT: Path = Path(outcomeeng_testing.__file__).parent / "fixtures" / "bump"


@dataclass(frozen=True)
class MalformedManifestCase:
    content: str
    expected_diagnostic: str


def manifest_relpath(plugin: str, manifest: str) -> str:
    """Return the repository-relative manifest path for `plugin`/`manifest`."""
    return f"{SOURCE_PLUGINS_DIR}/{plugin}/{manifest}"


def distribution_roots() -> tuple[str, ...]:
    """Return every source-owned root that contributes bump-triggering paths."""
    return (SOURCE_PLUGINS_DIR, DIST_CLAUDE_PLUGINS_DIR, DIST_CODEX_PLUGINS_DIR)


def distribution_relpath(root: str, plugin: str, subpath: str) -> str:
    """Return a repository-relative path under a recognized distribution root."""
    return f"{root}/{plugin}/{subpath}"


def manifest_text(name: str, version: str) -> str:
    """Return canonical-form plugin manifest JSON with the given version."""
    return json.dumps({"name": name, "version": version}, indent=2) + "\n"


def malformed_manifest_cases(plugin: str) -> tuple[MalformedManifestCase, ...]:
    """Return manifest payloads that lack a parseable string version."""
    return (
        MalformedManifestCase(content="{", expected_diagnostic="invalid JSON"),
        MalformedManifestCase(
            content=json.dumps({"name": plugin}),
            expected_diagnostic="string version",
        ),
        MalformedManifestCase(
            content=json.dumps({"version": 1}),
            expected_diagnostic="string version",
        ),
        MalformedManifestCase(
            content=json.dumps({"version": "not-semver"}),
            expected_diagnostic="invalid version",
        ),
    )


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
            path=distribution_relpath(
                SOURCE_PLUGINS_DIR,
                plugin,
                f"skills/{slug}/SKILL.md",
            ),
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


def include_targets() -> st.SearchStrategy[str]:
    """Non-empty include targets a shared fragment can be addressed by.

    A target is the path a build include directive quotes, resolved relative
    to the shared authored root, so it may nest (`prose/voice/fragment.md`)
    but never starts or ends empty.
    """
    return st.text(
        alphabet=st.characters(blacklist_characters=("\x00",)),
        min_size=1,
    )


def shared_include_indexes() -> st.SearchStrategy[Mapping[str, frozenset[str]]]:
    """Arbitrary include indexes mapping a target to the plugins naming it.

    The domain spans empty indexes, single-consumer targets, and targets
    several plugins include, so the resolution under test is exercised against
    an index shape it did not choose.
    """
    return st.dictionaries(
        keys=include_targets(),
        values=st.frozensets(plugin_names(), min_size=1, max_size=3),
        max_size=4,
    )


@st.composite
def indexed_targets(
    draw: st.DrawFn,
) -> tuple[str, Mapping[str, frozenset[str]]]:
    """An include index paired with a target that is usually one of its keys.

    Drawing the target independently of the index would make a hit vanishingly
    rare, so a resolution that always returned the empty set would satisfy the
    property almost every run. Sampling the index's own keys when it has any
    keeps the covered domain spanning both hits and misses.
    """
    index = draw(shared_include_indexes())
    if index:
        target = draw(st.one_of(st.sampled_from(sorted(index)), include_targets()))
    else:
        target = draw(include_targets())
    return target, index


def arbitrary_diff_paths() -> st.SearchStrategy[str]:
    """Arbitrary text representing diff paths — including pathological cases.

    Covers any string a `git diff --name-only` line might carry: paths
    outside recognized roots, paths with empty segments
    (`src/plugins//foo`), paths that equal a prefix without a name
    (`src/plugins/`, `src/plugins`), and paths under recognized roots
    with valid plugin names.
    """
    return st.text(alphabet=st.characters(blacklist_characters=("\x00",)))


__all__ = [
    "arbitrary_diff_paths",
    "distribution_relpath",
    "distribution_roots",
    "malformed_manifest_cases",
    "MalformedManifestCase",
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
