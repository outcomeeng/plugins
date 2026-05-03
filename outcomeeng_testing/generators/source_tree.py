"""Hypothesis strategies for generating valid src/ plugin tree configurations.

The strategies emit immutable config dataclasses that ``materialize`` then
applies to a SrcTreeBuilder. Tests use ``@given(src_tree_configs())`` to
exercise the build pipeline across a varied space of valid src/ inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn

from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

NAME_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
NAME_WITH_HYPHEN_ALPHABET = "abcdefghijklmnopqrstuvwxyz-"

MIN_NAME_LEN = 1
MAX_NAME_LEN = 12

MIN_BODY_LEN = 0
MAX_BODY_LEN = 120
PRINTABLE_ASCII_MIN = 32
PRINTABLE_ASCII_MAX = 126

MIN_PLUGINS = 1
MAX_PLUGINS = 3
MAX_PER_PLUGIN_ITEMS = 2
MAX_SHARED_TOPICS = 2
MAX_PER_TOPIC_REFERENCES = 2

REFERENCE_FILE_SUFFIX = ".md"


@dataclass(frozen=True)
class PluginConfig:
    """Configuration for a single plugin in a generated src/ tree."""

    name: str
    skills: Mapping[str, str]
    commands: Mapping[str, str]
    agents: Mapping[str, str]


@dataclass(frozen=True)
class SharedTopicConfig:
    """Configuration for a single shared topic in a generated src/ tree."""

    scope: str
    topic: str
    fragment_body: str
    references: Mapping[str, str]


@dataclass(frozen=True)
class SrcTreeConfig:
    """Configuration for a generated src/ tree."""

    plugins: tuple[PluginConfig, ...]
    shared_topics: tuple[SharedTopicConfig, ...]


_simple_name = st.text(
    alphabet=NAME_ALPHABET, min_size=MIN_NAME_LEN, max_size=MAX_NAME_LEN
)
_kebab_name = st.text(
    alphabet=NAME_WITH_HYPHEN_ALPHABET,
    min_size=MIN_NAME_LEN,
    max_size=MAX_NAME_LEN,
).filter(lambda s: not s.startswith("-") and not s.endswith("-"))
_body_text = st.text(
    min_size=MIN_BODY_LEN,
    max_size=MAX_BODY_LEN,
    alphabet=st.characters(
        min_codepoint=PRINTABLE_ASCII_MIN,
        max_codepoint=PRINTABLE_ASCII_MAX,
    ),
)
_reference_filename = _kebab_name.map(lambda s: f"{s}{REFERENCE_FILE_SUFFIX}")


@st.composite
def plugin_configs(draw: DrawFn) -> PluginConfig:
    """Strategy for a single plugin config with up to MAX_PER_PLUGIN_ITEMS each of skills, commands, agents."""
    return PluginConfig(
        name=draw(_simple_name),
        skills=draw(
            st.dictionaries(_kebab_name, _body_text, max_size=MAX_PER_PLUGIN_ITEMS)
        ),
        commands=draw(
            st.dictionaries(_kebab_name, _body_text, max_size=MAX_PER_PLUGIN_ITEMS)
        ),
        agents=draw(
            st.dictionaries(_kebab_name, _body_text, max_size=MAX_PER_PLUGIN_ITEMS)
        ),
    )


@st.composite
def shared_topic_configs(draw: DrawFn) -> SharedTopicConfig:
    """Strategy for a single shared topic config with up to MAX_PER_TOPIC_REFERENCES references."""
    return SharedTopicConfig(
        scope=draw(_simple_name),
        topic=draw(_kebab_name),
        fragment_body=draw(_body_text),
        references=draw(
            st.dictionaries(
                _reference_filename,
                _body_text,
                max_size=MAX_PER_TOPIC_REFERENCES,
            )
        ),
    )


@st.composite
def src_tree_configs(draw: DrawFn) -> SrcTreeConfig:
    """Strategy for a complete src/ tree config.

    Generates 1-3 plugins (each with up to 2 skills, 2 commands, 2 agents) plus
    0-2 shared topics. Plugin names are simple ASCII; skill, command, agent, and
    topic names are kebab-case. Bodies are printable ASCII to keep filesystem
    encoding deterministic.
    """
    plugins = draw(
        st.lists(
            plugin_configs(),
            min_size=MIN_PLUGINS,
            max_size=MAX_PLUGINS,
            unique_by=lambda p: p.name,
        )
    )
    shared = draw(
        st.lists(
            shared_topic_configs(),
            max_size=MAX_SHARED_TOPICS,
            unique_by=lambda t: (t.scope, t.topic),
        )
    )
    return SrcTreeConfig(plugins=tuple(plugins), shared_topics=tuple(shared))


def materialize(config: SrcTreeConfig, builder: SrcTreeBuilder) -> None:
    """Apply a SrcTreeConfig to a SrcTreeBuilder, materializing all plugins and topics."""
    for plugin in config.plugins:
        builder.add_plugin(
            plugin.name,
            skills=dict(plugin.skills),
            commands=dict(plugin.commands),
            agents=dict(plugin.agents),
        )
    for topic in config.shared_topics:
        builder.add_shared_topic(
            topic.scope,
            topic.topic,
            topic.fragment_body,
            references=dict(topic.references),
        )
