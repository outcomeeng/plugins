"""Compliance evidence for source-tree and template contracts."""

import re
from collections import Counter

import pytest

from outcomeeng.distribution.build import (
    COMMENT_DELIMITER_START,
    EmissionAction,
    project_emissions,
    plugin_names,
    template_source_files,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.generators.source_and_templating import (
    SourceScenario,
    source_scenarios,
)
from outcomeeng_testing.harnesses.distribution import CANONICAL_SOURCE_ROOT
from outcomeeng_testing.harnesses.source_and_templating import (
    bare_conditional_renders_per_target,
    implementation_is_ready,
    include_uses_fragment_file_contract,
    observe_build_comment_outputs,
    observe_required_skill_guidance,
    jinja_environment_uses_custom_delimiters,
    malformed_source_tree_is_rejected,
    ordinary_plugin_root_file_is_accepted,
    require_skill_emits_identically_across_targets,
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


def test_require_skill_expands_to_neutral_terminal_guidance() -> None:
    for observation in observe_required_skill_guidance():
        assert observation.skill_ref in observation.guidance
        assert all(
            runtime_name
            not in observation.guidance.replace(
                observation.skill_ref,
                "",
            )
            for runtime_name in observation.runtime_names
        )
        assert observation.guidance.endswith("report the missing skill and stop.")
        assert "continue with" not in observation.guidance


def test_neutral_guidance_oracle_rejects_runtime_specific_wording() -> None:
    assert require_skill_neutrality_oracle_rejects_runtime_specific_guidance()


def test_require_skill_locality_oracle_rejects_inlined_content() -> None:
    assert require_skill_locality_oracle_rejects_inlined_content()


def test_require_skill_renders_inline() -> None:
    assert require_skill_renders_inline()


def test_bare_conditional_block_renders_per_target() -> None:
    assert bare_conditional_renders_per_target()


@pytest.mark.parametrize("case", source_scenarios(), ids=lambda c: c.skill)
def test_build_comment_is_stripped_without_other_jinja_tokens(
    case: SourceScenario,
) -> None:
    for target, (rendered, comment) in observe_build_comment_outputs(case).items():
        assert comment not in rendered, (
            f"{target} shipped the build comment {comment!r}"
        )
        assert COMMENT_DELIMITER_START not in rendered, (
            f"{target} shipped a comment delimiter: {rendered!r}"
        )
        assert case.fragment_body in rendered, (
            f"{target} lost the surrounding body {case.fragment_body!r}"
        )


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

    # Drive the real projection rather than re-deriving the path from the same
    # helper under test, so this fails if template fan-out stops happening.
    projection = project_emissions(CANONICAL_SOURCE_ROOT)
    for target in Target:
        for source in templates:
            rendered = [
                emission
                for emission in projection.for_target(target)
                if emission.source == source
                and emission.action in {EmissionAction.RENDER, EmissionAction.COPY}
            ]
            reached = {emission.relative_path.parts[0] for emission in rendered}
            assert reached == set(plugins), (
                f"{source} reaches {sorted(reached)} on {target.value}, "
                f"not every plugin {sorted(plugins)}"
            )
            per_plugin = Counter(
                emission.relative_path.parts[0] for emission in rendered
            )
            duplicated = {
                plugin: count for plugin, count in per_plugin.items() if count != 1
            }
            assert not duplicated, (
                f"{source} emits more than once per plugin on {target.value}: "
                f"{duplicated}"
            )


def test_per_plugin_template_body_names_no_single_plugin() -> None:
    plugins = plugin_names(CANONICAL_SOURCE_ROOT)
    for source in template_source_files(CANONICAL_SOURCE_ROOT):
        body = source.read_text(encoding="utf-8")
        # Match only identity-bearing positions. A plugin slug can also be an
        # ordinary English word ("work") or a substring of an unrelated token
        # ("python" inside "python3"), so matching prose yields false positives;
        # what actually breaks a render is a slug in a path or skill-identity
        # position, where it names one plugin inside every other's output.
        named = [
            plugin
            for plugin in plugins
            if re.search(
                rf"(?:src/plugins/|dist/[a-z]+/|/){re.escape(plugin)}(?:[/_-]|\b)"
                rf"|\b{re.escape(plugin)}-plugin\b"
                rf"|\b{re.escape(plugin)}_",
                body,
            )
        ]
        assert not named, (
            f"{source} hardcodes plugin name(s) {named}; a template body must "
            "reach every plugin through the plugin-name build variable"
        )
