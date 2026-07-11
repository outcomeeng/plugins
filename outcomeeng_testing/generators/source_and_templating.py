"""Generated domains for source-and-templating evidence."""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.distribution.build import (
    resolve_runtime_token,
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import Target


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
