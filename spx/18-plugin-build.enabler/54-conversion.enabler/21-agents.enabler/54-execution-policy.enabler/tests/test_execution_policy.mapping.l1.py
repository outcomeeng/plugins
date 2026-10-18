"""Mapping evidence for converted Codex execution policy."""

from __future__ import annotations

from outcomeeng.distribution.agents import (
    ALL_TOOLS_SENTINEL,
    MANUAL_REVIEW_GUIDANCE_OPEN,
    PERMISSION_MODE_LIMITATION,
    PERMISSION_MODE_MAPPINGS,
    READ_ONLY_SANDBOX_MODE,
    READ_ONLY_TOOLS,
    SCRIPT_CAPABLE_TOOLS,
    SOURCE_TOOL_UNIVERSE,
    TOOLS_GUIDANCE_LIMITATION,
    WEB_CAPABLE_TOOLS,
    WEB_SEARCH_DISABLED,
    WRITE_CAPABLE_TOOLS,
    convert_agent,
    infer_sandbox_mode,
    map_permission_mode,
    map_web_search,
)
from outcomeeng_testing.generators.agent_conversion import every_tool_subset
from outcomeeng_testing.harnesses.agent_conversion import (
    WRITER_BODY,
    WRITER_DESCRIPTION,
    WRITER_SOURCE_PATH,
    converted_instruction_value,
    source_agent,
)


def test_permission_modes_map_to_codex_sandbox_or_manual_review() -> None:
    for source, expected in PERMISSION_MODE_MAPPINGS.items():
        assert map_permission_mode(source) == expected


def test_supported_permission_mode_reaches_converted_codex_sandbox_mode() -> None:
    for source, expected in PERMISSION_MODE_MAPPINGS.items():
        if expected is None:
            continue
        converted = convert_agent(source_agent(permission_mode=source))
        assert converted.values["sandbox_mode"] == expected


def test_tool_allowlist_without_web_tool_disables_web_search() -> None:
    assert map_web_search(tuple(sorted(READ_ONLY_TOOLS))) == WEB_SEARCH_DISABLED


def test_explicit_empty_tool_allowlist_disables_web_search() -> None:
    assert map_web_search(()) == WEB_SEARCH_DISABLED


def test_missing_tool_allowlist_leaves_web_search_to_runtime_default() -> None:
    assert map_web_search((), tools_declared=False) is None


def test_tool_allowlist_with_web_tool_leaves_web_search_to_runtime_default() -> None:
    assert map_web_search(tuple(sorted(WEB_CAPABLE_TOOLS))) is None


def test_all_tools_sentinel_leaves_web_search_to_runtime_default() -> None:
    assert map_web_search((ALL_TOOLS_SENTINEL,)) is None


def test_read_only_tool_allowlist_infers_read_only_sandbox() -> None:
    assert (
        infer_sandbox_mode(tuple(sorted(READ_ONLY_TOOLS)), None)
        == READ_ONLY_SANDBOX_MODE
    )


def test_read_only_web_tool_allowlist_infers_read_only_sandbox() -> None:
    assert (
        infer_sandbox_mode(tuple(sorted(READ_ONLY_TOOLS | WEB_CAPABLE_TOOLS)), None)
        == READ_ONLY_SANDBOX_MODE
    )


def test_web_capable_only_tool_allowlist_infers_read_only_sandbox() -> None:
    assert (
        infer_sandbox_mode(tuple(sorted(WEB_CAPABLE_TOOLS)), None)
        == READ_ONLY_SANDBOX_MODE
    )


def test_all_tools_sentinel_leaves_sandbox_to_runtime_default() -> None:
    assert infer_sandbox_mode((ALL_TOOLS_SENTINEL,), None) is None


def test_explicit_empty_tool_allowlist_infers_read_only_sandbox() -> None:
    assert infer_sandbox_mode((), None) == READ_ONLY_SANDBOX_MODE


def test_missing_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert infer_sandbox_mode((), None, tools_declared=False) is None


def test_write_capable_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert infer_sandbox_mode(tuple(sorted(WRITE_CAPABLE_TOOLS)), None) is None


def test_script_capable_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert infer_sandbox_mode(tuple(sorted(SCRIPT_CAPABLE_TOOLS)), None) is None


def test_explicit_unmapped_permission_mode_blocks_read_only_inference() -> None:
    for source, expected in PERMISSION_MODE_MAPPINGS.items():
        if expected is not None:
            continue
        assert infer_sandbox_mode(tuple(sorted(READ_ONLY_TOOLS)), source) is None


def test_unmapped_permission_mode_converts_to_manual_review_guidance() -> None:
    for source, expected in PERMISSION_MODE_MAPPINGS.items():
        if expected is not None:
            continue
        converted = convert_agent(
            source_agent(
                permission_mode=source,
                tools=tuple(sorted(READ_ONLY_TOOLS)),
                tools_declared=True,
            )
        )
        instructions = converted_instruction_value(converted)

        assert "sandbox_mode" not in converted.values
        assert f"permissionMode: {source}" in instructions
        assert PERMISSION_MODE_LIMITATION in instructions


def test_write_capable_tool_allowlist_converts_to_manual_review_guidance() -> None:
    tools = tuple(sorted(WRITE_CAPABLE_TOOLS))
    converted = convert_agent(
        source_agent(
            source_path=WRITER_SOURCE_PATH,
            name=WRITER_SOURCE_PATH.stem,
            description=WRITER_DESCRIPTION,
            body=WRITER_BODY,
            tools=tools,
            tools_declared=True,
        )
    )
    instructions = converted_instruction_value(converted)

    assert "sandbox_mode" not in converted.values
    assert all(tool in instructions for tool in tools)
    assert TOOLS_GUIDANCE_LIMITATION in instructions


def test_manual_guidance_names_exactly_the_tools_of_the_source_tool_set() -> None:
    for declared in every_tool_subset():
        converted = convert_agent(source_agent(tools=declared, tools_declared=True))
        instructions = converted_instruction_value(converted)
        if not declared:
            assert MANUAL_REVIEW_GUIDANCE_OPEN not in instructions, declared
            continue
        guidance = instructions.split(MANUAL_REVIEW_GUIDANCE_OPEN, 1)[1]

        for tool in sorted(SOURCE_TOOL_UNIVERSE):
            assert (f"`{tool}`" in guidance) == (tool in declared), (tool, declared)


def test_converted_web_search_follows_the_web_capability_of_every_tool_set() -> None:
    for declared in every_tool_subset():
        converted = convert_agent(source_agent(tools=declared, tools_declared=True))
        has_web_tool = any(tool in WEB_CAPABLE_TOOLS for tool in declared)

        assert converted.values.get("web_search") == (
            None if has_web_tool else WEB_SEARCH_DISABLED
        ), declared


def test_converted_sandbox_follows_the_read_only_capability_of_every_tool_set() -> None:
    read_only_or_web = READ_ONLY_TOOLS | WEB_CAPABLE_TOOLS
    for declared in every_tool_subset():
        converted = convert_agent(source_agent(tools=declared, tools_declared=True))
        is_read_only = all(tool in read_only_or_web for tool in declared)

        assert converted.values.get("sandbox_mode") == (
            READ_ONLY_SANDBOX_MODE if is_read_only else None
        ), declared
