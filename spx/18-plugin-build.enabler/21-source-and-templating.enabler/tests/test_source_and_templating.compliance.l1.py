"""Compliance evidence for source-tree and template contracts."""

import re

from outcomeeng.distribution.build import (
    plugin_names,
    template_relative_path,
    template_source_files,
)
from outcomeeng_testing.harnesses.distribution import CANONICAL_SOURCE_ROOT
from outcomeeng_testing.harnesses.source_and_templating import (
    bare_conditional_renders_per_target,
    implementation_is_ready,
    include_uses_fragment_file_contract,
    jinja_environment_uses_custom_delimiters,
    malformed_source_tree_is_rejected,
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


def test_build_rejects_malformed_src_tree() -> None:
    assert malformed_source_tree_is_rejected()


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


def test_per_plugin_template_renders_once_into_every_plugin() -> None:
    plugins = plugin_names(CANONICAL_SOURCE_ROOT)
    templates = template_source_files(CANONICAL_SOURCE_ROOT)
    assert plugins
    assert templates
    for source in templates:
        rendered_for = {
            template_relative_path(
                source, src_root=CANONICAL_SOURCE_ROOT, plugin=plugin
            ).parts[0]
            for plugin in plugins
        }
        assert rendered_for == set(plugins), (
            f"{source} does not reach every plugin: {sorted(rendered_for)}"
        )


def test_per_plugin_template_body_names_no_single_plugin() -> None:
    plugins = plugin_names(CANONICAL_SOURCE_ROOT)
    for source in template_source_files(CANONICAL_SOURCE_ROOT):
        body = source.read_text(encoding="utf-8")
        # Whole-word only: a plugin slug is a false positive as a substring of
        # an unrelated token, such as "python" inside the "python3" interpreter.
        named = [
            plugin for plugin in plugins if re.search(rf"\b{re.escape(plugin)}\b", body)
        ]
        assert not named, (
            f"{source} hardcodes plugin name(s) {named}; a template body must "
            "reach every plugin through the plugin-name build variable"
        )
