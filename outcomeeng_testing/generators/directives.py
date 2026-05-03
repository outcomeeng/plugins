"""Hypothesis strategies for build directive AST nodes.

Powers round-trip property tests:

    @given(directives())
    def test_parse_format_roundtrip(directive: Directive) -> None:
        text = format_directive(directive)
        parsed = parse_directives(text)
        assert parsed == (directive,)
"""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, SearchStrategy

from outcomeeng.scripts.build_plugins import (
    Directive,
    IncludeDirective,
    RequireSkillDirective,
)

_KEBAB_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
_KEBAB_INNER_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789-"

MIN_SEGMENT_LENGTH = 1
MAX_SEGMENT_LENGTH = 12
MIN_PATH_DEPTH = 1
MAX_PATH_DEPTH = 4
MARKDOWN_EXTENSION = ".md"


def _kebab_segment_strategy() -> SearchStrategy[str]:
    """Single kebab-case path segment: starts with a letter, no leading or trailing hyphens."""
    return st.text(
        alphabet=_KEBAB_ALPHABET,
        min_size=MIN_SEGMENT_LENGTH,
        max_size=1,
    ).flatmap(
        lambda first: st.text(
            alphabet=_KEBAB_INNER_ALPHABET,
            min_size=0,
            max_size=MAX_SEGMENT_LENGTH - 1,
        )
        .map(lambda rest: first + rest)
        .filter(lambda s: not s.endswith("-") and "--" not in s)
    )


_kebab_segment = _kebab_segment_strategy()


@st.composite
def include_paths(draw: DrawFn) -> str:
    """Slash-separated kebab-case path with .md extension."""
    segments = draw(
        st.lists(_kebab_segment, min_size=MIN_PATH_DEPTH, max_size=MAX_PATH_DEPTH)
    )
    return "/".join(segments) + MARKDOWN_EXTENSION


@st.composite
def skill_refs(draw: DrawFn) -> str:
    """Plugin:skill identifier, both segments kebab-case."""
    plugin = draw(_kebab_segment)
    skill = draw(_kebab_segment)
    return f"{plugin}:{skill}"


@st.composite
def include_directives(draw: DrawFn) -> IncludeDirective:
    return IncludeDirective(path=draw(include_paths()))


@st.composite
def require_skill_directives(draw: DrawFn) -> RequireSkillDirective:
    return RequireSkillDirective(skill_ref=draw(skill_refs()))


def directives() -> SearchStrategy[Directive]:
    """Strategy producing either IncludeDirective or RequireSkillDirective."""
    return st.one_of(include_directives(), require_skill_directives())
