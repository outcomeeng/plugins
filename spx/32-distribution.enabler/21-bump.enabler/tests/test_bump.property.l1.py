"""Level-1 property evidence for `spx/32-distribution.enabler/21-bump.enabler/`.

Covers the path-prefix allow-list compliance assertion in `bump.md`:

    ALWAYS: changes are detected only under `src/plugins/{name}/**` — any
    file change inside that prefix counts as a distribution-surface
    change for plugin `{name}`, and no path outside that prefix
    triggers any bump.

The ALWAYS framing is a universal claim over the diff-path domain. The
evidence is property-based: Hypothesis strategies from
`outcomeeng_testing.generators.bump` explore the input space, and an
independent oracle (the spec's path-prefix rule restated as a string
operation) derives the expected output for every generated input.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from outcomeeng.distribution.bump import SOURCE_PLUGINS_DIR, changed_plugins_from_diff
from outcomeeng_testing.generators.bump import (
    arbitrary_diff_paths,
    plugin_names,
    relative_subpaths,
)


_PREFIX: str = f"{SOURCE_PLUGINS_DIR}/"


def _expected_plugins(paths: list[str]) -> frozenset[str]:
    """Independent oracle: derive the expected plugin set from the spec rule.

    A path contributes plugin name `n` to the output iff it begins with
    `src/plugins/` followed by a non-empty `n` that ends at the next `/` or
    end-of-string. Restated here as a `startswith`/`find` walk so the
    oracle's algorithm differs from the implementation's `split`-based
    approach — a mutation in either path is detectable.
    """
    plugins: set[str] = set()
    for path in paths:
        if not path.startswith(_PREFIX):
            continue
        rest = path[len(_PREFIX) :]
        next_slash = rest.find("/")
        name = rest if next_slash == -1 else rest[:next_slash]
        if name:
            plugins.add(name)
    return frozenset(plugins)


@given(plugin=plugin_names(), subpath=relative_subpaths())
def test_any_path_under_a_plugin_directory_extracts_that_plugin(
    plugin: str,
    subpath: str,
) -> None:
    """For every non-empty `plugin` segment and any nested subpath, the path
    `src/plugins/{plugin}/{subpath}` contributes exactly `{plugin}` and nothing
    else — the allow-list claims the entire `src/plugins/{name}/**` subtree.
    """
    path = f"{SOURCE_PLUGINS_DIR}/{plugin}/{subpath}"
    assert changed_plugins_from_diff([path]) == frozenset({plugin})


@given(path=arbitrary_diff_paths())
def test_function_matches_spec_oracle_over_arbitrary_diff_paths(path: str) -> None:
    """For every diff path, the function's output equals the spec rule's
    output. This is the universal claim restated: the implementation
    realizes the path-prefix discipline and nothing more.
    """
    assert changed_plugins_from_diff([path]) == _expected_plugins([path])


@given(paths=st.lists(arbitrary_diff_paths(), max_size=12))
def test_aggregation_is_the_union_of_per_path_results(paths: list[str]) -> None:
    """The function aggregates correctly: `f(paths)` equals the union of
    `f([p])` over every `p in paths`. Hypothesis generates lists of
    arbitrary diff paths and the test asserts set equality between the
    one-shot and per-path-folded evaluations.
    """
    aggregated = changed_plugins_from_diff(paths)
    per_path_union: frozenset[str] = frozenset()
    for path in paths:
        per_path_union = per_path_union | changed_plugins_from_diff([path])
    assert aggregated == per_path_union
