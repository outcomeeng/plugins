"""Mapping evidence for converted Codex execution policy."""

from __future__ import annotations

from outcomeeng.distribution.agents import (
    ALL_TOOLS_SENTINEL,
    PERMISSION_MODE_LIMITATION,
    PERMISSION_MODE_MAPPINGS,
    READ_ONLY_SANDBOX_MODE,
    READ_ONLY_TOOLS,
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
    EXPECTED_PERMISSION_MODE_CORRESPONDENCE,
    EXPECTED_TOOL_CLASSIFICATION,
    WRITER_BODY,
    WRITER_DESCRIPTION,
    WRITER_SOURCE_PATH,
    converted_instruction_value,
    source_agent,
)


def test_permission_modes_map_to_codex_sandbox_or_manual_review() -> None:
    assert {source for source, _ in EXPECTED_PERMISSION_MODE_CORRESPONDENCE} == set(
        PERMISSION_MODE_MAPPINGS
    )
    for source, expected in EXPECTED_PERMISSION_MODE_CORRESPONDENCE:
        assert map_permission_mode(source) == expected


def test_supported_permission_mode_reaches_converted_codex_sandbox_mode() -> None:
    for source, expected in EXPECTED_PERMISSION_MODE_CORRESPONDENCE:
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
    for source, expected in EXPECTED_PERMISSION_MODE_CORRESPONDENCE:
        if expected is not None:
            continue
        assert infer_sandbox_mode(tuple(sorted(READ_ONLY_TOOLS)), source) is None


def test_unmapped_permission_mode_converts_to_manual_review_guidance() -> None:
    for source, expected in EXPECTED_PERMISSION_MODE_CORRESPONDENCE:
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


def test_tool_classification_matches_the_hand_authored_correspondence() -> None:
    production_by_class = {
        "read-only": READ_ONLY_TOOLS,
        "script-capable": SCRIPT_CAPABLE_TOOLS,
        "web-capable": WEB_CAPABLE_TOOLS,
        "write-capable": WRITE_CAPABLE_TOOLS,
    }
    for tool, capability in EXPECTED_TOOL_CLASSIFICATION:
        assert tool in production_by_class[capability], (tool, capability)
    assert {tool for tool, _ in EXPECTED_TOOL_CLASSIFICATION} == (
        READ_ONLY_TOOLS | SCRIPT_CAPABLE_TOOLS | WEB_CAPABLE_TOOLS | WRITE_CAPABLE_TOOLS
    )
