"""Mapping evidence for agent model, effort, and permission conversion."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.agents import (
    ALL_TOOLS_SENTINEL,
    ClaudeAgent,
    EFFORT_MAPPINGS,
    INHERIT_MODEL_VALUE,
    MODEL_MAPPINGS,
    MODEL_PREFIX_EXAMPLE_SUFFIX,
    PERMISSION_MODE_MAPPINGS,
    READ_ONLY_SANDBOX_MODE,
    READ_ONLY_TOOLS,
    UNMAPPED_PERMISSION_MODE_EXAMPLE,
    WEB_CAPABLE_TOOLS,
    WEB_SEARCH_DISABLED,
    WRITE_CAPABLE_TOOLS,
    convert_agent,
    infer_sandbox_mode,
    map_effort,
    map_model,
    map_permission_mode,
    map_web_search,
)


MODEL_PREFIX_CASES = tuple(
    (source_prefix, target_model) for source_prefix, target_model in MODEL_MAPPINGS
) + tuple(
    (f"{source_prefix}{MODEL_PREFIX_EXAMPLE_SUFFIX}", target_model)
    for source_prefix, target_model in MODEL_MAPPINGS
    if source_prefix.startswith("claude-")
)
MODEL_CASES = (*MODEL_PREFIX_CASES, (INHERIT_MODEL_VALUE, None))
EFFORT_CASES = tuple(EFFORT_MAPPINGS.items())
PERMISSION_MODE_CASES = (
    *tuple(PERMISSION_MODE_MAPPINGS.items()),
    (UNMAPPED_PERMISSION_MODE_EXAMPLE, None),
)


@pytest.mark.parametrize(
    ("source", "expected"),
    MODEL_CASES,
)
def test_claude_model_maps_to_codex_model(
    source: str,
    expected: str | None,
) -> None:
    assert map_model(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    EFFORT_CASES,
)
def test_claude_effort_maps_to_codex_reasoning_effort(
    source: str,
    expected: str,
) -> None:
    assert map_effort(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    EFFORT_CASES,
)
def test_claude_effort_reaches_converted_codex_reasoning_effort(
    source: str,
    expected: str,
) -> None:
    converted = convert_agent(
        ClaudeAgent(
            source_path=Path("reviewer.md"),
            name="reviewer",
            description="Review.",
            body="Review.",
            effort=source,
        )
    )

    assert converted.values["model_reasoning_effort"] == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    PERMISSION_MODE_CASES,
)
def test_permission_mode_maps_when_codex_has_supported_equivalent(
    source: str,
    expected: str | None,
) -> None:
    assert map_permission_mode(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    tuple(PERMISSION_MODE_MAPPINGS.items()),
)
def test_supported_permission_mode_reaches_converted_codex_sandbox_mode(
    source: str,
    expected: str,
) -> None:
    converted = convert_agent(
        ClaudeAgent(
            source_path=Path("reviewer.md"),
            name="reviewer",
            description="Review.",
            body="Review.",
            permission_mode=source,
        )
    )

    assert converted.values["sandbox_mode"] == expected


def test_tool_allowlist_without_web_tool_disables_web_search() -> None:
    assert map_web_search(tuple(READ_ONLY_TOOLS)) == WEB_SEARCH_DISABLED


def test_explicit_empty_tool_allowlist_disables_web_search() -> None:
    assert map_web_search(()) == WEB_SEARCH_DISABLED


def test_missing_tool_allowlist_leaves_web_search_to_runtime_default() -> None:
    assert map_web_search((), tools_declared=False) is None


def test_tool_allowlist_with_web_tool_leaves_web_search_to_runtime_default() -> None:
    assert map_web_search(tuple(WEB_CAPABLE_TOOLS)) is None


def test_all_tools_sentinel_leaves_web_search_to_runtime_default() -> None:
    assert map_web_search((ALL_TOOLS_SENTINEL,)) is None


def test_read_only_tool_allowlist_infers_read_only_sandbox() -> None:
    assert infer_sandbox_mode(tuple(READ_ONLY_TOOLS), None) == READ_ONLY_SANDBOX_MODE


def test_read_only_web_tool_allowlist_infers_read_only_sandbox() -> None:
    read_only_web_tools = tuple(READ_ONLY_TOOLS | WEB_CAPABLE_TOOLS)

    assert infer_sandbox_mode(read_only_web_tools, None) == READ_ONLY_SANDBOX_MODE


def test_all_tools_sentinel_leaves_sandbox_to_runtime_default() -> None:
    assert infer_sandbox_mode((ALL_TOOLS_SENTINEL,), None) is None


def test_explicit_empty_tool_allowlist_infers_read_only_sandbox() -> None:
    assert infer_sandbox_mode((), None) == READ_ONLY_SANDBOX_MODE


def test_missing_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert infer_sandbox_mode((), None, tools_declared=False) is None


def test_write_capable_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert infer_sandbox_mode(tuple(WRITE_CAPABLE_TOOLS), None) is None


def test_explicit_unmapped_permission_mode_blocks_read_only_inference() -> None:
    assert (
        infer_sandbox_mode(tuple(READ_ONLY_TOOLS), UNMAPPED_PERMISSION_MODE_EXAMPLE)
        is None
    )


def test_unmapped_permission_mode_converts_to_manual_review_guidance() -> None:
    converted = convert_agent(
        ClaudeAgent(
            source_path=Path("reviewer.md"),
            name="reviewer",
            description="Review.",
            body="Review.",
            permission_mode=UNMAPPED_PERMISSION_MODE_EXAMPLE,
            tools=tuple(READ_ONLY_TOOLS),
            tools_declared=True,
        )
    )

    instructions = converted.values["developer_instructions"].value

    assert "sandbox_mode" not in converted.values
    assert f"permissionMode: {UNMAPPED_PERMISSION_MODE_EXAMPLE}" in instructions
    assert "manual-review guidance" in instructions


def test_write_capable_tool_allowlist_converts_to_manual_review_guidance() -> None:
    converted = convert_agent(
        ClaudeAgent(
            source_path=Path("writer.md"),
            name="writer",
            description="Write.",
            body="Write.",
            tools=tuple(sorted(WRITE_CAPABLE_TOOLS)),
            tools_declared=True,
        )
    )

    instructions = converted.values["developer_instructions"].value

    assert "sandbox_mode" not in converted.values
    assert "command-level meanings" in instructions
    assert "manual-review guidance" in instructions
