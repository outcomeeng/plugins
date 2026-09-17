"""Compliance evidence for runtime-token parameterization."""

from __future__ import annotations

import pytest

from outcomeeng.distribution.agents import AGENT_TOOLS_FIELD, READ_ONLY_TOOLS
from outcomeeng.distribution.build import RuntimeTokenError, render_text
from outcomeeng.distribution.contracts import (
    RUNTIME_TOKEN_TOOL_KIND,
    RUNTIME_TOKEN_USE_SKILL_CAPABILITY,
    RUNTIME_TOKEN_USE_SKILL_NAMES,
    Target,
    format_runtime_token,
)
from outcomeeng.distribution.profiles import PROFILE_FIELD
from outcomeeng.validation.skill_frontmatter import ALLOWED_TOOLS_FIELD

from outcomeeng_testing.harnesses.runtime_parameterization import (
    build_fails_on_unknown_kind_capability_or_runtime,
    conditional_renders_absent_capability_only_where_present,
    field_kind_renders_live_registry_name_per_target,
    file_kind_renders_guide_filename_per_target,
    registry_backed_render_rejects_missing_injected_target_name,
    registry_contract_drives_render_path,
    registry_guard_contract_rejects_mismatched_enforcement,
    registry_is_keyed_by_kind_with_explicit_guard_enforcement,
    registry_token_renders_each_target_name,
    runtime_explicit_token_rejects_unavailable_or_missing_runtime,
    runtime_explicit_token_renders_named_runtime_on_every_target,
    term_kind_renders_live_registry_name_per_target,
    optional_tool_frontmatter_observations,
)


def test_registry_token_renders_each_target_name() -> None:
    assert registry_token_renders_each_target_name()


def test_registry_contract_drives_render_path() -> None:
    assert registry_contract_drives_render_path()


def test_registry_backed_render_rejects_missing_injected_target_name() -> None:
    assert registry_backed_render_rejects_missing_injected_target_name()


def test_file_kind_renders_guide_filename_per_target() -> None:
    assert file_kind_renders_guide_filename_per_target()


def test_field_kind_renders_live_registry_name_per_target() -> None:
    assert field_kind_renders_live_registry_name_per_target()


def test_term_kind_renders_live_registry_name_per_target() -> None:
    assert term_kind_renders_live_registry_name_per_target()


def test_runtime_explicit_token_renders_named_runtime_on_every_target() -> None:
    assert runtime_explicit_token_renders_named_runtime_on_every_target()


def test_runtime_explicit_token_rejects_unavailable_or_missing_runtime() -> None:
    assert runtime_explicit_token_rejects_unavailable_or_missing_runtime()


def test_build_fails_on_unknown_kind_capability_or_runtime() -> None:
    assert build_fails_on_unknown_kind_capability_or_runtime()


def test_conditional_renders_absent_capability_only_where_present() -> None:
    assert conditional_renders_absent_capability_only_where_present()


def test_registry_keyed_by_kind_with_explicit_guard_enforcement() -> None:
    assert registry_is_keyed_by_kind_with_explicit_guard_enforcement()


def test_registry_guard_contract_rejects_mismatched_enforcement() -> None:
    assert registry_guard_contract_rejects_mismatched_enforcement()


@pytest.mark.parametrize("field", (ALLOWED_TOOLS_FIELD, AGENT_TOOLS_FIELD))
def test_target_absent_tool_is_omitted_from_list_valued_frontmatter(
    field: str,
) -> None:
    stable_tools = tuple(sorted(READ_ONLY_TOOLS))
    for observation in optional_tool_frontmatter_observations(field):
        target_name = RUNTIME_TOKEN_USE_SKILL_NAMES[observation.target.value]
        expected = (
            (stable_tools[0], target_name, *stable_tools[1:])
            if target_name is not None
            else stable_tools
        )
        assert observation.tools == expected
        assert ", ," not in observation.rendered
        assert ",\n---" not in observation.rendered


def test_target_absent_tool_fails_outside_recognized_frontmatter_item() -> None:
    token = format_runtime_token(
        RUNTIME_TOKEN_TOOL_KIND,
        RUNTIME_TOKEN_USE_SKILL_CAPABILITY,
    )
    with pytest.raises(RuntimeTokenError):
        render_text(token, variables={"target": Target.CODEX.value})
    with pytest.raises(RuntimeTokenError):
        render_text(
            f"---\n{PROFILE_FIELD}: {token}\n---\n",
            variables={"target": Target.CODEX.value},
        )
