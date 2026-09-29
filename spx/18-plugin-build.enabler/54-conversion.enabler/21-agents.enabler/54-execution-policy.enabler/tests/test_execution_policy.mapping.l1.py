"""Mapping evidence for converted Codex execution policy."""

from __future__ import annotations

from outcomeeng.distribution.agents import (
    ALL_TOOLS_SENTINEL,
    CODEX_PERMISSION_MODE_GUIDANCE_TEMPLATE,
    PERMISSION_MODE_LIMITATION,
    PERMISSION_MODE_MAPPINGS,
    READ_ONLY_SANDBOX_MODE,
    READ_ONLY_TOOLS,
    SANDBOX_MODE_FIELD,
    SCRIPT_CAPABLE_TOOLS,
    TOOLS_GUIDANCE_LIMITATION,
    WEB_CAPABLE_TOOLS,
    WEB_SEARCH_DISABLED,
    WRITE_CAPABLE_TOOLS,
    convert_agent,
    infer_sandbox_mode,
    map_permission_mode,
    map_web_search,
)
from outcomeeng_testing.harnesses.agent_conversion import (
    converted_instruction_value,
    source_agent,
)


def test_permission_modes_map_to_codex_sandbox_or_manual_review() -> None:
    supported = tuple(
        (source, sandbox_mode)
        for source, sandbox_mode in PERMISSION_MODE_MAPPINGS.items()
        if sandbox_mode is not None
    )
    unsupported = tuple(
        source
        for source, sandbox_mode in PERMISSION_MODE_MAPPINGS.items()
        if sandbox_mode is None
    )

    assert supported
    assert unsupported
    for source, sandbox_mode in supported:
        converted = convert_agent(source_agent(permission_mode=source))
        instructions = converted_instruction_value(converted)

        assert map_permission_mode(source) == sandbox_mode
        assert converted.values[SANDBOX_MODE_FIELD] == sandbox_mode
        assert PERMISSION_MODE_LIMITATION not in instructions
    for source in unsupported:
        converted = convert_agent(
            source_agent(permission_mode=source, tools=tuple(sorted(READ_ONLY_TOOLS)))
        )
        instructions = converted_instruction_value(converted)

        assert map_permission_mode(source) is None
        assert SANDBOX_MODE_FIELD not in converted.values
        assert (
            CODEX_PERMISSION_MODE_GUIDANCE_TEMPLATE.format(permission_mode=source)
            in instructions
        )


def test_explicit_unmapped_permission_mode_blocks_read_only_inference() -> None:
    unsupported = tuple(
        source
        for source, sandbox_mode in PERMISSION_MODE_MAPPINGS.items()
        if sandbox_mode is None
    )

    assert unsupported
    for source in unsupported:
        assert infer_sandbox_mode(tuple(sorted(READ_ONLY_TOOLS)), source) is None


def test_single_tool_allowlists_map_web_search_by_web_capability() -> None:
    tools = tuple(
        sorted(
            READ_ONLY_TOOLS
            | SCRIPT_CAPABLE_TOOLS
            | WEB_CAPABLE_TOOLS
            | WRITE_CAPABLE_TOOLS
        )
    )

    assert tools
    for tool in tools:
        expected = None if tool in WEB_CAPABLE_TOOLS else WEB_SEARCH_DISABLED
        assert map_web_search((tool,)) == expected


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


def test_single_tool_allowlists_map_sandbox_by_capability_class() -> None:
    read_only_capable = tuple(sorted(READ_ONLY_TOOLS | WEB_CAPABLE_TOOLS))
    unrestricted = tuple(sorted(SCRIPT_CAPABLE_TOOLS | WRITE_CAPABLE_TOOLS))

    assert read_only_capable
    assert unrestricted
    for tool in read_only_capable:
        assert infer_sandbox_mode((tool,), None) == READ_ONLY_SANDBOX_MODE
    for tool in unrestricted:
        assert infer_sandbox_mode((tool,), None) is None
        assert (
            infer_sandbox_mode(tuple(sorted({*read_only_capable, tool})), None) is None
        )


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


def test_write_capable_tool_allowlist_converts_to_manual_review_guidance() -> None:
    tools = tuple(sorted(WRITE_CAPABLE_TOOLS))
    converted = convert_agent(source_agent(tools=tools))
    instructions = converted_instruction_value(converted)

    assert tools
    assert SANDBOX_MODE_FIELD not in converted.values
    assert all(tool in instructions for tool in tools)
    assert TOOLS_GUIDANCE_LIMITATION in instructions
