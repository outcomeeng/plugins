"""Harness for runtime-parameterization evidence tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.agents import (
    CODEX_FAST_MODEL,
    CODEX_STANDARD_MODEL,
    CODEX_STRONG_MODEL,
)
from outcomeeng.distribution.build import (
    CONFIGURED_AGENT_TERM_NAMES,
    IMPLEMENTED,
    RUNTIME_TOKEN_REGISTRY,
    RuntimeTokenError,
    RuntimeTokenKind,
    build,
    resolve_runtime_token,
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

PLUGIN_NAME = "develop"
SKILL_NAME = "example-skill"
TOOL_KIND = "tool"
FILE_KIND = "file"
TERM_KIND = "term"
FIELD_KIND = "field"
GUIDE_CAPABILITY = "root_guide"
BOTH_RUNTIME_CAPABILITY = "ask_user"
CLAUDE_ONLY_CAPABILITY = "schedule_wakeup"
MISSING_CAPABILITY = "nonexistent"
UNKNOWN_CAPABILITY = "unknown_capability"
LIVE_FIELD_CAPABILITY = "configured_agent_prompt"
LIVE_TERM_CAPABILITY = "configured_agent"


def implementation_is_ready() -> bool:
    return IMPLEMENTED


def registry_token_renders_each_target_name() -> bool:
    _require_implemented()
    token_names = RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[BOTH_RUNTIME_CAPABILITY]
    bodies = _render_skill_bodies(
        f"Ask the user via {{{{! tool('{BOTH_RUNTIME_CAPABILITY}') !}}}} now.",
    )
    return _target_body_contains_only_target_names(bodies, token_names)


def file_kind_renders_guide_filename_per_target() -> bool:
    _require_implemented()
    guide_names = RUNTIME_TOKEN_REGISTRY[FILE_KIND].names[GUIDE_CAPABILITY]
    bodies = _render_skill_bodies(
        f"Read the guide at {{{{! file('{GUIDE_CAPABILITY}') !}}}} once per session.",
    )
    return _target_body_contains_only_target_names(bodies, guide_names)


def field_kind_renders_live_registry_name_per_target() -> bool:
    _require_implemented()
    field_names = RUNTIME_TOKEN_REGISTRY[FIELD_KIND].names[LIVE_FIELD_CAPABILITY]
    bodies = _render_skill_bodies(
        f"Configure the field {{{{! field('{LIVE_FIELD_CAPABILITY}') !}}}}.",
    )
    return _target_body_contains_only_target_names(bodies, field_names)


def term_kind_renders_live_registry_name_per_target() -> bool:
    _require_implemented()
    term_names = RUNTIME_TOKEN_REGISTRY[TERM_KIND].names[LIVE_TERM_CAPABILITY]
    bodies = _render_skill_bodies(
        f"Configure the {{{{! term('{LIVE_TERM_CAPABILITY}') !}}}}.",
    )
    return _target_body_contains_only_target_names(bodies, term_names)


def runtime_explicit_token_renders_named_runtime_on_every_target() -> bool:
    _require_implemented()
    claude_name = RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[BOTH_RUNTIME_CAPABILITY][
        "claude"
    ]
    bodies = _render_skill_bodies(
        f"On Claude this is {{{{! tool('{BOTH_RUNTIME_CAPABILITY}', 'claude') !}}}}.",
    )
    return all(claude_name in body for body in bodies.values())


def token_for_capability_absent_on_target_fails() -> bool:
    _require_implemented()
    names = RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[CLAUDE_ONLY_CAPABILITY]
    return "codex" not in names and _raises_runtime_token_error(
        lambda: _render_skill_bodies(
            f"Wait via {{{{! tool('{CLAUDE_ONLY_CAPABILITY}') !}}}}.",
        )
    )


def conditional_renders_absent_capability_only_where_present() -> bool:
    _require_implemented()
    claude_name = RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[CLAUDE_ONLY_CAPABILITY][
        "claude"
    ]
    bodies = _render_skill_bodies(
        "{!% if target == 'claude' %!}"
        f"Wait via {{{{! tool('{CLAUDE_ONLY_CAPABILITY}') !}}}}."
        "{!% endif %!}",
    )
    return (
        claude_name in bodies[Target.CLAUDE] and claude_name not in bodies[Target.CODEX]
    )


def registry_is_keyed_by_kind_with_explicit_guard_enforcement() -> bool:
    _require_implemented()
    return (
        set(RUNTIME_TOKEN_REGISTRY) == {TOOL_KIND, FIELD_KIND, TERM_KIND, FILE_KIND}
        and all(
            isinstance(kind, RuntimeTokenKind)
            for kind in RUNTIME_TOKEN_REGISTRY.values()
        )
        and RUNTIME_TOKEN_REGISTRY[TOOL_KIND].lint_enforced is True
        and RUNTIME_TOKEN_REGISTRY[FIELD_KIND].lint_enforced is True
        and RUNTIME_TOKEN_REGISTRY[TERM_KIND].lint_enforced is False
        and RUNTIME_TOKEN_REGISTRY[FILE_KIND].lint_enforced is True
    )


def term_registry_names_configured_agent_concepts() -> bool:
    _require_implemented()
    terms = RUNTIME_TOKEN_REGISTRY[TERM_KIND].names
    return all(
        terms[capability] == names
        for capability, names in CONFIGURED_AGENT_TERM_NAMES.items()
    )


def configured_agent_model_terms_match_converter_models() -> bool:
    _require_implemented()
    terms = RUNTIME_TOKEN_REGISTRY[TERM_KIND].names
    return (
        terms["configured_agent_standard_model"]["codex"] == CODEX_STANDARD_MODEL
        and terms["configured_agent_fast_model"]["codex"] == CODEX_FAST_MODEL
        and terms["configured_agent_auditor_model"]["codex"] == CODEX_STANDARD_MODEL
        and terms["configured_agent_strong_models"]["codex"]
        == f"{CODEX_STRONG_MODEL} or {CODEX_STANDARD_MODEL}"
        and terms["configured_agent_fast_or_standard_models"]["codex"]
        == f"{CODEX_FAST_MODEL} or {CODEX_STANDARD_MODEL}"
    )


def resolve_renders_each_kind_from_its_own_sub_registry() -> bool:
    _require_implemented()
    return all(
        resolve_runtime_token(case.kind, case.capability, case.runtime)
        == RUNTIME_TOKEN_REGISTRY[case.kind].names[case.capability][case.runtime]
        for case in runtime_token_resolver_cases()
    )


def resolve_fails_on_unknown_kind_capability_or_runtime() -> bool:
    _require_implemented()
    registry = {
        TOOL_KIND: RuntimeTokenKind(
            lint_enforced=True,
            names={
                BOTH_RUNTIME_CAPABILITY: {
                    "claude": RUNTIME_TOKEN_REGISTRY[TOOL_KIND].names[
                        BOTH_RUNTIME_CAPABILITY
                    ]["claude"],
                },
            },
        ),
    }
    return (
        _raises_runtime_token_error(
            lambda: resolve_runtime_token(
                FIELD_KIND,
                BOTH_RUNTIME_CAPABILITY,
                "claude",
                registry=registry,
            )
        )
        and _raises_runtime_token_error(
            lambda: resolve_runtime_token(
                TOOL_KIND,
                UNKNOWN_CAPABILITY,
                "claude",
                registry=registry,
            )
        )
        and _raises_runtime_token_error(
            lambda: resolve_runtime_token(
                TOOL_KIND,
                BOTH_RUNTIME_CAPABILITY,
                "codex",
                registry=registry,
            )
        )
    )


def field_global_is_wired_to_the_resolver() -> bool:
    _require_implemented()
    return _kind_global_is_wired_to_the_resolver(FIELD_KIND)


def term_global_is_wired_to_the_resolver() -> bool:
    _require_implemented()
    return _kind_global_is_wired_to_the_resolver(TERM_KIND)


def _require_implemented() -> None:
    if not implementation_is_ready():
        msg = "outcomeeng.distribution.build is not implemented"
        raise AssertionError(msg)


def _render_skill_bodies(body: str) -> dict[Target, str]:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        builder = SrcTreeBuilder(tmp_path)
        builder.add_plugin(PLUGIN_NAME, skills={SKILL_NAME: _skill_with(body)})
        build(builder.src_root, tmp_path / "dist")
        return {
            target: (
                tmp_path
                / "dist"
                / target.value
                / PLUGIN_NAME
                / "skills"
                / SKILL_NAME
                / "SKILL.md"
            ).read_text()
            for target in Target
        }


def _skill_with(body: str) -> str:
    return f"---\nname: {SKILL_NAME}\ndescription: Example skill.\n---\n\n{body}\n"


def _target_body_contains_only_target_names(
    bodies: dict[Target, str],
    names: dict[str, str],
) -> bool:
    claude_name = names["claude"]
    codex_name = names["codex"]
    claude_body = bodies[Target.CLAUDE]
    codex_body = bodies[Target.CODEX]
    return (
        claude_name in claude_body
        and codex_name in codex_body
        and codex_name not in claude_body
        and claude_name not in codex_body
    )


def _raises_runtime_token_error(call: Callable[[], object]) -> bool:
    try:
        call()
    except RuntimeTokenError:
        return True
    return False


def _kind_global_is_wired_to_the_resolver(kind: str) -> bool:
    return _raises_runtime_token_error(
        lambda: _render_skill_bodies(f"{{{{! {kind}('{MISSING_CAPABILITY}') !}}}}")
    )
