from pathlib import Path

from outcomeeng.distribution.contracts import (
    GIT_METADATA_DIR_NAME,
    REFERENCES_SUBDIR_NAME,
    SKILL_FILENAME,
)
from outcomeeng_testing.harnesses.distribution import (
    observe_directive_description_cleaning,
    observe_plugin_without_skills,
    observe_skill_collection,
    observe_skill_copy_with_links,
    observe_skill_without_manifest,
    observe_target_cleanup,
)


def test_skill_collection_returns_complete_metadata() -> None:
    observed = observe_skill_collection()

    assert observed.sources
    assert {
        (skill.source, skill.name, skill.description, skill.dir_name)
        for skill in observed.collected
    } == {
        (source, skill_name, observed.scenario.action, skill_name)
        for skill_name, source in observed.sources.items()
    }


def test_plugin_without_skills_is_skipped() -> None:
    assert observe_plugin_without_skills() == ()


def test_skill_without_manifest_is_skipped() -> None:
    assert observe_skill_without_manifest() == ()


def test_directive_description_is_cleaned() -> None:
    observed = observe_directive_description_cleaning()

    assert observed.cleaned == observed.action


def test_target_cleanup_preserves_only_git_metadata() -> None:
    observed = observe_target_cleanup()

    assert observed.remaining_entries == (GIT_METADATA_DIR_NAME,)
    assert observed.preserved_metadata_content == observed.written_metadata_content


def test_skill_copy_skips_broken_symlinks() -> None:
    observed = observe_skill_copy_with_links()
    references = Path(REFERENCES_SUBDIR_NAME)

    assert Path(SKILL_FILENAME) in observed.copied_paths
    assert references / observed.regular_reference in observed.copied_paths
    assert references / observed.valid_link_reference in observed.copied_paths
    assert references / observed.broken_link_reference not in observed.copied_paths
