"""Generated domains for source-and-templating evidence."""

from __future__ import annotations

from dataclasses import dataclass

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


def source_scenarios() -> tuple[SourceScenario, ...]:
    """Generate distinct names, paths, references, and bodies per runtime target."""
    return tuple(
        SourceScenario(
            plugin=f"{target.value}-plugin",
            skill=f"{target.value}-skill",
            skill_ref=f"{target.value}-plugin:{target.value}-skill",
            scope=f"{target.value}-scope",
            inner_topic=f"{target.value}-inner",
            outer_topic=f"{target.value}-outer",
            cycle_topic=f"{target.value}-cycle",
            fragment_body=f"{target.value} fragment body\n",
        )
        for target in Target
    )
