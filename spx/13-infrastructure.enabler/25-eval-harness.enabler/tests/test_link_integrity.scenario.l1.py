"""Scenario tests for the [eval] link-integrity walker.

The walker scans markdown files for ``[eval](path)`` references and
asserts each target resolves to an existing ``eval.toml``. The
marketplace script under ``outcomeeng/scripts/`` invokes the walker;
``just check`` consumes the walker's exit code.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.evals.link_integrity import (
    BrokenEvalLink,
    EvalLink,
    find_eval_links,
    validate_eval_links,
)


EVAL_TOML_FILENAME = "eval.toml"


def _write_eval_dir(directory: Path, slug: str) -> Path:
    eval_dir = directory / "evals" / slug
    eval_dir.mkdir(parents=True)
    toml_path = eval_dir / EVAL_TOML_FILENAME
    toml_path.write_text(
        f'title = "{slug}"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    (eval_dir / "prompt.md").write_text("", encoding="utf-8")
    return toml_path


def test_find_eval_links_finds_resolvable_link(tmp_path: Path) -> None:
    node_dir = tmp_path / "spx" / "node"
    node_dir.mkdir(parents=True)
    _write_eval_dir(node_dir, "rule-one")
    spec = node_dir / "spec.md"
    spec.write_text(
        "- NEVER: bad thing ([eval](evals/rule-one/eval.toml))\n",
        encoding="utf-8",
    )

    links = find_eval_links(tmp_path)

    assert len(links) == 1
    assert isinstance(links[0], EvalLink)
    assert links[0].source.resolve() == spec.resolve()
    assert (
        links[0].target.resolve()
        == (node_dir / "evals" / "rule-one" / EVAL_TOML_FILENAME).resolve()
    )


def test_find_eval_links_ignores_non_eval_markdown_links(tmp_path: Path) -> None:
    node_dir = tmp_path / "spx" / "node"
    node_dir.mkdir(parents=True)
    spec = node_dir / "spec.md"
    spec.write_text(
        "- ALWAYS: do thing ([test](tests/test_thing.scenario.l1.py))\n"
        "- See [related doc](other.md)\n",
        encoding="utf-8",
    )

    links = find_eval_links(tmp_path)

    assert links == []


def test_find_eval_links_returns_all_links_across_files(tmp_path: Path) -> None:
    node_a = tmp_path / "spx" / "a"
    node_b = tmp_path / "spx" / "b"
    node_a.mkdir(parents=True)
    node_b.mkdir(parents=True)
    _write_eval_dir(node_a, "rule-a")
    _write_eval_dir(node_b, "rule-b")
    (node_a / "spec.md").write_text(
        "([eval](evals/rule-a/eval.toml))\n",
        encoding="utf-8",
    )
    (node_b / "spec.md").write_text(
        "([eval](evals/rule-b/eval.toml))\n",
        encoding="utf-8",
    )

    links = find_eval_links(tmp_path)

    assert len(links) == 2


def test_validate_eval_links_returns_empty_when_all_resolve(tmp_path: Path) -> None:
    node_dir = tmp_path / "spx" / "node"
    node_dir.mkdir(parents=True)
    _write_eval_dir(node_dir, "rule-one")
    (node_dir / "spec.md").write_text(
        "([eval](evals/rule-one/eval.toml))\n",
        encoding="utf-8",
    )

    broken = validate_eval_links(tmp_path)

    assert broken == []


def test_validate_eval_links_reports_missing_eval_toml(tmp_path: Path) -> None:
    node_dir = tmp_path / "spx" / "node"
    node_dir.mkdir(parents=True)
    (node_dir / "spec.md").write_text(
        "([eval](evals/missing-rule/eval.toml))\n",
        encoding="utf-8",
    )

    broken = validate_eval_links(tmp_path)

    assert len(broken) == 1
    assert isinstance(broken[0], BrokenEvalLink)
    assert "missing-rule" in str(broken[0].target)


def test_validate_eval_links_rejects_link_to_non_eval_toml(tmp_path: Path) -> None:
    node_dir = tmp_path / "spx" / "node"
    node_dir.mkdir(parents=True)
    (node_dir / "spec.md").write_text(
        "([eval](evals/rule/cases.jsonl))\n",
        encoding="utf-8",
    )
    (node_dir / "evals" / "rule").mkdir(parents=True)
    (node_dir / "evals" / "rule" / "cases.jsonl").write_text("", encoding="utf-8")

    broken = validate_eval_links(tmp_path)

    assert len(broken) == 1
    assert "eval.toml" in broken[0].reason


def test_validate_eval_links_resolves_paths_relative_to_source_file(
    tmp_path: Path,
) -> None:
    deep_node = tmp_path / "spx" / "a" / "b" / "c"
    deep_node.mkdir(parents=True)
    _write_eval_dir(deep_node, "deep-rule")
    (deep_node / "spec.md").write_text(
        "([eval](evals/deep-rule/eval.toml))\n",
        encoding="utf-8",
    )

    broken = validate_eval_links(tmp_path)

    assert broken == []
