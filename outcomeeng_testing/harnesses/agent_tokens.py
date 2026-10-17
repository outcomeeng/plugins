"""Observations of the agent-token owner, its rendered copies, and the build's per-agent tables."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.build import (
    AGENT_CAPABILITY_REGISTRY,
    CONFIGURED_AGENT_PROMPT_FIELD_NAMES,
    CONFIGURED_AGENT_TERM_NAMES,
)
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng.distribution.orchestration import CATALOG_PATHS
from outcomeeng.distribution.shipped_scripts import load_shipped_module
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/agent_tokens.py``.
REPO_ROOT: Final = Path(__file__).resolve().parents[2]

AGENT_TOKEN_OWNER_PATH: Final = (
    Path(SOURCE_ROOT_NAME)
    / PLUGINS_DIR_NAME
    / "coding-agents"
    / "skills"
    / "recover-prowl-agents"
    / "scripts"
    / "agent_tokens.py"
)
AGENT_TOKEN_OWNER_MODULE_NAME: Final = "agent_tokens"
AGENT_TOKEN_ENUM_NAME: Final = "AgentToken"
AGENT_TOKEN_DATA_FILENAME: Final = "agent-tokens.json"
SPEC_TREE_PLUGIN_NAME: Final = "spec-tree"


@dataclass(frozen=True)
class RenderedAgentTokens:
    """The data file one target's tree carries beside one script that reads it."""

    target: Target
    script: Path
    document: Mapping[str, object] | None


@dataclass(frozen=True)
class AgentKeyedTable:
    """One per-agent table of the build and the keys it carries."""

    name: str
    keys: tuple[object, ...]


def declared_agent_tokens() -> Mapping[str, str]:
    """Return each ``AgentToken`` member name and its token, read from the owner module."""
    module = load_shipped_module(
        AGENT_TOKEN_OWNER_MODULE_NAME, REPO_ROOT / AGENT_TOKEN_OWNER_PATH
    )
    enum_class = getattr(module, AGENT_TOKEN_ENUM_NAME)
    return {member.name: member.value for member in enum_class}


def rendered_agent_token_files() -> tuple[RenderedAgentTokens, ...]:
    """Observe the data file beside each spec-tree script that reads it, in every target tree.

    A script reads the data file when its authored source names the file.
    """
    plugin_source = (
        REPO_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME / SPEC_TREE_PLUGIN_NAME
    )
    reading_scripts = sorted(
        script.relative_to(plugin_source)
        for script in plugin_source.rglob("*.py")
        if AGENT_TOKEN_DATA_FILENAME in script.read_text(encoding="utf-8")
    )
    reader = DistTreeReader(REPO_ROOT)
    observations: list[RenderedAgentTokens] = []
    for target in Target:
        plugin_root = reader.target_root(target) / SPEC_TREE_PLUGIN_NAME
        for script in reading_scripts:
            data_file = plugin_root / script.parent / AGENT_TOKEN_DATA_FILENAME
            document = (
                json.loads(data_file.read_text(encoding="utf-8"))
                if data_file.is_file()
                else None
            )
            observations.append(RenderedAgentTokens(target, script, document))
    return tuple(observations)


def build_agent_keyed_tables() -> tuple[AgentKeyedTable, ...]:
    """Observe the keys of every per-agent table the build carries."""
    tables = [
        AgentKeyedTable("AGENT_CAPABILITY_REGISTRY", tuple(AGENT_CAPABILITY_REGISTRY)),
        AgentKeyedTable(
            "CONFIGURED_AGENT_PROMPT_FIELD_NAMES",
            tuple(CONFIGURED_AGENT_PROMPT_FIELD_NAMES),
        ),
        AgentKeyedTable("CATALOG_PATHS", tuple(CATALOG_PATHS)),
    ]
    tables.extend(
        AgentKeyedTable(f"CONFIGURED_AGENT_TERM_NAMES[{capability}]", tuple(names))
        for capability, names in CONFIGURED_AGENT_TERM_NAMES.items()
    )
    return tuple(tables)


def generated_tree_directory_names() -> frozenset[str]:
    """Observe the names of the generated trees directly under ``dist/``."""
    dist_root = REPO_ROOT / DIST_DIR_NAME
    return frozenset(entry.name for entry in dist_root.iterdir() if entry.is_dir())
