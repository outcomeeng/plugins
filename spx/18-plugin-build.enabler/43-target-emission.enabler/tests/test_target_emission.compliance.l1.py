"""Compliance evidence for per-target emission."""

from __future__ import annotations

from collections import Counter

from outcomeeng_testing.harnesses.distribution import CANONICAL_SOURCE_ROOT
from outcomeeng.distribution.build import (
    AGENT_CAPABILITY_REGISTRY,
    CLAUDE_SKILL_DIR_TOKEN,
    CODEX_SKILL_DIR_TOKEN,
    CLAUDE_ONLY_FRONTMATTER_FIELDS,
    DISABLE_MODEL_INVOCATION_FIELD,
    EXECUTION_TIME_INJECTION_START,
    EXECUTION_TIME_INJECTION_END,
    FLAT_AGENT_PLUGIN_SEPARATOR,
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE,
    EmissionAction,
    agent_capability,
    agent_slug,
    plugin_names,
    template_source_files,
    skill_dir_path_references,
    frontmatter_field_names,
    rewrite_paths_for_target,
    strip_frontmatter_fields,
    contains_execution_time_skill_content_injection,
)
from outcomeeng.distribution.contracts import SKILLS_SUBDIR_NAME, Target
from outcomeeng.distribution.contracts import RUNTIME_TOKEN_USE_SKILL_NAMES
from outcomeeng.distribution.agents import READ_ONLY_TOOLS
from outcomeeng.validation.skill_frontmatter import (
    ALLOWED_TOOLS_FIELD,
    ARGUMENT_HINT_FIELD,
)
from outcomeeng_testing.generators.source_and_templating import source_scenarios
from outcomeeng_testing.generators.target_emission import execution_time_commands
from outcomeeng_testing.harnesses.target_emission import (
    projected_versus_emitted,
    projected_sources,
    text_emissions,
    emitted_texts,
    optional_tool_emissions,
    repeated_include_observations,
    scoped_include_observations,
    source_emission_counts,
    agent_artifact_paths,
    agent_artifact_texts,
    structure_deviations,
    synthetic_inventory,
)


def test_every_source_file_emits_to_both_target_trees() -> None:
    counts = source_emission_counts()
    sources = projected_sources()
    assert sources
    template_sources = set(template_source_files(CANONICAL_SOURCE_ROOT))
    plugin_count = len(plugin_names(CANONICAL_SOURCE_ROOT))
    for target, per_source in counts.items():
        missing = [source for source in sources if per_source[source] < 1]
        assert not missing, f"{target.value} emits nothing for {missing}"
        # An ordinary source emits exactly once per target; only a per-plugin
        # template fans out, and then exactly once per plugin. Requiring only
        # "at least one" would let a duplicate emission pass unnoticed.
        for source in sources:
            expected = plugin_count if source in template_sources else 1
            assert per_source[source] == expected, (
                f"{target.value} emits {per_source[source]} outputs for {source}, "
                f"expected {expected}"
            )

    for target, inventory in projected_versus_emitted().items():
        assert inventory.projected_paths == inventory.emitted_paths, (
            f"{target.value} projected/emitted path mismatch: "
            f"{inventory.projected_paths ^ inventory.emitted_paths}"
        )
        assert inventory.projected_directories == inventory.emitted_directories, (
            f"{target.value} projected/emitted directory mismatch: "
            f"{inventory.projected_directories ^ inventory.emitted_directories}"
        )

    fixture = synthetic_inventory()
    assert fixture.covered_subdirs == fixture.expected_subdirs, (
        "synthetic fixture misses plugin subdirectories: "
        f"{fixture.expected_subdirs - fixture.covered_subdirs}"
    )
    assert any(len(path.parts) == 2 for path in fixture.source_paths), (
        "synthetic fixture covers no plugin-root file"
    )
    required_actions = {
        EmissionAction.FAN_OUT,
        EmissionAction.CONVERT_AGENT,
    }
    assert required_actions <= fixture.covered_actions, (
        f"synthetic fixture misses emission actions: "
        f"{required_actions - fixture.covered_actions}"
    )
    for target, per_source in fixture.per_source_counts.items():
        uncovered = [path for path in fixture.source_paths if per_source[path] < 1]
        assert not uncovered, f"{target.value} emits nothing for {uncovered}"
    for target, inventory in fixture.projected_versus_emitted.items():
        assert inventory.projected_paths == inventory.emitted_paths, (
            f"synthetic {target.value} projected/emitted mismatch: "
            f"{inventory.projected_paths ^ inventory.emitted_paths}"
        )


def test_target_trees_mirror_source_structure() -> None:
    capabilities = {target: agent_capability(target) for target in Target}
    for target, deviations in structure_deviations().items():
        if capabilities[target].manifest_declares_agents:
            assert not deviations, (
                f"{target.value} declares agents in its manifest, so no output "
                f"may leave its mirrored path: {deviations}"
            )
            continue
        for path in deviations:
            assert path.parts[1] == SKILLS_SUBDIR_NAME, (
                f"{target.value} deviation outside the lifecycle skill: {path}"
            )
            assert path.suffix == capabilities[target].suffix, (
                f"{target.value} deviation is not a native agent artifact: {path}"
            )


def test_repeated_include_emits_shared_source_once_per_target() -> None:
    observations = repeated_include_observations()
    assert observations
    for observation in observations:
        for target, count in observation.counts.items():
            assert count == 1, (observation.case.skill_ref, target, count)


def test_claude_output_preserves_skill_dir_token() -> None:
    emissions = tuple(row for row in text_emissions() if row.target is Target.CLAUDE)
    assert any(CLAUDE_SKILL_DIR_TOKEN in row.source for row in emissions)
    for row in emissions:
        assert Counter(
            skill_dir_path_references(row.output, CLAUDE_SKILL_DIR_TOKEN)
        ) == Counter(skill_dir_path_references(row.source, CLAUDE_SKILL_DIR_TOKEN)), (
            row.path
        )
        assert row.output.count(CLAUDE_SKILL_DIR_TOKEN) == row.source.count(
            CLAUDE_SKILL_DIR_TOKEN
        ), row.path


def test_codex_output_rewrites_skill_dir_token_to_codex_token() -> None:
    emissions = tuple(row for row in text_emissions() if row.target is Target.CODEX)
    assert any(CLAUDE_SKILL_DIR_TOKEN in row.source for row in emissions)
    for row in emissions:
        escaped = tuple(
            line
            for line in row.source.splitlines()
            if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE in line
        )
        unescaped = tuple(
            line
            for line in row.source.splitlines()
            if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in line
        )
        assert Counter(
            skill_dir_path_references(row.output, CLAUDE_SKILL_DIR_TOKEN)
        ) == Counter(
            reference
            for line in escaped
            for reference in skill_dir_path_references(line, CLAUDE_SKILL_DIR_TOKEN)
        ), row.path
        assert Counter(
            skill_dir_path_references(row.output, CODEX_SKILL_DIR_TOKEN)
        ) == Counter(
            reference.replace(CLAUDE_SKILL_DIR_TOKEN, CODEX_SKILL_DIR_TOKEN, 1)
            for line in unescaped
            for reference in skill_dir_path_references(line, CLAUDE_SKILL_DIR_TOKEN)
        ) + Counter(skill_dir_path_references(row.source, CODEX_SKILL_DIR_TOKEN)), (
            row.path
        )
        assert row.output.count(CLAUDE_SKILL_DIR_TOKEN) == sum(
            line.count(CLAUDE_SKILL_DIR_TOKEN) for line in escaped
        ), row.path


def test_skill_dir_rewrite_escape_preserves_authoring_guidance() -> None:
    emissions = text_emissions()
    assert any(SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE in row.source for row in emissions)
    for row in emissions:
        escaped_lines = tuple(
            line
            for line in row.source.splitlines()
            if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE in line
        )
        if not escaped_lines:
            continue
        escaped_references = Counter(
            reference
            for line in escaped_lines
            for reference in skill_dir_path_references(line, CLAUDE_SKILL_DIR_TOKEN)
        )
        output_references = Counter(
            skill_dir_path_references(row.output, CLAUDE_SKILL_DIR_TOKEN)
        )
        assert SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in row.output, (
            row.target,
            row.path,
        )
        if row.target is Target.CLAUDE:
            assert row.output.count(CLAUDE_SKILL_DIR_TOKEN) == row.source.count(
                CLAUDE_SKILL_DIR_TOKEN
            ), (row.target, row.path)
            assert escaped_references <= output_references, (row.target, row.path)
        else:
            assert row.output.count(CLAUDE_SKILL_DIR_TOKEN) == sum(
                line.count(CLAUDE_SKILL_DIR_TOKEN) for line in escaped_lines
            ), (row.target, row.path)
            assert escaped_references == output_references, (row.target, row.path)


def test_codex_skill_frontmatter_strips_claude_only_fields() -> None:
    emissions = text_emissions()
    for field in (
        ALLOWED_TOOLS_FIELD,
        ARGUMENT_HINT_FIELD,
        DISABLE_MODEL_INVOCATION_FIELD,
    ):
        assert any(field in frontmatter_field_names(row.source) for row in emissions), (
            field
        )
    for row in emissions:
        source_fields = frontmatter_field_names(row.source)
        output_fields = frontmatter_field_names(row.output)
        for field in (ALLOWED_TOOLS_FIELD, ARGUMENT_HINT_FIELD):
            assert (field in output_fields) == (field in source_fields), (
                row.target,
                row.path,
                field,
            )
        for field in CLAUDE_ONLY_FRONTMATTER_FIELDS:
            assert (field in output_fields) == (
                row.target is Target.CLAUDE and field in source_fields
            ), (row.target, row.path, field)
    for row in emitted_texts():
        if row.target is Target.CODEX:
            assert not frozenset(
                CLAUDE_ONLY_FRONTMATTER_FIELDS
            ) & frontmatter_field_names(row.text), row.path


def test_target_scoped_includes_emit_only_to_matching_tree() -> None:
    observations = scoped_include_observations()
    assert observations
    for observation in observations:
        assert not observation.inactive_text, observation.case
        for target, paths in observation.paths.items():
            assert (observation.case.expected_relative_path in paths) == (
                target is observation.case.target
            ), (observation.case, target)


def test_unescaped_path_rewrite_is_idempotent() -> None:
    for row in text_emissions():
        unescaped = "\n".join(
            line
            for line in row.source.splitlines()
            if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in line
        )
        once = rewrite_paths_for_target(unescaped, target=row.target)
        assert rewrite_paths_for_target(once, target=row.target) == once, (
            row.target,
            row.path,
        )


def test_frontmatter_strip_is_idempotent() -> None:
    for row in text_emissions():
        once = strip_frontmatter_fields(
            row.source, fields=CLAUDE_ONLY_FRONTMATTER_FIELDS
        )
        assert (
            strip_frontmatter_fields(once, fields=CLAUDE_ONLY_FRONTMATTER_FIELDS)
            == once
        ), row.path


def test_outputs_do_not_contain_execution_time_skill_content_injection() -> None:
    commands = execution_time_commands()
    assert commands
    for command in commands:
        assert contains_execution_time_skill_content_injection(
            f"{EXECUTION_TIME_INJECTION_START}{command}{EXECUTION_TIME_INJECTION_END}"
        ), command
        assert not contains_execution_time_skill_content_injection(command), command
    outputs = emitted_texts()
    assert outputs
    for row in outputs:
        assert not contains_execution_time_skill_content_injection(row.text), (
            row.target,
            row.path,
        )


def test_agent_capabilities_resolve_from_the_source_owned_registry() -> None:
    for target in Target:
        capability = agent_capability(target)
        assert capability.suffix.startswith("."), (
            f"{target.value} declares no native agent artifact suffix"
        )
        # Filename shape comes from the registry's namespace flag, not from
        # emission logic: a namespaced target keeps the bare stem, a flat one
        # takes the plugin slug as a prefix.
        for case in source_scenarios():
            slug = agent_slug(case.plugin, case.skill, capability=capability)
            assert slug == (
                case.skill
                if capability.namespaced
                else f"{case.plugin}{FLAT_AGENT_PLUGIN_SEPARATOR}{case.skill}"
            ), (target, case, slug)


def test_no_target_tree_carries_an_agent_artifact_it_cannot_read() -> None:
    foreign_suffixes = {
        target: {
            other.suffix
            for name, other in AGENT_CAPABILITY_REGISTRY.items()
            if name != target.value
        }
        - {agent_capability(target).suffix}
        for target in Target
    }
    for target in Target:
        capability = agent_capability(target)
        artifacts = agent_artifact_paths(target)
        assert artifacts, (
            f"{target.value} carries no agent artifacts, so this check would "
            "pass vacuously"
        )
        for path in artifacts:
            assert path.suffix == capability.suffix, (
                f"{target.value} carries {path}, whose suffix is not this "
                f"target's native agent format {capability.suffix}"
            )
            assert path.suffix not in foreign_suffixes[target], (
                f"{target.value} carries a foreign agent artifact: {path}"
            )


def test_no_agent_artifact_carries_another_targets_skill_dir_token() -> None:
    # Conversion emits a derived artifact, so it bypasses the rendered-text
    # corpus the skill-dir rewrite assertions draw from. Reading the committed
    # agent artifacts directly keeps the rewrite contract reachable for the
    # converted class instead of holding only where the corpus already looks.
    for target in Target:
        assert agent_artifact_paths(target), (
            f"{target.value} carries no agent artifacts, so this check would "
            "pass vacuously"
        )
        foreign_token = (
            CODEX_SKILL_DIR_TOKEN if target is Target.CLAUDE else CLAUDE_SKILL_DIR_TOKEN
        )
        for path, text in agent_artifact_texts(target).items():
            assert foreign_token not in text, (target, path)


def test_target_absent_tool_item_is_removed_without_reordering() -> None:
    stable_tools = tuple(sorted(READ_ONLY_TOOLS))
    for observation in optional_tool_emissions():
        target_name = RUNTIME_TOKEN_USE_SKILL_NAMES[observation.target.value]
        expected = (
            (stable_tools[0], target_name, *stable_tools[1:])
            if target_name is not None
            else stable_tools
        )
        assert observation.tools == expected
        assert ", ," not in observation.text
        assert ",\n---" not in observation.text
