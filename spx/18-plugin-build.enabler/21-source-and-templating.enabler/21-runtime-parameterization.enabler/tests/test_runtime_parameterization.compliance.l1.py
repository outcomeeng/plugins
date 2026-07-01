"""Compliance evidence for runtime-token parameterization."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.build import (
    RUNTIME_TOKEN_REGISTRY,
    IMPLEMENTED,
    RuntimeTokenError,
    RuntimeTokenKind,
    build,
    resolve_runtime_token,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


PLUGIN_NAME = "develop"
SKILL_NAME = "example-skill"

# The unique-token kind that carries the seeded tool capabilities.
TOOL_KIND = "tool"

# The unique-token kind that carries per-runtime filenames, and the capability for
# the root agent guide that diverges across both runtimes.
FILE_KIND = "file"
GUIDE_CAPABILITY = "root_guide"

# A capability that diverges across both runtimes, and one that exists for Claude
# with no Codex equivalent — both drawn from the source-owned registry so the test
# carries no copied name literals.
BOTH_RUNTIME_CAPABILITY = "ask_user"
CLAUDE_ONLY_CAPABILITY = "schedule_wakeup"


def _skill_with(body: str) -> str:
    return f"---\nname: {SKILL_NAME}\ndescription: Example skill.\n---\n\n{body}\n"


def _build_one_skill(tmp_path: Path, body: str) -> DistTreeReader:
    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: _skill_with(body)})
    build(builder.src_root, tmp_path / "dist")
    return DistTreeReader(tmp_path)


def test_registry_token_renders_each_target_name(tmp_path: Path) -> None:
    tool_names = RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[BOTH_RUNTIME_CAPABILITY]
    claude_name = tool_names["claude"]
    codex_name = tool_names["codex"]

    reader = _build_one_skill(
        tmp_path,
        f"Ask the user via {{{{! tool('{BOTH_RUNTIME_CAPABILITY}') !}}}} now.",
    )

    claude_body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=Target.CLAUDE)
    codex_body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=Target.CODEX)
    assert claude_name in claude_body
    assert codex_name in codex_body
    assert codex_name not in claude_body
    assert claude_name not in codex_body


def test_file_kind_renders_guide_filename_per_target(tmp_path: Path) -> None:
    guide_names = RUNTIME_TOKEN_REGISTRY[FILE_KIND].names[GUIDE_CAPABILITY]
    claude_name = guide_names["claude"]
    codex_name = guide_names["codex"]

    reader = _build_one_skill(
        tmp_path,
        f"Read the guide at {{{{! file('{GUIDE_CAPABILITY}') !}}}} once per session.",
    )

    claude_body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=Target.CLAUDE)
    codex_body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=Target.CODEX)
    assert claude_name in claude_body
    assert codex_name in codex_body
    assert codex_name not in claude_body
    assert claude_name not in codex_body


def test_runtime_explicit_token_renders_named_runtime_on_every_target(
    tmp_path: Path,
) -> None:
    claude_name = RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[BOTH_RUNTIME_CAPABILITY][
        "claude"
    ]

    reader = _build_one_skill(
        tmp_path,
        f"On Claude this is {{{{! tool('{BOTH_RUNTIME_CAPABILITY}', 'claude') !}}}}.",
    )

    for target in Target:
        body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=target)
        assert claude_name in body


def test_token_for_capability_absent_on_target_fails(tmp_path: Path) -> None:
    assert (
        "codex" not in RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[CLAUDE_ONLY_CAPABILITY]
    )

    with pytest.raises(RuntimeTokenError):
        _build_one_skill(
            tmp_path,
            f"Wait via {{{{! tool('{CLAUDE_ONLY_CAPABILITY}') !}}}}.",
        )


def test_conditional_renders_absent_capability_only_where_present(
    tmp_path: Path,
) -> None:
    claude_name = RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[CLAUDE_ONLY_CAPABILITY][
        "claude"
    ]

    reader = _build_one_skill(
        tmp_path,
        "{!% if target == 'claude' %!}"
        f"Wait via {{{{! tool('{CLAUDE_ONLY_CAPABILITY}') !}}}}."
        "{!% endif %!}",
    )

    claude_body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=Target.CLAUDE)
    codex_body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=Target.CODEX)
    assert claude_name in claude_body
    assert claude_name not in codex_body


def test_registry_keyed_by_kind_with_explicit_guard_enforcement() -> None:
    # The registry is keyed by token kind; each kind is a RuntimeTokenKind that
    # declares whether the source-layer guard enforces its names. tool, field, and
    # file are unique-token kinds the guard enforces; term concept terms are common
    # words it excludes (review covers them).
    assert set(RUNTIME_TOKEN_REGISTRY) == {"tool", "field", "term", "file"}
    assert all(
        isinstance(kind, RuntimeTokenKind) for kind in RUNTIME_TOKEN_REGISTRY.values()
    )
    assert RUNTIME_TOKEN_REGISTRY["tool"].lint_enforced is True
    assert RUNTIME_TOKEN_REGISTRY["field"].lint_enforced is True
    assert RUNTIME_TOKEN_REGISTRY["term"].lint_enforced is False
    assert RUNTIME_TOKEN_REGISTRY["file"].lint_enforced is True


def test_resolve_renders_each_kind_from_its_own_sub_registry() -> None:
    # One resolution path serves every kind: the kind selects the sub-registry,
    # then capability and runtime select the name. Built from the source-owned
    # RuntimeTokenKind so field() and term() render exactly as tool() does. The
    # expected name is read back from the same controlled registry (input-derived
    # oracle), not asserted against the live (empty) field/term kinds.
    registry = {
        "tool": RuntimeTokenKind(
            lint_enforced=True,
            names={
                "ask_user": {"claude": "AskUserQuestion", "codex": "request_user_input"}
            },
        ),
        "field": RuntimeTokenKind(
            lint_enforced=True,
            names={"tools_list": {"claude": "allowed-tools", "codex": "tools"}},
        ),
        "term": RuntimeTokenKind(
            lint_enforced=False,
            names={"research_agent": {"claude": "subagent", "codex": "agent"}},
        ),
    }
    for kind, capability, runtime in (
        ("tool", "ask_user", "codex"),
        ("field", "tools_list", "claude"),
        ("term", "research_agent", "codex"),
    ):
        expected = registry[kind].names[capability][runtime]
        assert (
            resolve_runtime_token(kind, capability, runtime, registry=registry)
            == expected
        )


def test_resolve_fails_on_unknown_kind_capability_or_runtime() -> None:
    registry = {
        "tool": RuntimeTokenKind(
            lint_enforced=True, names={"ask_user": {"claude": "AskUserQuestion"}}
        ),
    }
    with pytest.raises(RuntimeTokenError):
        resolve_runtime_token("field", "ask_user", "claude", registry=registry)
    with pytest.raises(RuntimeTokenError):
        resolve_runtime_token("tool", "unknown_capability", "claude", registry=registry)
    with pytest.raises(RuntimeTokenError):
        resolve_runtime_token("tool", "ask_user", "codex", registry=registry)


@pytest.mark.parametrize("kind", ["field", "term"])
def test_kind_global_is_wired_to_the_resolver(tmp_path: Path, kind: str) -> None:
    # Every registry kind is exposed as a build template global. A field()/term()
    # token for a capability the kind has no name for fails through the resolver
    # (RuntimeTokenError) — an unregistered global would instead raise Jinja's
    # UndefinedError, so this proves the global exists and reaches resolution.
    with pytest.raises(RuntimeTokenError):
        _build_one_skill(tmp_path, f"{{{{! {kind}('nonexistent') !}}}}")
