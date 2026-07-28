"""Generated domains for hygiene-operation evidence."""

from __future__ import annotations

from dataclasses import dataclass

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy


@dataclass(frozen=True)
class CleanWorkspaceCase:
    """Variable tracked and ignored content in a cleanup worktree."""

    staged_content: bytes
    unstaged_index_content: bytes
    unstaged_worktree_content: bytes
    ignored_files: tuple[tuple[str, bytes], ...]


@dataclass(frozen=True)
class XmlSpacingWorkspaceCase:
    """Variable target and non-target markdown content."""

    target_content: str
    non_target_index_content: str
    non_target_worktree_content: str


_SAFE_PATH_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789_-"
_MARKDOWN_TEXT_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-"
)
_TAG_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
_INDENT_ALPHABET = " \t"


def markdown_contents() -> SearchStrategy[str]:
    """Generate variable markdown spanning text, lists, tags, and fences."""
    text_fragment = st.text(
        alphabet=_MARKDOWN_TEXT_ALPHABET,
        min_size=1,
        max_size=24,
    )
    tag_name = st.text(alphabet=_TAG_ALPHABET, min_size=1, max_size=12)
    newline = st.sampled_from(("\n", "\r\n"))
    indent = st.text(alphabet=_INDENT_ALPHABET, min_size=0, max_size=3)
    list_marker = st.one_of(
        st.sampled_from(("-", "*", "+")),
        st.integers(min_value=1, max_value=999).map(lambda value: f"{value}."),
        st.integers(min_value=1, max_value=999).map(lambda value: f"{value})"),
    )
    fence_marker = st.sampled_from(("```", "~~~", "````", "~~~~"))
    markdown_line = st.one_of(
        st.builds(
            lambda line_indent, marker, text, line_end: (
                f"{line_indent}{marker} {text}{line_end}"
            ),
            indent,
            list_marker,
            text_fragment,
            newline,
        ),
        st.builds(
            lambda line_indent, tag, line_end: f"{line_indent}</{tag}>{line_end}",
            indent,
            tag_name,
            newline,
        ),
        st.builds(
            lambda text, line_end: f"{text}{line_end}",
            text_fragment,
            newline,
        ),
        newline,
        st.builds(
            lambda marker, line_end: f"{marker}{line_end}",
            fence_marker,
            newline,
        ),
    )
    return st.lists(markdown_line, min_size=0, max_size=80).map("".join)


def clean_workspace_cases() -> SearchStrategy[CleanWorkspaceCase]:
    """Generate worktree states with tracked and gitignored content."""
    ignored_name = st.text(
        alphabet=_SAFE_PATH_ALPHABET,
        min_size=1,
        max_size=16,
    ).filter(lambda value: value not in {".", ".."})
    ignored_file = st.tuples(ignored_name, st.binary(max_size=64))
    return st.builds(
        CleanWorkspaceCase,
        staged_content=st.binary(max_size=64),
        unstaged_index_content=st.binary(max_size=64),
        unstaged_worktree_content=st.binary(max_size=64),
        ignored_files=st.lists(
            ignored_file,
            min_size=1,
            max_size=4,
            unique_by=lambda entry: entry[0],
        ).map(tuple),
    )


def xml_spacing_workspace_cases() -> SearchStrategy[XmlSpacingWorkspaceCase]:
    """Generate staged targets and transformable unstaged non-targets."""
    malformed = st.builds(
        lambda text, tag: f"- {text}\n</{tag}>\n",
        st.text(
            alphabet=_MARKDOWN_TEXT_ALPHABET,
            min_size=1,
            max_size=24,
        ),
        st.text(alphabet=_TAG_ALPHABET, min_size=1, max_size=12),
    )
    return st.builds(
        XmlSpacingWorkspaceCase,
        target_content=malformed,
        non_target_index_content=markdown_contents(),
        non_target_worktree_content=malformed,
    )


__all__ = [
    "CleanWorkspaceCase",
    "XmlSpacingWorkspaceCase",
    "clean_workspace_cases",
    "markdown_contents",
    "xml_spacing_workspace_cases",
]
