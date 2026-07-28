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
    ignored_directories: tuple[tuple[str, str, bytes], ...]
    untracked_files: tuple[tuple[str, bytes], ...]


@dataclass(frozen=True)
class XmlSpacingWorkspaceCase:
    """Variable target and non-target markdown content."""

    target_content: str
    non_target_index_content: str
    non_target_worktree_content: str


@dataclass(frozen=True)
class FencedMarkdownCase:
    """Fenced markdown and its line-ending-normalized expectation."""

    content: str
    expected_content: str


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


def fenced_markdown_cases() -> SearchStrategy[FencedMarkdownCase]:
    """Generate fenced markdown containing transformable pseudo-XML content."""
    fence_marker = st.sampled_from(("```", "~~~", "````", "~~~~"))
    text_fragment = st.text(
        alphabet=_MARKDOWN_TEXT_ALPHABET,
        min_size=1,
        max_size=24,
    )
    tag_name = st.text(alphabet=_TAG_ALPHABET, min_size=1, max_size=12)
    newline = st.sampled_from(("\n", "\r\n"))
    return st.builds(
        _fenced_markdown_case,
        fence_marker,
        text_fragment,
        tag_name,
        newline,
    )


def _fenced_markdown_case(
    marker: str,
    text: str,
    tag: str,
    line_end: str,
) -> FencedMarkdownCase:
    content = (
        f"{marker}{line_end}- {text}{line_end}</{tag}>{line_end}{marker}{line_end}"
    )
    return FencedMarkdownCase(
        content=content,
        expected_content=content.replace("\r\n", "\n"),
    )


@st.composite
def clean_workspace_cases(draw: st.DrawFn) -> CleanWorkspaceCase:
    """Generate worktree states with tracked and gitignored content."""
    path_component = st.text(
        alphabet=_SAFE_PATH_ALPHABET,
        min_size=1,
        max_size=16,
    ).filter(lambda value: value not in {".", ".."})
    top_level_names = draw(
        st.lists(path_component, min_size=3, max_size=9, unique=True)
    )
    ignored_file_count = draw(
        st.integers(min_value=1, max_value=len(top_level_names) - 2)
    )
    ignored_directory_count = draw(
        st.integers(
            min_value=1,
            max_value=len(top_level_names) - ignored_file_count - 1,
        )
    )
    ignored_file_names = top_level_names[:ignored_file_count]
    ignored_directory_names = top_level_names[
        ignored_file_count : ignored_file_count + ignored_directory_count
    ]
    untracked_names = top_level_names[ignored_file_count + ignored_directory_count :]
    nested_artifact = st.tuples(
        st.lists(path_component, min_size=1, max_size=3).map("/".join),
        st.binary(max_size=64),
    )
    return CleanWorkspaceCase(
        staged_content=draw(st.binary(max_size=64)),
        unstaged_index_content=draw(st.binary(max_size=64)),
        unstaged_worktree_content=draw(st.binary(max_size=64)),
        ignored_files=tuple(
            (name, draw(st.binary(max_size=64))) for name in ignored_file_names
        ),
        ignored_directories=tuple(
            (name, artifact_path, content)
            for name in ignored_directory_names
            for artifact_path, content in (draw(nested_artifact),)
        ),
        untracked_files=tuple(
            (name, draw(st.binary(max_size=64))) for name in untracked_names
        ),
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
    "FencedMarkdownCase",
    "XmlSpacingWorkspaceCase",
    "clean_workspace_cases",
    "fenced_markdown_cases",
    "markdown_contents",
    "xml_spacing_workspace_cases",
]
