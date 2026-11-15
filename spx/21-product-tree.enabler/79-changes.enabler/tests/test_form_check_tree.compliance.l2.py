"""Compliance test for how the form check recognizes a Product Tree at the Base.

Covers ``form-check-tree`` in ``../changes.md``. The form check treats a repository
as having a Product Tree exactly when the tree of the record's Base holds, directly
under ``spx/``, a root Product spec or an indexed Node directory. Otherwise it judges
every Declarations heading as a path from the repository root. It reads no directory
of the checkout for this.

Each case builds a synthetic repository, commits a Base, and checks one fixed Draft
whose only subsection is headed by the root path ``docs/guide.md``. The observable is
whether the check reports the ``subsection-headings`` finding that a heading must be a
path from ``spx/``. The test is ``l2`` because it spawns ``git`` against synthetic
repositories under ``tmp_path``.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.form_check import (
    Intent,
    commit_base,
    findings,
    write_draft,
)

HEADING = "docs/guide.md"
SPX_HEADING_DETAIL = "the heading is a path from spx/"

PRODUCT_SPEC = (
    "---\nid: 01a1e000-0000-7000-8000-000000000001\nkind: product\n---\n\n# Example\n"
)
PLAIN_SPEC = "---\nid: 01a1e000-0000-7000-8000-000000000002\n---\n\n# Example\n"
DECISION = "# Loose decision\n"
INTENT = Intent(
    title="The guide names its intro",
    output="The guide opens with its intro.",
    why="Readers find the intro first.",
    verification="The audit at close finds the intro line.",
)
PAYLOAD = ["```diff", "  # Guide", "+ Read this first.", "```"]


def commit_guide_base(repo: pathlib.Path, files: dict[str, str]) -> str:
    """Commit ``docs/guide.md`` and ``files`` as the Base; return its commit."""
    return commit_base(repo, {HEADING: "# Guide\n\nIntro.\n", **files})


def write_guide_draft(directory: pathlib.Path, base: str) -> pathlib.Path:
    return write_draft(directory, base, INTENT, HEADING, PAYLOAD)


def spx_heading_finding(
    repo: pathlib.Path, draft: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> bool:
    return any(
        finding["rule"] == "subsection-headings"
        and finding["location"] == HEADING
        and finding["detail"] == SPX_HEADING_DETAIL
        for finding in findings(repo, draft, capsys)
    )


NO_TREE_BASES = {
    "loose-decision-and-local": {
        "spx/15-loose.adr.md": DECISION,
        "spx/local/changes.md": "# Changes\n",
    },
    "unindexed-node-suffix-under-local": {
        "spx/local/fixtures/not-a-node.capability/notes.md": "# Notes\n",
    },
    "spec-without-product-kind": {"spx/example.spec.md": PLAIN_SPEC},
    "placeholder-index": {"spx/NN-later.capability/later.md": "# Later\n"},
}

TREE_BASES = {
    "root-product-spec-only": {"spx/example.spec.md": PRODUCT_SPEC},
    "root-product-spec-3x": {"spx/example.product.md": "# Example\n"},
    "indexed-node-4x": {"spx/21-thing.capability/thing.spec.md": PLAIN_SPEC},
    "indexed-node-3x": {"spx/21-thing.enabler/thing.md": "# Thing\n"},
    "fractional-index-node": {"spx/21.54-thing.domain/thing.spec.md": PLAIN_SPEC},
}


@pytest.mark.parametrize("files", NO_TREE_BASES.values(), ids=NO_TREE_BASES.keys())
def test_base_without_product_tree_judges_root_paths(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], files: dict[str, str]
) -> None:
    repo = tmp_path / "repo"
    base = commit_guide_base(repo, files)
    draft = write_guide_draft(tmp_path, base)
    assert not spx_heading_finding(repo, draft, capsys)


@pytest.mark.parametrize("files", TREE_BASES.values(), ids=TREE_BASES.keys())
def test_base_with_product_tree_requires_spx_paths(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], files: dict[str, str]
) -> None:
    repo = tmp_path / "repo"
    base = commit_guide_base(repo, files)
    draft = write_guide_draft(tmp_path, base)
    assert spx_heading_finding(repo, draft, capsys)


def test_checkout_tree_does_not_create_a_product_tree(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    base = commit_guide_base(repo, NO_TREE_BASES["loose-decision-and-local"])
    node = repo / "spx/21-thing.capability"
    node.mkdir(parents=True)
    (node / "thing.spec.md").write_text(PLAIN_SPEC, encoding="utf-8")
    (repo / "spx/example.spec.md").write_text(PRODUCT_SPEC, encoding="utf-8")
    draft = write_guide_draft(tmp_path, base)
    assert not spx_heading_finding(repo, draft, capsys)


def test_checkout_without_spx_keeps_the_base_product_tree(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    base = commit_guide_base(repo, TREE_BASES["root-product-spec-only"])
    (repo / "spx/example.spec.md").unlink()
    (repo / "spx").rmdir()
    draft = write_guide_draft(tmp_path, base)
    assert spx_heading_finding(repo, draft, capsys)
