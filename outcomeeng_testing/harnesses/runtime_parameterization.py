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
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng.validation.runtime_tokens import forbidden_names
from outcomeeng_testing.generators.source_and_templating import (
    InvalidRuntimeTokenCase,
    invalid_runtime_token_cases,
    runtime_token_probe_name,
    source_scenarios,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

SKILL_NAME = "example-skill"
SPEC_STATED_RUNTIME_NAMES = {
    (RUNTIME_TOKEN_TOOL_KIND, "ask_user"): {
        Target.CLAUDE: "AskUserQuestion",
        Target.CODEX: "request_user_input",
    },
    (RUNTIME_TOKEN_FILE_KIND, RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY): {
        Target.CLAUDE: "CLAUDE.md",
        Target.CODEX: "AGENTS.md",
    },
}


def implementation_is_ready() -> bool:
    return IMPLEMENTED


def registry_token_renders_each_target_name() -> bool:
    _require_implemented()
    return (
        all(
            _implicit_registry_case_renders(
                case.kind,
                case.capability,
                Target(case.runtime),
            )
            for case in runtime_token_resolver_cases()
        )
        and all(
            _implicit_registry_case_matches_expected(
                kind,
                capability,
                runtime,
                expected,
            )
            for (kind, capability), names in SPEC_STATED_RUNTIME_NAMES.items()
            for runtime, expected in names.items()
        )
    )


def registry_contract_drives_render_path() -> bool:
    _require_implemented()
    kind = RUNTIME_TOKEN_TOOL_KIND
    capability = RUNTIME_TOKEN_ASK_USER_CAPABILITY
    runtime = Target.CODEX
    kind_entry = RUNTIME_TOKEN_REGISTRY[kind]
    probe_name = runtime_token_probe_name(kind, capability)
    runtime_names = {
        **kind_entry.names[capability],
        runtime.value: probe_name,
    }
    registry = {
        **RUNTIME_TOKEN_REGISTRY,
        kind: RuntimeTokenKind(
            lint_enforced=kind_entry.lint_enforced,
            names={
                **kind_entry.names,
                capability: runtime_names,
            },
        ),
    }
    return (
        render_text(
            f"{{{{! {kind}('{capability}') !}}}}",
            variables={"target": runtime.value},
            runtime_token_registry=registry,
        )
        == probe_name
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
            target: (
                "Read the guide at "
                f"{_registry_name(RUNTIME_TOKEN_FILE_KIND, RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY, target)} "
                "once per session."
            )
            for target in Target
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
            target: (
                "Configure the field "
                f"{_registry_name(RUNTIME_TOKEN_FIELD_KIND, RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY, target)}."
            )
            for target in Target
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
            target: (
                "Configure the "
                f"{_registry_name(RUNTIME_TOKEN_TERM_KIND, RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY, target)}."
            )
            for target in Target
        },
    )


def runtime_explicit_token_renders_named_runtime_on_every_target() -> bool:
    _require_implemented()
    return all(
        _explicit_registry_case_renders(
            case.kind,
            case.capability,
            Target(case.runtime),
        )
        for case in runtime_token_resolver_cases()
    )


def _implicit_registry_case_renders(
    kind: str,
    capability: str,
    runtime: Target,
) -> bool:
    template = (
        f"{{!% if target == '{runtime.value}' %!}}"
        f"{{{{! {kind}('{capability}') !}}}}"
        "{!% endif %!}"
    )
    bodies = _render_skill_bodies(template)
    return _target_bodies_equal(
        bodies,
        {
            target: _registry_name(kind, capability, runtime)
            if target is runtime
            else ""
            for target in Target
        },
    )


def _implicit_registry_case_matches_expected(
    kind: str,
    capability: str,
    runtime: Target,
    expected: str,
) -> bool:
    template = (
        f"{{!% if target == '{runtime.value}' %!}}"
        f"{{{{! {kind}('{capability}') !}}}}"
        "{!% endif %!}"
    )
    return _target_bodies_equal(
        _render_skill_bodies(template),
        {target: expected if target is runtime else "" for target in Target},
    )


def _explicit_registry_case_renders(
    kind: str,
    capability: str,
    runtime: Target,
) -> bool:
    bodies = _render_skill_bodies(
        f"{{{{! {kind}('{capability}', '{runtime.value}') !}}}}"
    )
    return _target_bodies_equal(
        bodies,
        {target: _registry_name(kind, capability, runtime) for target in Target},
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


def _registry_name(kind: str, capability: str, target: Target) -> str:
    return RUNTIME_TOKEN_REGISTRY[kind].names[capability][target.value]


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
