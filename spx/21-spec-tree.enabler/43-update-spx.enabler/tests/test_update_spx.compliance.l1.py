"""Compliance evidence: a re-render reflects only the template and the enabled languages.

Two NEVER rules in ``update-spx.md``:

- The render substitutes no product-specific string — a brace-delimited illustration
  token in the template passes through to the output unchanged.
- An update keeps no unmodeled hand-prose edit — a tampered guide re-renders to the same
  output as a clean render from the same languages, proving the body edit has no effect.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.update_spx import (
    ILLUSTRATION_TOKEN,
    LANG_PRIMARY,
    SESSION_ARCHIVE_RESULT_INSTRUCTION,
    SESSION_MANAGEMENT_HEADING,
    SESSION_RESULT_FRONTMATTER_FIELD,
    build_template,
    extract_markdown_section,
    load_update_spx_module,
    read_canonical_spx_template,
)

VERSION = "0.18.0"
JUNK_EDIT = "HAND-EDITED JUNK THAT MUST NOT SURVIVE A RE-RENDER"


def test_render_passes_brace_token_through_unchanged() -> None:
    module = load_update_spx_module()
    rendered = module.render(build_template(VERSION), (LANG_PRIMARY,), VERSION)
    assert ILLUSTRATION_TOKEN in rendered


def test_re_render_ignores_unmodeled_body_edits() -> None:
    module = load_update_spx_module()
    template = build_template(VERSION)
    guide = module.render(template, (LANG_PRIMARY,), VERSION)

    tampered = guide + f"\n\n## Hand Section\n\n{JUNK_EDIT}\n"
    updated = module.render(template, module.parse_languages(tampered), VERSION)

    assert JUNK_EDIT not in updated
    assert updated == module.render(template, (LANG_PRIMARY,), VERSION)


def test_canonical_template_does_not_require_session_result_frontmatter() -> None:
    session_section = extract_markdown_section(
        read_canonical_spx_template(),
        SESSION_MANAGEMENT_HEADING,
    )

    assert SESSION_ARCHIVE_RESULT_INSTRUCTION not in session_section
    assert SESSION_RESULT_FRONTMATTER_FIELD not in session_section
