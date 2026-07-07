"""Generators for Codex plugin cache reconciliation tests."""

from __future__ import annotations

from dataclasses import dataclass

from hypothesis import strategies as st


@dataclass(frozen=True)
class StaleAfterSuccessfulRefresh:
    """Version domain where Codex reports a stale version after a successful add."""

    plugin: str
    stale_version: str
    desired_version: str


@dataclass(frozen=True)
class AddableCodexPluginSet:
    """Generated addable plugin set plus one working-tree-only plugin."""

    generated_plugins: tuple[str, ...]
    working_tree_only_plugin: str


def addable_codex_plugin_sets() -> st.SearchStrategy[AddableCodexPluginSet]:
    """Generate plugin sets that make hardcoded refresh lists falsifiable."""
    plugin_names = st.from_regex(
        r"[a-z][a-z0-9]*(?:-[a-z0-9]+){0,3}",
        fullmatch=True,
    )
    return st.sets(plugin_names, min_size=1, max_size=4).flatmap(
        lambda generated: st.builds(
            _addable_codex_plugin_set,
            generated=st.just(frozenset(generated)),
            working_tree_only_plugin=plugin_names.filter(
                lambda name: name not in generated
            ),
        )
    )


def stale_after_successful_refreshes() -> st.SearchStrategy[
    StaleAfterSuccessfulRefresh
]:
    """Generate valid plugin/version triples for stale post-refresh reports.

    The desired version is always greater than the stale version by patch segment,
    covering stale-to-desired local-refresh shapes while varying plugin identity
    and numeric version space.
    """
    return st.builds(
        _stale_after_successful_refresh,
        plugin=st.from_regex(
            r"[a-z][a-z0-9]*(?:-[a-z0-9]+){0,3}",
            fullmatch=True,
        ),
        major=st.integers(min_value=0, max_value=3),
        minor=st.integers(min_value=0, max_value=99),
        patch=st.integers(min_value=0, max_value=999),
        patch_increment=st.integers(min_value=1, max_value=20),
    )


def _stale_after_successful_refresh(
    *,
    plugin: str,
    major: int,
    minor: int,
    patch: int,
    patch_increment: int,
) -> StaleAfterSuccessfulRefresh:
    return StaleAfterSuccessfulRefresh(
        plugin=plugin,
        stale_version=f"{major}.{minor}.{patch}",
        desired_version=f"{major}.{minor}.{patch + patch_increment}",
    )


def _addable_codex_plugin_set(
    *,
    generated: frozenset[str],
    working_tree_only_plugin: str,
) -> AddableCodexPluginSet:
    return AddableCodexPluginSet(
        generated_plugins=tuple(sorted(generated)),
        working_tree_only_plugin=working_tree_only_plugin,
    )


__all__ = [
    "AddableCodexPluginSet",
    "StaleAfterSuccessfulRefresh",
    "addable_codex_plugin_sets",
    "stale_after_successful_refreshes",
]
