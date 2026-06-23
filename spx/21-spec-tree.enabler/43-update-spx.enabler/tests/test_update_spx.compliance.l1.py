"""Compliance evidence for the two-file guide generator.

Three rules in ``update-spx.md`` with deterministic test evidence:

- NEVER: the render substitutes a product-specific string — a brace-delimited illustration
  token in the template passes through to the output unchanged.
- NEVER: an update keeps an unmodeled hand-prose edit — a tampered guide re-renders to the
  same output as a clean render from the same languages.
- ALWAYS: generation writes both guide files, never one without the other.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.update_spx import (
    ILLUSTRATION_TOKEN,
    LANG_PRIMARY,
    RUNTIME_CLAUDE,
    RUNTIME_CODEX,
    SESSION_ARCHIVE_RESULT_INSTRUCTION,
    SESSION_MANAGEMENT_HEADING,
    SESSION_RESULT_FRONTMATTER_FIELD,
    build_template,
    extract_markdown_section,
    load_update_spx_module,
    read_canonical_spx_template,
    write_template,
)

VERSION = "0.18.0"
JUNK_EDIT = "HAND-EDITED JUNK THAT MUST NOT SURVIVE A RE-RENDER"


def test_render_passes_brace_token_through_unchanged() -> None:
    module = load_update_spx_module()
    rendered = module.render(
        build_template(VERSION), (LANG_PRIMARY,), VERSION, RUNTIME_CLAUDE
    )
    assert ILLUSTRATION_TOKEN in rendered


def test_re_render_ignores_unmodeled_body_edits() -> None:
    module = load_update_spx_module()
    template = build_template(VERSION)
    guide = module.render(template, (LANG_PRIMARY,), VERSION, RUNTIME_CLAUDE)

    tampered = guide + f"\n\n## Hand Section\n\n{JUNK_EDIT}\n"
    updated = module.render(
        template, module.parse_languages(tampered), VERSION, RUNTIME_CLAUDE
    )

    assert JUNK_EDIT not in updated
    assert updated == module.render(template, (LANG_PRIMARY,), VERSION, RUNTIME_CLAUDE)


def test_generation_writes_both_guide_files(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, VERSION)

    exit_code = module.main(
        [
            "--template",
            str(template),
            "--spx-dir",
            str(tmp_path),
            "--languages",
            LANG_PRIMARY,
            "--write",
        ]
    )
    assert exit_code == 0

    # Every runtime's guide file is written — never one without the other.
    written = {
        name
        for name in module.RUNTIME_GUIDE_FILENAMES.values()
        if (tmp_path / name).is_file()
    }
    assert written == set(module.RUNTIME_GUIDE_FILENAMES.values())


def test_write_regenerates_a_drifted_guide(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, VERSION)
    args = [
        "--template",
        str(template),
        "--spx-dir",
        str(tmp_path),
        "--languages",
        LANG_PRIMARY,
    ]
    assert module.main([*args, "--write"]) == 0

    # Drift both guides by hand, then regenerate — the gate's basis is that --write
    # overwrites the drift, so a regenerate-and-diff catches a tampered guide.
    guides = [tmp_path / name for name in module.RUNTIME_GUIDE_FILENAMES.values()]
    for guide in guides:
        guide.write_text(guide.read_text() + "\n\nHAND DRIFT\n", encoding="utf-8")
    assert module.main([*args, "--write"]) == 0
    for guide in guides:
        assert "HAND DRIFT" not in guide.read_text(encoding="utf-8")


def test_no_rendered_guide_teaches_result_session_frontmatter() -> None:
    module = load_update_spx_module()
    template = read_canonical_spx_template()
    # Render the canonical template for each runtime and assert the rendered
    # Session Management section carries no result-frontmatter instruction —
    # exercising the generator's output, not just the authored template text.
    for runtime in (RUNTIME_CLAUDE, RUNTIME_CODEX):
        rendered = module.render(template, (LANG_PRIMARY,), VERSION, runtime)
        section = extract_markdown_section(rendered, SESSION_MANAGEMENT_HEADING)
        assert SESSION_ARCHIVE_RESULT_INSTRUCTION not in section
        assert SESSION_RESULT_FRONTMATTER_FIELD not in section
