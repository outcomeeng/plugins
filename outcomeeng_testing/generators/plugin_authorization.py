"""Open plugin and role domains for root authorization evidence."""

from dataclasses import dataclass

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.distribution.contracts import Target


@dataclass(frozen=True)
class PluginAuthorizationCase:
    catalogs: dict[Target, tuple[str, ...]]
    additional_plugin: str
    additional_role: str


def plugin_authorization_cases() -> SearchStrategy[PluginAuthorizationCase]:
    """Vary catalog membership, order, and a role independently of shipped names."""
    return st.lists(
        st.from_regex(r"[a-z][a-z0-9-]{0,20}", fullmatch=True),
        min_size=5,
        max_size=13,
        unique=True,
    ).map(
        lambda names: PluginAuthorizationCase(
            catalogs={
                Target.CLAUDE: tuple(names[1::2]),
                Target.CODEX: tuple(names[2::2]),
            },
            additional_plugin=names[0],
            additional_role=names[-1],
        )
    )
