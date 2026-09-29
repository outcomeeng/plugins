"""Mapping evidence for marketplace definitions and invocation names."""

from __future__ import annotations

import tomllib
from pathlib import Path

from outcomeeng.distribution.agents import AGENT_NAME_FIELD
from outcomeeng.distribution.build import (
    FLAT_AGENT_PLUGIN_SEPARATOR,
    NATIVE_AGENT_PLUGIN_SEPARATOR,
    agent_capability,
    agent_dispatch_name,
    agent_slug,
    converted_agent_relative_path,
    plugin_relative_path,
    source_plugin_name,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses.agent_conversion import (
    agent_document_oracle,
    build_repository_agents,
)


def test_agent_definition_and_dispatch_names_preserve_plugin_and_authored_role(
    tmp_path: Path,
) -> None:
    repository_agents = build_repository_agents(tmp_path)
    targets = tuple(Target)

    assert targets
    assert repository_agents.sources
    for target in targets:
        capability = agent_capability(target)
        target_tree = repository_agents.dist_root / target.value
        for source in repository_agents.sources_for(target):
            plugin = source_plugin_name(source, src_root=repository_agents.source_root)
            stem = source.stem
            slug = agent_slug(plugin, stem, capability=capability)
            dispatch = agent_dispatch_name(plugin, stem, capability=capability)
            if capability.namespaced:
                assert slug == stem
                assert dispatch.split(NATIVE_AGENT_PLUGIN_SEPARATOR) == [plugin, stem]
                artifact = target_tree / plugin_relative_path(
                    source, src_root=repository_agents.source_root
                )
                assert (
                    agent_document_oracle(artifact).frontmatter[AGENT_NAME_FIELD]
                    == stem
                )
                continue

            assert slug == FLAT_AGENT_PLUGIN_SEPARATOR.join((plugin, stem))
            assert dispatch == slug
            artifact = target_tree / converted_agent_relative_path(
                plugin, stem, capability=capability
            )
            assert artifact.exists(), f"missing canonical agent artifact {artifact}"
            assert artifact.stem == dispatch
            parsed = tomllib.loads(artifact.read_text(encoding="utf-8"))
            assert parsed[AGENT_NAME_FIELD] == slug
