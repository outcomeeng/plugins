"""Generated domains for source-and-templating evidence."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from outcomeeng.distribution.build import (
    RUNTIME_TOKEN_REGISTRY,
    SHARED_FRAGMENT_FILENAME,
    IncludeDirective,
    format_directive,
    resolve_runtime_token,
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import (
    MARKDOWN_FILE_SUFFIX,
    PLUGIN_SUBDIRS,
    REFERENCES_SUBDIR_NAME,
    RUNTIME_TOKEN_ASK_USER_CAPABILITY,
    RUNTIME_TOKEN_TOOL_KIND,
    SKILLS_SUBDIR_NAME,
    Target,
    format_target_conditional,
)


@dataclass(frozen=True)
class SourceScenario:
    """One generated source-tree scenario."""

    plugin: str
    skill: str
    skill_ref: str
    scope: str
    inner_topic: str
    outer_topic: str
    cycle_topic: str
    fragment_body: str
    branch_payloads: dict[Target, str]


@dataclass(frozen=True)
class InvalidRuntimeTokenCase:
    """One generated registry coordinate outside the production domain."""

    kind: str
    capability: str


def invalid_runtime_token_capability(kind: str) -> str:
    """Generate a capability name outside one live kind registry."""
    return _name_outside(RUNTIME_TOKEN_REGISTRY[kind].names)


def invalid_runtime_token_cases() -> tuple[InvalidRuntimeTokenCase, ...]:
    """Generate one invalid coordinate for each registry lookup boundary."""
    return (
        InvalidRuntimeTokenCase(
            kind=_name_outside(RUNTIME_TOKEN_REGISTRY),
            capability=RUNTIME_TOKEN_ASK_USER_CAPABILITY,
        ),
        InvalidRuntimeTokenCase(
            kind=RUNTIME_TOKEN_TOOL_KIND,
            capability=invalid_runtime_token_capability(RUNTIME_TOKEN_TOOL_KIND),
        ),
    )


def runtime_token_probe_name(kind: str, capability: str) -> str:
    """Generate a runtime name outside one live capability registry."""
    return _name_outside(RUNTIME_TOKEN_REGISTRY[kind].names[capability].values())


class IncludePlacement(StrEnum):
    """Authored location of a target-scoped include directive."""

    SOURCE = "source"
    SHARED_FRAGMENT = "shared-fragment"


@dataclass(frozen=True)
class TargetScopedIncludeCase:
    """One target-scoped include and its expected fan-out path."""

    source: SourceScenario
    target: Target
    placement: IncludePlacement
    root_body: str
    outer_fragment_body: str | None
    reference_filename: str
    expected_relative_path: Path


def source_scenarios() -> tuple[SourceScenario, ...]:
    """Compose source-tree cases from every production runtime-token coordinate."""
    return tuple(
        SourceScenario(
            plugin=f"{coordinate.kind}-{coordinate.runtime}",
            skill=coordinate.capability.replace("_", "-"),
            skill_ref=(
                f"{coordinate.kind}-{coordinate.runtime}:"
                f"{coordinate.capability.replace('_', '-')}"
            ),
            scope=coordinate.kind,
            inner_topic=coordinate.capability.replace("_", "-"),
            outer_topic=(
                f"{coordinate.capability.replace('_', '-')}-{coordinate.runtime}"
            ),
            cycle_topic=(
                f"{coordinate.runtime}-{coordinate.capability.replace('_', '-')}"
            ),
            fragment_body=(
                resolve_runtime_token(
                    coordinate.kind,
                    coordinate.capability,
                    coordinate.runtime,
                )
                + "\n"
            ),
            branch_payloads={
                target: (
                    f"{target.value}:"
                    f"{resolve_runtime_token(coordinate.kind, coordinate.capability, coordinate.runtime)}"
                )
                for target in Target
            },
        )
        for coordinate in runtime_token_resolver_cases()
    )


def _name_outside(domain: Collection[str]) -> str:
    names = set(domain)
    candidate = f"{max(names)}_outside_domain"
    while candidate in names:
        candidate = f"{candidate}_outside_domain"
    return candidate


def target_scoped_include_cases() -> tuple[TargetScopedIncludeCase, ...]:
    """Cover each target with direct and nested conditional includes."""
    cases: list[TargetScopedIncludeCase] = []
    for source in source_scenarios():
        inner_directive = format_directive(
            IncludeDirective(
                f"{source.scope}/{source.inner_topic}/{SHARED_FRAGMENT_FILENAME}"
            )
        )
        outer_directive = format_directive(
            IncludeDirective(
                f"{source.scope}/{source.outer_topic}/{SHARED_FRAGMENT_FILENAME}"
            )
        )
        reference_filename = f"{source.cycle_topic}{MARKDOWN_FILE_SUFFIX}"
        expected_relative_path = (
            Path(source.plugin)
            / SKILLS_SUBDIR_NAME
            / source.skill
            / REFERENCES_SUBDIR_NAME
            / reference_filename
        )
        for target in Target:
            conditional = format_target_conditional(target, inner_directive)
            cases.extend(
                (
                    TargetScopedIncludeCase(
                        source=source,
                        target=target,
                        placement=IncludePlacement.SOURCE,
                        root_body=conditional,
                        outer_fragment_body=None,
                        reference_filename=reference_filename,
                        expected_relative_path=expected_relative_path,
                    ),
                    TargetScopedIncludeCase(
                        source=source,
                        target=target,
                        placement=IncludePlacement.SHARED_FRAGMENT,
                        root_body=outer_directive,
                        outer_fragment_body=conditional,
                        reference_filename=reference_filename,
                        expected_relative_path=expected_relative_path,
                    ),
                )
            )
    return tuple(cases)


def unrecognized_plugin_subdirectory_names() -> tuple[str, ...]:
    """Return generated directory names outside the production allowlist."""
    candidates = {
        name
        for scenario in source_scenarios()
        for name in (scenario.outer_topic, scenario.cycle_topic)
    }
    return tuple(sorted(candidates.difference(PLUGIN_SUBDIRS)))
