"""Generated domains for source-and-templating evidence."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

from outcomeeng.distribution.build import (
    RUNTIME_TOKEN_REGISTRY,
    resolve_runtime_token,
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import (
    PLUGIN_SUBDIRS,
    RUNTIME_TOKEN_ASK_USER_CAPABILITY,
    RUNTIME_TOKEN_TOOL_KIND,
    Target,
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


def unrecognized_plugin_subdirectory_names() -> tuple[str, ...]:
    """Return generated directory names outside the production allowlist."""
    candidates = {
        name
        for scenario in source_scenarios()
        for name in (scenario.outer_topic, scenario.cycle_topic)
    }
    return tuple(sorted(candidates.difference(PLUGIN_SUBDIRS)))
