"""Level 1 property tests for scripts/fix-xml-spacing.py."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng.scripts import fix_xml_spacing

TEXT_ALPHABET: Final = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-"
)
TAG_ALPHABET: Final = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
INDENT_ALPHABET: Final = " \t"
MAX_TEXT_LENGTH: Final = 24
MAX_TAG_LENGTH: Final = 12
MAX_INDENT_WIDTH: Final = 3
MAX_LINE_COUNT: Final = 80
MAX_EXAMPLES: Final = 100

TEXT_FRAGMENT = st.text(
    alphabet=TEXT_ALPHABET,
    min_size=1,
    max_size=MAX_TEXT_LENGTH,
)
TAG_NAME = st.text(
    alphabet=TAG_ALPHABET,
    min_size=1,
    max_size=MAX_TAG_LENGTH,
)
NEWLINE = st.sampled_from(["\n", "\r\n"])
INDENT = st.text(
    alphabet=INDENT_ALPHABET,
    min_size=0,
    max_size=MAX_INDENT_WIDTH,
)
LIST_MARKER = st.one_of(
    st.sampled_from(["-", "*", "+"]),
    st.integers(min_value=1, max_value=999).map(lambda value: f"{value}."),
    st.integers(min_value=1, max_value=999).map(lambda value: f"{value})"),
)
FENCE_MARKER = st.sampled_from(["```", "~~~", "````", "~~~~"])

MARKDOWN_LINE = st.one_of(
    st.builds(
        lambda indent, marker, text, newline: f"{indent}{marker} {text}{newline}",
        INDENT,
        LIST_MARKER,
        TEXT_FRAGMENT,
        NEWLINE,
    ),
    st.builds(
        lambda indent, tag, newline: f"{indent}</{tag}>{newline}",
        INDENT,
        TAG_NAME,
        NEWLINE,
    ),
    st.builds(
        lambda text, newline: f"{text}{newline}",
        TEXT_FRAGMENT,
        NEWLINE,
    ),
    st.builds(lambda newline: newline, NEWLINE),
    st.builds(
        lambda marker, newline: f"{marker}{newline}",
        FENCE_MARKER,
        NEWLINE,
    ),
)
MARKDOWN_CONTENT = st.lists(
    MARKDOWN_LINE,
    min_size=0,
    max_size=MAX_LINE_COUNT,
).map("".join)


@given(content=MARKDOWN_CONTENT)
@settings(max_examples=MAX_EXAMPLES)
def test_fix_file_is_idempotent_for_generated_markdown(content: str) -> None:
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "sample.md"
        path.write_text(content, encoding="utf-8", newline="")

        fix_xml_spacing.fix_file(path)
        after_first = path.read_text(encoding="utf-8")

        fix_xml_spacing.fix_file(path)
        after_second = path.read_text(encoding="utf-8")

        assert after_second == after_first
