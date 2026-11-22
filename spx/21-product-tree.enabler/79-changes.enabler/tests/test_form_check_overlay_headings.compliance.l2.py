"""Compliance test for repository-root headings the changes overlay admits.

Covers ``form-check-overlay-headings`` in ``../changes.md``. When the Base's
``spx/local/changes.md`` holds the line ``- Repository-root headings: admitted``,
the form check judges a Declarations heading outside ``spx/`` as a path from the
repository root and accepts the line edits, ``new file``, ``deleted file``, move
and replacement operations on that file. Without the line, it fails such a heading
with ``subsection-headings``.

Each case builds a synthetic repository whose Base holds a root Product spec, so
the Base holds a Product Tree, and checks one Draft whose only subsection names a
file under ``docs/``. The observable is whether the check reports a
``subsection-headings`` or ``operation-kinds`` finding on that subsection. The test
is ``l2`` because it spawns ``git`` against synthetic repositories under
``tmp_path``.
"""

from __future__ import annotations

import pathlib
from collections.abc import Sequence

import pytest

from outcomeeng_testing.harnesses.form_check import (
    Intent,
    commit_base,
    findings,
    write_draft,
)

ADMITTING_LINE = "- Repository-root headings: admitted"
OVERLAY = "spx/local/changes.md"
GUIDE = "docs/guide.md"
PRODUCT_SPEC = (
    "---\nid: 01a1e000-0000-7000-8000-000000000001\nkind: product\n---\n\n# Example\n"
)
ADMITTING_OVERLAY = f"# Changes\n\n- Repository: `example/changes`\n{ADMITTING_LINE}\n"
SILENT_OVERLAY = "# Changes\n\n- Repository: `example/changes`\n"
INTENT = Intent(
    title="The guide names its intro",
    output="The guide opens with its intro.",
    why="Readers find the intro first.",
    verification="The audit at close finds the intro line.",
)
JUDGED_RULES = frozenset({"subsection-headings", "operation-kinds"})

OPERATIONS: dict[str, tuple[str, Sequence[str]]] = {
    "line-edit": (GUIDE, ["```diff", "  # Guide", "+ Read this first.", "```"]),
    "new-file": ("docs/setup.md", ["```diff", "new file", "+ # Setup", "```"]),
    "deleted-file": (GUIDE, ["```diff", "deleted file", "```"]),
    "replacement": (GUIDE, ["````markdown", "# Guide", "", "Read this first.", "````"]),
    "move": (
        GUIDE,
        ["```diff", f"rename from {GUIDE}", "rename to docs/intro.md", "```"],
    ),
}


def commit_tree_base(repo: pathlib.Path, overlay: str | None) -> str:
    """Commit a Product Tree Base holding ``docs/guide.md`` and, when given, the overlay."""
    files = {"spx/example.spec.md": PRODUCT_SPEC, GUIDE: "# Guide\n\nIntro.\n"}
    if overlay is not None:
        files[OVERLAY] = overlay
    return commit_base(repo, files)


def judged_findings(
    repo: pathlib.Path,
    draft: pathlib.Path,
    heading: str,
    capsys: pytest.CaptureFixture[str],
) -> list[dict[str, str]]:
    return [
        finding
        for finding in findings(repo, draft, capsys)
        if finding["rule"] in JUDGED_RULES and finding["location"] == heading
    ]


@pytest.mark.parametrize("operation", OPERATIONS.values(), ids=OPERATIONS.keys())
def test_admitting_overlay_accepts_root_headings(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    operation: tuple[str, Sequence[str]],
) -> None:
    heading, payload = operation
    repo = tmp_path / "repo"
    base = commit_tree_base(repo, ADMITTING_OVERLAY)
    draft = write_draft(tmp_path, base, INTENT, heading, payload)
    assert judged_findings(repo, draft, heading, capsys) == []


OVERLAYS_WITHOUT_LINE = {"silent-overlay": SILENT_OVERLAY, "no-overlay": None}


@pytest.mark.parametrize(
    "overlay", OVERLAYS_WITHOUT_LINE.values(), ids=OVERLAYS_WITHOUT_LINE.keys()
)
@pytest.mark.parametrize("operation", OPERATIONS.values(), ids=OPERATIONS.keys())
def test_without_the_line_root_headings_fail(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    operation: tuple[str, Sequence[str]],
    overlay: str | None,
) -> None:
    heading, payload = operation
    repo = tmp_path / "repo"
    base = commit_tree_base(repo, overlay)
    draft = write_draft(tmp_path, base, INTENT, heading, payload)
    rules = {
        finding["rule"] for finding in judged_findings(repo, draft, heading, capsys)
    }
    assert "subsection-headings" in rules


def test_line_in_the_checkout_alone_admits_nothing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    heading, payload = OPERATIONS["line-edit"]
    repo = tmp_path / "repo"
    base = commit_tree_base(repo, SILENT_OVERLAY)
    (repo / OVERLAY).write_text(ADMITTING_OVERLAY, encoding="utf-8")
    draft = write_draft(tmp_path, base, INTENT, heading, payload)
    rules = {
        finding["rule"] for finding in judged_findings(repo, draft, heading, capsys)
    }
    assert "subsection-headings" in rules
