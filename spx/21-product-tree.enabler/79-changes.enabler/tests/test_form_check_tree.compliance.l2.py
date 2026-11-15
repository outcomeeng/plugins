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

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from types import ModuleType

import pytest

SCRIPT = (
    pathlib.Path(__file__).resolve().parents[4]
    / "src/plugins/product-tree/skills/change-standards/scripts/form_check.py"
)
HEADING = "docs/guide.md"
SPX_HEADING_DETAIL = "the heading is a path from spx/"

PRODUCT_SPEC = (
    "---\nid: 01a1e000-0000-7000-8000-000000000001\nkind: product\n---\n\n# Example\n"
)
PLAIN_SPEC = "---\nid: 01a1e000-0000-7000-8000-000000000002\n---\n\n# Example\n"
DECISION = "# Loose decision\n"


def load_form_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location("form_check", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["form_check"] = module
    spec.loader.exec_module(module)
    return module


FORM_CHECK = load_form_check()


def git(repo: pathlib.Path, *argv: str) -> str:
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    completed = subprocess.run(
        ["git", *argv], cwd=repo, env=env, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def commit_base(repo: pathlib.Path, files: dict[str, str]) -> str:
    """Commit ``docs/guide.md`` and ``files`` as the Base; return its commit."""
    git(repo.parent, "init", "-q", "-b", "main", str(repo))
    git(repo, "config", "commit.gpgsign", "false")
    for path, text in {"docs/guide.md": "# Guide\n\nIntro.\n", **files}.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return git(repo, "rev-parse", "HEAD")


def write_draft(directory: pathlib.Path, base: str) -> pathlib.Path:
    draft = directory / "draft.md"
    draft.write_text(
        "\n".join(
            [
                "---",
                "title: The guide names its intro",
                "product: plugins",
                "maturity: Proposed",
                "lifecycle: Submitted",
                "parent: null",
                "predecessors: []",
                "blockers: []",
                f"base: {base}",
                "priority: null",
                "primary_value: null",
                "investment: null",
                "---",
                "",
                "## Statement of Intent",
                "",
                "- Output: The guide opens with its intro.",
                "- Why: Readers find the intro first.",
                "- Verification: The audit at close finds the intro line.",
                "",
                "## Declarations",
                "",
                f"### {HEADING}",
                "",
                "```diff",
                "  # Guide",
                "+ Read this first.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return draft


def spx_heading_finding(
    repo: pathlib.Path, draft: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> bool:
    FORM_CHECK.main(["--root", str(repo), "--draft", str(draft)])
    result = json.loads(capsys.readouterr().out)
    return any(
        finding["rule"] == "subsection-headings"
        and finding["location"] == HEADING
        and finding["detail"] == SPX_HEADING_DETAIL
        for finding in result.get("findings", [])
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
    base = commit_base(repo, files)
    draft = write_draft(tmp_path, base)
    assert not spx_heading_finding(repo, draft, capsys)


@pytest.mark.parametrize("files", TREE_BASES.values(), ids=TREE_BASES.keys())
def test_base_with_product_tree_requires_spx_paths(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], files: dict[str, str]
) -> None:
    repo = tmp_path / "repo"
    base = commit_base(repo, files)
    draft = write_draft(tmp_path, base)
    assert spx_heading_finding(repo, draft, capsys)


def test_checkout_tree_does_not_create_a_product_tree(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    base = commit_base(repo, NO_TREE_BASES["loose-decision-and-local"])
    node = repo / "spx/21-thing.capability"
    node.mkdir(parents=True)
    (node / "thing.spec.md").write_text(PLAIN_SPEC, encoding="utf-8")
    (repo / "spx/example.spec.md").write_text(PRODUCT_SPEC, encoding="utf-8")
    draft = write_draft(tmp_path, base)
    assert not spx_heading_finding(repo, draft, capsys)


def test_checkout_without_spx_keeps_the_base_product_tree(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    base = commit_base(repo, TREE_BASES["root-product-spec-only"])
    (repo / "spx/example.spec.md").unlink()
    (repo / "spx").rmdir()
    draft = write_draft(tmp_path, base)
    assert spx_heading_finding(repo, draft, capsys)
