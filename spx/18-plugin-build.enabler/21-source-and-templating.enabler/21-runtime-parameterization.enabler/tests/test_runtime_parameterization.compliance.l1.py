"""Compliance evidence for runtime-token parameterization."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    RUNTIME_TOKEN_REGISTRY,
    IMPLEMENTED,
    RuntimeTokenError,
    Target,
    build,
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


# The guard's enforcement is scoped to the develop plugin for the pilot.
PLUGIN_NAME = "develop"
SKILL_NAME = "example-skill"

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
    claude_name = RUNTIME_TOKEN_REGISTRY[BOTH_RUNTIME_CAPABILITY]["claude"]
    codex_name = RUNTIME_TOKEN_REGISTRY[BOTH_RUNTIME_CAPABILITY]["codex"]

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


def test_runtime_explicit_token_renders_named_runtime_on_every_target(
    tmp_path: Path,
) -> None:
    claude_name = RUNTIME_TOKEN_REGISTRY[BOTH_RUNTIME_CAPABILITY]["claude"]

    reader = _build_one_skill(
        tmp_path,
        f"On Claude this is {{{{! tool('{BOTH_RUNTIME_CAPABILITY}', 'claude') !}}}}.",
    )

    for target in Target:
        body = reader.read_skill_body(PLUGIN_NAME, SKILL_NAME, target=target)
        assert claude_name in body


def test_guard_fails_on_raw_runtime_token_in_develop(tmp_path: Path) -> None:
    raw_token = RUNTIME_TOKEN_REGISTRY[BOTH_RUNTIME_CAPABILITY]["claude"]

    with pytest.raises(RuntimeTokenError):
        _build_one_skill(tmp_path, f"Ask the user via {raw_token} now.")


def test_token_for_capability_absent_on_target_fails(tmp_path: Path) -> None:
    assert "codex" not in RUNTIME_TOKEN_REGISTRY[CLAUDE_ONLY_CAPABILITY]

    with pytest.raises(RuntimeTokenError):
        _build_one_skill(
            tmp_path,
            f"Wait via {{{{! tool('{CLAUDE_ONLY_CAPABILITY}') !}}}}.",
        )


def test_conditional_renders_absent_capability_only_where_present(
    tmp_path: Path,
) -> None:
    claude_name = RUNTIME_TOKEN_REGISTRY[CLAUDE_ONLY_CAPABILITY]["claude"]

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
