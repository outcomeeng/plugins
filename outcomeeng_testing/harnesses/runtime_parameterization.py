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
    BuildError,
    CONFIGURED_AGENT_TERM_NAMES,
    IMPLEMENTED,
    RUNTIME_TOKEN_ASK_USER_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_AUDITOR_MODEL_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_MODEL_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_OR_STANDARD_MODELS_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_STANDARD_MODEL_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_STRONG_MODELS_CAPABILITY,
    RUNTIME_TOKEN_FIELD_KIND,
    RUNTIME_TOKEN_FILE_KIND,
    RUNTIME_TOKEN_REGISTRY,
    RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY,
    RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY,
    RUNTIME_TOKEN_TERM_KIND,
    RUNTIME_TOKEN_TOOL_KIND,
    RuntimeTokenError,
    RuntimeTokenKind,
    build,
    render_text,
    resolve_runtime_token,
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.generators.source_and_templating import source_scenarios
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

SKILL_NAME = "example-skill"
UNKNOWN_TOKEN_KIND = "unknown_kind"
UNKNOWN_CAPABILITY = "unknown_capability"


def implementation_is_ready() -> bool:
    return IMPLEMENTED


def registry_token_renders_each_target_name() -> bool:
    _require_implemented()
    token_names = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TOOL_KIND].names[
        RUNTIME_TOKEN_ASK_USER_CAPABILITY
    ]
    bodies = _render_skill_bodies(
        "Ask the user via "
        f"{{{{! {RUNTIME_TOKEN_TOOL_KIND}('{RUNTIME_TOKEN_ASK_USER_CAPABILITY}') !}}}} "
        "now.",
    )
    return _target_body_contains_only_target_names(bodies, token_names)


def file_kind_renders_guide_filename_per_target() -> bool:
    _require_implemented()
    guide_names = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_FILE_KIND].names[
        RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY
    ]
    bodies = _render_skill_bodies(
        "Read the guide at "
        f"{{{{! {RUNTIME_TOKEN_FILE_KIND}('{RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY}') !}}}} "
        "once per session.",
    )
    return _target_body_contains_only_target_names(bodies, guide_names)


def field_kind_renders_live_registry_name_per_target() -> bool:
    _require_implemented()
    field_names = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_FIELD_KIND].names[
        RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY
    ]
    bodies = _render_skill_bodies(
        "Configure the field "
        f"{{{{! {RUNTIME_TOKEN_FIELD_KIND}('{RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY}') !}}}}.",
    )
    return _target_body_contains_only_target_names(bodies, field_names)


def term_kind_renders_live_registry_name_per_target() -> bool:
    _require_implemented()
    term_names = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TERM_KIND].names[
        RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY
    ]
    bodies = _render_skill_bodies(
        "Configure the "
        f"{{{{! {RUNTIME_TOKEN_TERM_KIND}('{RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY}') !}}}}.",
    )
    return _target_body_contains_only_target_names(bodies, term_names)


def runtime_explicit_token_renders_named_runtime_on_every_target() -> bool:
    _require_implemented()
    claude_name = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TOOL_KIND].names[
        RUNTIME_TOKEN_ASK_USER_CAPABILITY
    ][Target.CLAUDE.value]
    bodies = _render_skill_bodies(
        "On Claude this is "
        f"{{{{! {RUNTIME_TOKEN_TOOL_KIND}('{RUNTIME_TOKEN_ASK_USER_CAPABILITY}', '{Target.CLAUDE.value}') !}}}}.",
    )
    return all(claude_name in body for body in bodies.values())


def build_fails_on_unknown_kind_capability_or_runtime() -> bool:
    _require_implemented()
    return (
        _raises_build_error(
            lambda: _render_skill_bodies(
                f"{{{{! {UNKNOWN_TOKEN_KIND}('{RUNTIME_TOKEN_ASK_USER_CAPABILITY}') !}}}}"
            )
        )
        and _raises_build_error(
            lambda: _render_skill_bodies(
                f"{{{{! {RUNTIME_TOKEN_TOOL_KIND}('{UNKNOWN_CAPABILITY}') !}}}}"
            )
        )
        and _raises_build_error(
            lambda: _render_skill_bodies(
                f"{{{{! {RUNTIME_TOKEN_TOOL_KIND}('{RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY}') !}}}}"
            )
        )
    )


def conditional_renders_absent_capability_only_where_present() -> bool:
    _require_implemented()
    claude_name = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TOOL_KIND].names[
        RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY
    ][Target.CLAUDE.value]
    template = (
        f"{{!% if target == '{Target.CLAUDE.value}' %!}}"
        f"Wait via {{{{! {RUNTIME_TOKEN_TOOL_KIND}('{RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY}') !}}}}."
        "{!% endif %!}"
    )
    bodies = _render_skill_bodies(template)
    codex_rendered = render_text(
        template,
        variables={"target": Target.CODEX.value},
    )
    return (
        claude_name in bodies[Target.CLAUDE]
        and claude_name not in bodies[Target.CODEX]
        and codex_rendered == ""
    )


def _raises_build_error(call: Callable[[], object]) -> bool:
    try:
        call()
    except BuildError:
        return True
    return False


def registry_is_keyed_by_kind_with_explicit_guard_enforcement() -> bool:
    _require_implemented()
    return (
        set(RUNTIME_TOKEN_REGISTRY)
        == {
            RUNTIME_TOKEN_TOOL_KIND,
            RUNTIME_TOKEN_FIELD_KIND,
            RUNTIME_TOKEN_TERM_KIND,
            RUNTIME_TOKEN_FILE_KIND,
        }
        and all(
            isinstance(kind, RuntimeTokenKind)
            for kind in RUNTIME_TOKEN_REGISTRY.values()
        )
        and RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TOOL_KIND].lint_enforced is True
        and RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_FIELD_KIND].lint_enforced is True
        and RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TERM_KIND].lint_enforced is False
        and RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_FILE_KIND].lint_enforced is True
    )


def term_registry_names_configured_agent_concepts() -> bool:
    _require_implemented()
    terms = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TERM_KIND].names
    return all(
        terms[capability] == names
        for capability, names in CONFIGURED_AGENT_TERM_NAMES.items()
    )


def configured_agent_model_terms_match_converter_models() -> bool:
    _require_implemented()
    terms = RUNTIME_TOKEN_REGISTRY[RUNTIME_TOKEN_TERM_KIND].names
    return (
        terms[RUNTIME_TOKEN_CONFIGURED_AGENT_STANDARD_MODEL_CAPABILITY][
            Target.CODEX.value
        ]
        == CODEX_STANDARD_MODEL
        and terms[RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_MODEL_CAPABILITY][
            Target.CODEX.value
        ]
        == CODEX_FAST_MODEL
        and terms[RUNTIME_TOKEN_CONFIGURED_AGENT_AUDITOR_MODEL_CAPABILITY][
            Target.CODEX.value
        ]
        == CODEX_STANDARD_MODEL
        and terms[RUNTIME_TOKEN_CONFIGURED_AGENT_STRONG_MODELS_CAPABILITY][
            Target.CODEX.value
        ]
        == f"{CODEX_STRONG_MODEL} or {CODEX_STANDARD_MODEL}"
        and terms[RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_OR_STANDARD_MODELS_CAPABILITY][
            Target.CODEX.value
        ]
        == f"{CODEX_FAST_MODEL} or {CODEX_STANDARD_MODEL}"
    )


def resolve_renders_each_kind_from_its_own_sub_registry() -> bool:
    _require_implemented()
    return all(
        resolve_runtime_token(case.kind, case.capability, case.runtime)
        == RUNTIME_TOKEN_REGISTRY[case.kind].names[case.capability][case.runtime]
        for case in runtime_token_resolver_cases()
    )


def field_global_is_wired_to_the_resolver() -> bool:
    _require_implemented()
    return _kind_global_is_wired_to_the_resolver(RUNTIME_TOKEN_FIELD_KIND)


def term_global_is_wired_to_the_resolver() -> bool:
    _require_implemented()
    return _kind_global_is_wired_to_the_resolver(RUNTIME_TOKEN_TERM_KIND)


def _require_implemented() -> None:
    if not implementation_is_ready():
        msg = "outcomeeng.distribution.build is not implemented"
        raise AssertionError(msg)


def _render_skill_bodies(body: str) -> dict[Target, str]:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        builder = SrcTreeBuilder(tmp_path)
        for scenario in source_scenarios():
            builder.add_plugin(
                scenario.plugin,
                skills={f"{scenario.skill}-{SKILL_NAME}": _skill_with(body)},
            )
        build(builder.src_root, tmp_path / "dist")
        return {
            target: "\n".join(
                (
                    tmp_path
                    / "dist"
                    / target.value
                    / scenario.plugin
                    / "skills"
                    / f"{scenario.skill}-{SKILL_NAME}"
                    / "SKILL.md"
                ).read_text()
                for scenario in source_scenarios()
            )
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
        lambda: _render_skill_bodies(f"{{{{! {kind}('{UNKNOWN_CAPABILITY}') !}}}}")
    )
