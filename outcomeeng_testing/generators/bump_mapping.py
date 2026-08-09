"""Generator-owned mapping cases for bump segment tests."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.distribution.bump import (
    ChangedPath,
    DIST_CLAUDE_PLUGINS_DIR,
    DIST_CODEX_PLUGINS_DIR,
    FileStatus,
    Segment,
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

AUTO_SEGMENT_MAPPING_CASES: tuple[tuple[FileStatus, str, Segment], ...] = (
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/new-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.COPIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/copied-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.DELETED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/old-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.RENAMED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/renamed/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{AGENTS_SUBDIR_NAME}/new-agent{MARKDOWN_FILE_SUFFIX}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{CLAUDE_PLUGIN_SUBDIR_NAME}/plugin.json",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{CODEX_PLUGIN_SUBDIR_NAME}/plugin.json",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            DIST_CLAUDE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            DIST_CODEX_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
        ),
        Segment.MINOR,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/existing/{SKILL_FILENAME}",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR,
            "foo",
            f"{CLAUDE_PLUGIN_SUBDIR_NAME}/plugin.json",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.MODIFIED,
        distribution_relpath(
            DIST_CODEX_PLUGINS_DIR,
            "foo",
            f"{SKILLS_SUBDIR_NAME}/generated-skill/{SKILL_FILENAME}",
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR, "foo", "skills/existing/scripts/helper.py"
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.COPIED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR, "foo", "skills/existing/scripts/copied_helper.py"
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(
            SOURCE_PLUGINS_DIR, "foo", "skills/existing/references/notes.md"
        ),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "templates/new-template.md"),
        Segment.PATCH,
    ),
    (
        FileStatus.ADDED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", "hooks/hooks.json"),
        Segment.PATCH,
    ),
    (
        FileStatus.DELETED,
        distribution_relpath(SOURCE_PLUGINS_DIR, "foo", ".gitignore"),
        Segment.PATCH,
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


def change_attribution_cases() -> tuple[tuple[ChangedPath, frozenset[str]], ...]:
    """Every `FileStatus`, paired with the plugins that change attributes to.

    The destination sits in `foo` and any source in `bar`, so an attribution
    that reaches the source path is visible as `bar` appearing in the result.
    """
    destination = distribution_relpath(
        SOURCE_PLUGINS_DIR, "foo", f"{SKILLS_SUBDIR_NAME}/new-skill/{SKILL_FILENAME}"
    )
    source = distribution_relpath(
        SOURCE_PLUGINS_DIR, "bar", f"{SKILLS_SUBDIR_NAME}/old-skill/{SKILL_FILENAME}"
    )
    return (
        (ChangedPath(FileStatus.ADDED, destination), frozenset({"foo"})),
        (ChangedPath(FileStatus.MODIFIED, destination), frozenset({"foo"})),
        (ChangedPath(FileStatus.DELETED, destination), frozenset({"foo"})),
        (ChangedPath(FileStatus.COPIED, destination, source), frozenset({"foo"})),
        (
            ChangedPath(FileStatus.RENAMED, destination, source),
            frozenset({"foo", "bar"}),
        ),
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
