"""Finite source-tool-set domains for agent conversion mappings."""

from collections.abc import Iterator
from itertools import combinations

from outcomeeng.distribution.agents import SOURCE_TOOL_UNIVERSE


def every_tool_subset() -> Iterator[tuple[str, ...]]:
    """Yield every subset of the source-owned tool universe, smallest first."""
    universe = tuple(sorted(SOURCE_TOOL_UNIVERSE))
    for size in range(len(universe) + 1):
        yield from combinations(universe, size)
