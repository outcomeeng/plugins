"""Variable plugin and authored-role names for namespace evidence."""

from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Final

from hypothesis import strategies as st

NAME_WORD_ALPHABET: Final = string.ascii_lowercase + string.digits
NAME_WORD_SEPARATOR: Final = "-"


@dataclass(frozen=True)
class AgentNameCase:
    """One generated plugin with authored roles that share its words or not."""

    plugin: str
    roles: tuple[str, ...]


def _hyphenated_names() -> st.SearchStrategy[str]:
    return st.lists(st.text(alphabet=NAME_WORD_ALPHABET, min_size=1), min_size=1).map(
        NAME_WORD_SEPARATOR.join
    )


@st.composite
def agent_name_cases(draw: st.DrawFn) -> AgentNameCase:
    """Generate a plugin with an independent role, the plugin's own name as a
    role, and a role that begins with the plugin name."""
    plugin = draw(_hyphenated_names())
    suffix = draw(_hyphenated_names())
    return AgentNameCase(
        plugin=plugin,
        roles=(suffix, plugin, NAME_WORD_SEPARATOR.join((plugin, suffix))),
    )
