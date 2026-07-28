"""Level-1 property evidence for XML-spacing behavior."""

from __future__ import annotations

from hypothesis import given

from outcomeeng.hygiene.xml_spacing import fix_file
from outcomeeng_testing.generators.hygiene import (
    FencedMarkdownCase,
    fenced_markdown_cases,
    markdown_contents,
)
from outcomeeng_testing.harnesses.hygiene import (
    hygiene_generated_evidence,
    markdown_file,
)


@hygiene_generated_evidence
@given(content=markdown_contents())
def test_fix_file_is_idempotent_for_generated_markdown(content: str) -> None:
    with markdown_file(content) as path:
        fix_file(path)
        after_first = path.read_bytes()

        fix_file(path)

        assert path.read_bytes() == after_first


@hygiene_generated_evidence
@given(case=fenced_markdown_cases())
def test_fix_file_preserves_generated_fenced_content(
    case: FencedMarkdownCase,
) -> None:
    with markdown_file(case.content) as path:
        fix_file(path)

        assert path.read_text(encoding="utf-8") == case.expected_content
