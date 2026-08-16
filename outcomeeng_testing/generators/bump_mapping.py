"""Generator-owned mapping cases for bump segment tests."""

from __future__ import annotations

from collections.abc import Mapping

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.distribution.bump import (
    ChangedPath,
    DIST_CLAUDE_PLUGINS_DIR,
    DIST_CODEX_PLUGINS_DIR,
    FileStatus,
    Segment,
    SHARED_SOURCE_DIR,
    SOURCE_PLUGINS_DIR,
    Version,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CLAUDE_PLUGIN_SUBDIR_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng_testing.generators.bump import distribution_relpath


def lifecycle_surface_changes() -> tuple[ChangedPath, ...]:
    """Lifecycle changes to a declared plugin surface, across every root.

    Each entry is a non-modifying status applied to one of the three declared
    surfaces — a skill's `SKILL.md`, an agent definition, a plugin manifest —
    under the authored root and both generated roots. A rename reaches the
    surface from either end, so the last entry renames a declared surface to a
    path no surface covers: the plugin loses a skill, which the destination path
    alone does not show. These are inputs only; the segment each one classifies
    to is asserted by the linked test.
    """
    return (
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/new-skill/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.COPIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/copied-skill/{SKILL_FILENAME}",
            ),
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/source-skill/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.DELETED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/old-skill/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.RENAMED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/renamed/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{AGENTS_SUBDIR_NAME}/new-agent{MARKDOWN_FILE_SUFFIX}",
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{CLAUDE_PLUGIN_SUBDIR_NAME}/plugin.json",
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{CODEX_PLUGIN_SUBDIR_NAME}/plugin.json",
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                DIST_CLAUDE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                DIST_CODEX_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.RENAMED,
            distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "references/retired.md"),
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/retired/{SKILL_FILENAME}",
            ),
        ),
    )


def non_lifecycle_surface_changes() -> tuple[ChangedPath, ...]:
    """Changes that are either modifying or land outside a declared surface.

    The first three modify a declared surface; the rest touch a path no declared
    surface covers, under both an authored and a generated root. One of them is a
    copy whose git-detected source is another plugin's `SKILL.md`, which git
    reports whenever a new file resembles an existing one: the copy leaves that
    source untouched, so the destination alone decides the segment. These are
    inputs only; the segment each one classifies to is asserted by the linked test.
    """
    return (
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/existing/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "foo",
                f"{CLAUDE_PLUGIN_SUBDIR_NAME}/plugin.json",
            ),
        ),
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(
                DIST_CODEX_PLUGINS_DIR,
                "foo",
                f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", "skills/existing/scripts/helper.py"
            ),
        ),
        ChangedPath(
            FileStatus.COPIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", "skills/existing/scripts/copied_helper.py"
            ),
            distribution_relpath(
                SOURCE_PLUGINS_DIR,
                "bar",
                f"{SKILLS_SUBDIR_NAME}/donor/{SKILL_FILENAME}",
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", "skills/existing/references/notes.md"
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", "templates/new-template.md"
            ),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "hooks/hooks.json"),
        ),
        ChangedPath(
            FileStatus.DELETED,
            distribution_relpath(SOURCE_PLUGINS_DIR, "foo", ".gitignore"),
        ),
    )


def versions() -> SearchStrategy[Version]:
    """Generate the full non-negative semantic-version component domain."""
    component = st.integers(min_value=0)
    return st.builds(Version, major=component, minor=component, patch=component)


def segments() -> SearchStrategy[Segment]:
    """Generate every source-owned bump segment."""
    return st.sampled_from(tuple(Segment))


def mixed_minor_triggering_changes() -> tuple[ChangedPath, ...]:
    return (
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", ".claude-plugin/plugin.json"
            ),
        ),
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/existing/SKILL.md"),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(DIST_CODEX_PLUGINS_DIR, "foo", "skills/new/SKILL.md"),
        ),
    )


ATTRIBUTION_DESTINATION_PLUGIN: str = "foo"
ATTRIBUTION_SOURCE_PLUGIN: str = "bar"


def change_attribution_inputs() -> tuple[ChangedPath, ...]:
    """One change per `FileStatus`, spanning the source-owned status domain.

    Every change lands in `ATTRIBUTION_DESTINATION_PLUGIN` and carries a source
    path in `ATTRIBUTION_SOURCE_PLUGIN` wherever git reports one, so an
    attribution that reaches the source path is visible as that second plugin
    appearing in the result. The domain enumerates `FileStatus` itself, so a
    status added to the source contract enters the domain rather than needing a
    case written for it here.
    """
    destination = distribution_relpath(
        SOURCE_PLUGINS_DIR,
        ATTRIBUTION_DESTINATION_PLUGIN,
        f"{SKILLS_SUBDIR_NAME}/new-skill/{SKILL_FILENAME}",
    )
    source = distribution_relpath(
        SOURCE_PLUGINS_DIR,
        ATTRIBUTION_SOURCE_PLUGIN,
        f"{SKILLS_SUBDIR_NAME}/old-skill/{SKILL_FILENAME}",
    )
    carries_source = {FileStatus.COPIED, FileStatus.RENAMED}
    return tuple(
        ChangedPath(status, destination, source if status in carries_source else None)
        for status in FileStatus
    )


SHARED_INCLUDING_PLUGIN: str = "consumer"
SHARED_DESTINATION_TARGET: str = "voice/fragment.md"
SHARED_SOURCE_TARGET: str = "voice/retired.md"
SHARED_SOURCE_PLUGIN: str = "predecessor"


def shared_include_index() -> Mapping[str, frozenset[str]]:
    """The source-owned include index the shared-change domain resolves against.

    The destination target names one plugin and the source target names a
    different one, so an attribution that reaches only the destination is
    distinguishable from one that reaches both.
    """
    return {
        SHARED_DESTINATION_TARGET: frozenset({SHARED_INCLUDING_PLUGIN}),
        SHARED_SOURCE_TARGET: frozenset({SHARED_SOURCE_PLUGIN}),
    }


def shared_change_attribution_inputs() -> tuple[ChangedPath, ...]:
    """One shared-root change per `FileStatus`, spanning the status domain.

    Every change lands on the destination include target and carries a source
    target wherever git reports one, so an attribution that reaches the source
    is visible as `SHARED_SOURCE_PLUGIN` appearing in the result. The domain
    enumerates `FileStatus` itself, so a status added to the source contract
    enters the domain rather than needing a case written for it here.
    """
    destination = f"{SHARED_SOURCE_DIR}/{SHARED_DESTINATION_TARGET}"
    source = f"{SHARED_SOURCE_DIR}/{SHARED_SOURCE_TARGET}"
    carries_source = {FileStatus.COPIED, FileStatus.RENAMED}
    return tuple(
        ChangedPath(status, destination, source if status in carries_source else None)
        for status in FileStatus
    )


def patch_only_changes() -> tuple[ChangedPath, ...]:
    return (
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(
                SOURCE_PLUGINS_DIR, "foo", ".claude-plugin/plugin.json"
            ),
        ),
        ChangedPath(
            FileStatus.MODIFIED,
            distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "skills/existing/SKILL.md"),
        ),
        ChangedPath(
            FileStatus.ADDED,
            distribution_relpath(DIST_CLAUDE_PLUGINS_DIR, "foo", "templates/foo.md"),
        ),
    )
