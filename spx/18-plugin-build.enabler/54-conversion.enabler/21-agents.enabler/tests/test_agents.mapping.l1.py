"""Mapping evidence for agent model, effort, and permission conversion."""

from __future__ import annotations

import pytest

from outcomeeng.distribution.agents import map_effort, map_model, map_permission_mode


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("opus", "gpt-5.4"),
        ("claude-opus-4-1", "gpt-5.4"),
        ("sonnet", "gpt-5.4-mini"),
        ("claude-sonnet-4-5", "gpt-5.4-mini"),
        ("haiku", "gpt-5.4-mini"),
        ("claude-haiku-3-5", "gpt-5.4-mini"),
        ("inherit", None),
    ],
)
def test_claude_model_maps_to_codex_model(
    source: str,
    expected: str | None,
) -> None:
    assert map_model(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("low", "low"),
        ("medium", "medium"),
        ("high", "high"),
        ("max", "xhigh"),
    ],
)
def test_claude_effort_maps_to_codex_reasoning_effort(
    source: str,
    expected: str,
) -> None:
    assert map_effort(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("acceptEdits", "workspace-write"),
        ("readOnly", "read-only"),
        ("bypassPermissions", None),
    ],
)
def test_permission_mode_maps_when_codex_has_supported_equivalent(
    source: str,
    expected: str | None,
) -> None:
    assert map_permission_mode(source) == expected
