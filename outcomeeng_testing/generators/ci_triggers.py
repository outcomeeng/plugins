"""Hypothesis strategies for eval CI trigger-path derivation."""

from __future__ import annotations

import string

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

_SEGMENT_ALPHABET = string.ascii_lowercase + string.digits + "-"
_RECURSIVE_GLOB_SUFFIX = "/**"


def _segments() -> SearchStrategy[list[str]]:
    return st.lists(
        st.text(_SEGMENT_ALPHABET, min_size=1, max_size=6),
        min_size=1,
        max_size=4,
    )


def _directory_globs() -> SearchStrategy[str]:
    return _segments().map(lambda parts: "/".join(parts) + _RECURSIVE_GLOB_SUFFIX)


def _file_patterns() -> SearchStrategy[str]:
    return _segments().map(lambda parts: "/".join(parts) + ".md")


def trigger_patterns() -> SearchStrategy[str]:
    """One trigger pattern: a recursive directory glob or a concrete file path."""

    return st.one_of(_directory_globs(), _file_patterns())


def trigger_pattern_sets() -> SearchStrategy[set[str]]:
    """Pattern sets that mix nested globs, disjoint globs, and file paths.

    Nesting is what minimization must reason about, so the strategy composes a
    freely generated set with a derived set of children under those globs —
    a purely random set would rarely produce the covering relationships the
    property is about.
    """

    def _with_nested_children(base: set[str]) -> SearchStrategy[set[str]]:
        globs = sorted(p for p in base if p.endswith(_RECURSIVE_GLOB_SUFFIX))
        if not globs:
            return st.just(base)
        children = st.lists(
            st.tuples(st.sampled_from(globs), _segments()),
            max_size=4,
        ).map(
            lambda pairs: {
                glob.removesuffix(_RECURSIVE_GLOB_SUFFIX)
                + "/"
                + "/".join(parts)
                + suffix
                for glob, parts in pairs
                for suffix in (_RECURSIVE_GLOB_SUFFIX, ".md")
            }
        )
        return children.map(lambda extra: base | extra)

    return st.sets(trigger_patterns(), min_size=1, max_size=6).flatmap(
        _with_nested_children
    )


def probe_paths() -> SearchStrategy[str]:
    """Repository-relative paths a trigger pattern set is evaluated against."""

    return _segments().map(lambda parts: "/".join(parts) + ".md")
