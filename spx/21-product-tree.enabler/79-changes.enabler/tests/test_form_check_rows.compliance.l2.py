"""Compliance test for two 4.0 row forms the form check accepts.

Covers ``form-check-linked-heading`` and ``form-check-scenario-steps`` in
``../changes.md``. A Mapping heading whose subject is a slug link names that slug,
so the infrastructure line keyed by the slug satisfies the check. The indented
Given, When, Then and And lines after a ``+`` Scenario row belong to that row, so
the check asks no slug of them. Each case builds a synthetic repository with one
implementation-malleable Node, commits it as the Base, and checks one Draft. The
test is ``l2`` because it spawns ``git`` against synthetic repositories under
``tmp_path``.
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
NODE = "spx/21-thing.capability"
SPEC = f"{NODE}/thing.spec.md"
TEST_FILE = f"{NODE}/tests/test_thing.mapping.l1.py"
PRODUCT_SPEC = (
    "---\nid: 01a1e000-0000-7000-8000-000000000001\nkind: product\n---\n\n# Example\n"
)
NODE_SPEC = (
    "---\nid: 01a1e000-0000-7000-8000-000000000003\n---\n\n# Thing\n\n"
    "PROVIDES things\nSO THAT readers\nCAN read them\n\n## Assertions\n"
)


def load_form_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location("form_check_rows", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["form_check_rows"] = module
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


def commit_base(repo: pathlib.Path) -> str:
    git(repo.parent, "init", "-q", "-b", "main", str(repo))
    git(repo, "config", "commit.gpgsign", "false")
    for path, text in {
        "spx/example.spec.md": PRODUCT_SPEC,
        SPEC: NODE_SPEC,
        TEST_FILE: "def test_thing() -> None:\n    assert True\n",
    }.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return git(repo, "rev-parse", "HEAD")


def write_draft(directory: pathlib.Path, base: str, payload: list[str]) -> pathlib.Path:
    draft = directory / "draft.md"
    lines = [
        "---",
        "title: The thing reads things",
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
        "- Output: The thing reads things.",
        "- Why: Readers need things.",
        "- Verification: A test reads a thing.",
        "",
        "## Declarations",
        "",
        f"### {NODE}",
        "",
        *payload,
        "",
    ]
    draft.write_text("\n".join(lines), encoding="utf-8")
    return draft


def findings(
    repo: pathlib.Path, draft: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> list[dict[str, str]]:
    FORM_CHECK.main(["--root", str(repo), "--draft", str(draft)])
    return json.loads(capsys.readouterr().out).get("findings", [])


LINKED_MAPPING = [
    "```diff",
    "  ## Assertions",
    "+ ### Test.Mapping: [thing-kinds](tests/test_thing.mapping.l1.py)",
    "+ Each kind of thing maps to its reader.",
    "+ | Case | Kind | Reader |",
    "+ | ---- | ---- | ------ |",
    "+ | small | small | quick reader |",
    "```",
    "",
    "Infrastructure: thing-kinds none",
]

MULTI_LINE_SCENARIO = [
    "```diff",
    "  ## Assertions",
    "+ ### Test.Scenario: reading",
    "+ - read-one:",
    "+   - Given one thing",
    "+   - When a reader reads it",
    "+   - Then the reader holds exactly one thing",
    "+   - And the thing stays unchanged",
    "```",
    "",
    "Infrastructure: read-one none",
]

UNSLUGGED_ROW = [
    "```diff",
    "  ## Assertions",
    "+ ### Test.Scenario: reading",
    "+ - a reader reads a thing",
    "```",
    "",
    "Infrastructure: read-one none",
]


def test_linked_mapping_heading_takes_its_slugs_infrastructure_line(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = write_draft(tmp_path, commit_base(repo), LINKED_MAPPING)
    rules = [finding["rule"] for finding in findings(repo, draft, capsys)]
    assert "infrastructure-line" not in rules


def test_linked_mapping_heading_without_its_line_still_fails(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = write_draft(tmp_path, commit_base(repo), LINKED_MAPPING[:-2])
    details = [
        finding["detail"]
        for finding in findings(repo, draft, capsys)
        if finding["rule"] == "infrastructure-line"
    ]
    assert any("thing-kinds" in detail for detail in details)


def test_scenario_step_lines_belong_to_their_row(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = write_draft(tmp_path, commit_base(repo), MULTI_LINE_SCENARIO)
    rules = [finding["rule"] for finding in findings(repo, draft, capsys)]
    assert "body-lines-only" not in rules


def test_unslugged_row_still_fails(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = write_draft(tmp_path, commit_base(repo), UNSLUGGED_ROW)
    rules = [finding["rule"] for finding in findings(repo, draft, capsys)]
    assert "body-lines-only" in rules
