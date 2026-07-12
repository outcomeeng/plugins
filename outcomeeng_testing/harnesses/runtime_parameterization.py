"""Harness for runtime-parameterization evidence tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import (
    BuildError,
    IMPLEMENTED,
    RUNTIME_TOKEN_ASK_USER_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY,
    RUNTIME_TOKEN_FIELD_KIND,
    RUNTIME_TOKEN_FILE_KIND,
    RUNTIME_TOKEN_REGISTRY,
    RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY,
    RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY,
    RUNTIME_TOKEN_TERM_KIND,
    RUNTIME_TOKEN_TOOL_KIND,
    RuntimeTokenKind,
    build,
    render_text,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng.validation.runtime_tokens import forbidden_names
from outcomeeng_testing.generators.source_and_templating import (
    InvalidRuntimeTokenCase,
    invalid_runtime_token_cases,
    source_scenarios,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

SKILL_NAME = "example-skill"


def implementation_is_ready() -> bool:
    return IMPLEMENTED


def registry_token_renders_each_target_name() -> bool:
    _require_implemented()
    bodies = _render_skill_bodies(
        "Ask the user via "
        f"{{{{! {RUNTIME_TOKEN_TOOL_KIND}('{RUNTIME_TOKEN_ASK_USER_CAPABILITY}') !}}}} "
        "now.",
    )
    return _target_bodies_equal(
        bodies,
        {
            Target.CLAUDE: "Ask the user via AskUserQuestion now.",
            Target.CODEX: "Ask the user via request_user_input now.",
        },
    )


def file_kind_renders_guide_filename_per_target() -> bool:
    _require_implemented()
    bodies = _render_skill_bodies(
        "Read the guide at "
        f"{{{{! {RUNTIME_TOKEN_FILE_KIND}('{RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY}') !}}}} "
        "once per session.",
    )
    return _target_bodies_equal(
        bodies,
        {
            Target.CLAUDE: "Read the guide at CLAUDE.md once per session.",
            Target.CODEX: "Read the guide at AGENTS.md once per session.",
        },
    )


def field_kind_renders_live_registry_name_per_target() -> bool:
    _require_implemented()
    bodies = _render_skill_bodies(
        "Configure the field "
        f"{{{{! {RUNTIME_TOKEN_FIELD_KIND}('{RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY}') !}}}}.",
    )
    return _target_bodies_equal(
        bodies,
        {
            Target.CLAUDE: "Configure the field system prompt.",
            Target.CODEX: "Configure the field developer_instructions.",
        },
    )


def term_kind_renders_live_registry_name_per_target() -> bool:
    _require_implemented()
    bodies = _render_skill_bodies(
        "Configure the "
        f"{{{{! {RUNTIME_TOKEN_TERM_KIND}('{RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY}') !}}}}.",
    )
    return _target_bodies_equal(
        bodies,
        {
            Target.CLAUDE: "Configure the subagent.",
            Target.CODEX: "Configure the custom agent.",
        },
    )


def runtime_explicit_token_renders_named_runtime_on_every_target() -> bool:
    _require_implemented()
    bodies = _render_skill_bodies(
        "On Claude this is "
        f"{{{{! {RUNTIME_TOKEN_TOOL_KIND}('{RUNTIME_TOKEN_ASK_USER_CAPABILITY}', '{Target.CLAUDE.value}') !}}}}.",
    )
    return _target_bodies_equal(
        bodies,
        {
            Target.CLAUDE: "On Claude this is AskUserQuestion.",
            Target.CODEX: "On Claude this is AskUserQuestion.",
        },
    )


def build_fails_on_unknown_kind_capability_or_runtime() -> bool:
    _require_implemented()
    return (
        all(
            _invalid_runtime_token_case_fails(case)
            for case in invalid_runtime_token_cases()
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
    return _target_bodies_equal(
        bodies,
        {
            Target.CLAUDE: f"Wait via {claude_name}.",
            Target.CODEX: "",
        },
    ) and render_text(
        template,
        variables={"target": Target.CODEX.value},
    ) == ""


def _raises_build_error(call: Callable[[], object]) -> bool:
    try:
        call()
    except BuildError:
        return True
    return False


def _invalid_runtime_token_case_fails(case: InvalidRuntimeTokenCase) -> bool:
    return _raises_build_error(
        lambda: _render_skill_bodies(
            f"{{{{! {case.kind}('{case.capability}') !}}}}"
        )
    )


def registry_is_keyed_by_kind_with_explicit_guard_enforcement() -> bool:
    _require_implemented()
    expected_forbidden = tuple(
        sorted(
            {
                name
                for kind in RUNTIME_TOKEN_REGISTRY.values()
                if kind.lint_enforced
                for entry in kind.names.values()
                for name in entry.values()
            },
            key=len,
            reverse=True,
        )
    )
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
        and forbidden_names() == expected_forbidden
    )


def _require_implemented() -> None:
    if not implementation_is_ready():
        msg = "outcomeeng.distribution.build is not implemented"
        raise AssertionError(msg)


def _render_skill_bodies(body: str) -> dict[Target, tuple[str, ...]]:
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
            target: tuple(
                _rendered_skill_body(
                    tmp_path
                    / "dist"
                    / target.value
                    / scenario.plugin
                    / "skills"
                    / f"{scenario.skill}-{SKILL_NAME}"
                    / "SKILL.md"
                )
                for scenario in source_scenarios()
            )
            for target in Target
        }


def _skill_with(body: str) -> str:
    return f"---\nname: {SKILL_NAME}\ndescription: Example skill.\n---\n\n{body}\n"


def _rendered_skill_body(path: Path) -> str:
    _, separator, body = path.read_text(encoding="utf-8").partition("---\n\n")
    if not separator:
        msg = f"generated skill lacks a frontmatter boundary: {path}"
        raise AssertionError(msg)
    return body.strip()


def _target_bodies_equal(
    bodies: dict[Target, tuple[str, ...]],
    expected: dict[Target, str],
) -> bool:
    return all(
        rendered_bodies
        and all(body == expected[target] for body in rendered_bodies)
        for target, rendered_bodies in bodies.items()
    )
