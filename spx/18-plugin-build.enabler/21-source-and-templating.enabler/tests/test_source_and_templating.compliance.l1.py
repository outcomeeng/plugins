"""Compliance evidence for source-tree and template contracts."""

from outcomeeng_testing.harnesses.source_and_templating import (
    bare_conditional_renders_per_target,
    implementation_is_ready,
    include_uses_fragment_file_contract,
    jinja_environment_uses_custom_delimiters,
    ordinary_plugin_root_file_is_accepted,
    require_skill_emits_identically_across_targets,
    require_skill_expands_to_neutral_guidance,
    require_skill_locality_oracle_rejects_inlined_content,
    require_skill_neutrality_oracle_rejects_runtime_specific_guidance,
    require_skill_renders_inline,
    shared_topic_references_travel_with_fragment,
    shared_topic_without_fragment_is_rejected,
    skill_dir_escape_survives_jinja_pass,
    unrecognized_plugin_subdirectories_are_rejected,
    well_formed_source_tree_builds,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


def test_build_accepts_well_formed_src_tree() -> None:
    assert well_formed_source_tree_builds()


def test_build_accepts_ordinary_files_under_plugin_root() -> None:
    assert ordinary_plugin_root_file_is_accepted()


def test_build_rejects_unrecognized_plugin_subdirectories() -> None:
    assert unrecognized_plugin_subdirectories_are_rejected()


def test_build_rejects_shared_topic_without_fragment() -> None:
    assert shared_topic_without_fragment_is_rejected()


def test_shared_topic_references_travel_with_fragment() -> None:
    assert shared_topic_references_travel_with_fragment()


def test_jinja_environment_uses_custom_delimiters() -> None:
    assert jinja_environment_uses_custom_delimiters()


def test_require_skill_expands_to_neutral_guidance() -> None:
    assert require_skill_expands_to_neutral_guidance()


def test_neutral_guidance_oracle_rejects_runtime_specific_wording() -> None:
    assert require_skill_neutrality_oracle_rejects_runtime_specific_guidance()


def test_require_skill_locality_oracle_rejects_inlined_content() -> None:
    assert require_skill_locality_oracle_rejects_inlined_content()


def test_require_skill_renders_inline() -> None:
    assert require_skill_renders_inline()


def test_bare_conditional_block_renders_per_target() -> None:
    assert bare_conditional_renders_per_target()


def test_skill_dir_escape_survives_jinja_pass() -> None:
    assert skill_dir_escape_survives_jinja_pass()


def test_require_skill_expands_identically_across_targets() -> None:
    assert require_skill_emits_identically_across_targets()


def test_include_directive_uses_fragment_file_contract() -> None:
    assert include_uses_fragment_file_contract()
