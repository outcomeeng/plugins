from outcomeeng_testing.harnesses.distribution import (
    directive_description_is_cleaned,
    plugin_without_skills_is_skipped,
    skill_collection_returns_complete_metadata,
    skill_copy_skips_broken_symlinks,
    skill_without_manifest_is_skipped,
    target_cleanup_preserves_only_git_metadata,
)


def test_skill_collection_returns_complete_metadata() -> None:
    assert skill_collection_returns_complete_metadata()


def test_plugin_without_skills_is_skipped() -> None:
    assert plugin_without_skills_is_skipped()


def test_skill_without_manifest_is_skipped() -> None:
    assert skill_without_manifest_is_skipped()


def test_directive_description_is_cleaned() -> None:
    assert directive_description_is_cleaned()


def test_target_cleanup_preserves_only_git_metadata() -> None:
    assert target_cleanup_preserves_only_git_metadata()


def test_skill_copy_skips_broken_symlinks() -> None:
    assert skill_copy_skips_broken_symlinks()
