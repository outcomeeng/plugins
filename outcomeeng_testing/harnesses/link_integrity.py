"""Fixture writers for evidence-link-integrity tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_testing.evals.link_integrity import (
    BrokenEvalLink,
    BrokenTestLink,
    EvalLink,
    TestLink,
    find_eval_links,
    find_test_links,
    validate_eval_links,
    validate_test_links,
)


def write_eval_dir(directory: Path, slug: str) -> Path:
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


def write_test_file(directory: Path, name: str) -> Path:
    tests_dir = directory / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_path = tests_dir / name
    test_path.write_text("def test_placeholder() -> None: pass\n", encoding="utf-8")
    return test_path


def assert_link_integrity_contract() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _assert_find_eval_links_finds_resolvable_link(root / "eval-resolvable")
        _assert_find_eval_links_ignores_non_eval_markdown_links(root / "eval-nonlink")
        _assert_find_eval_links_ignores_inline_code_spans(root / "eval-inline")
        _assert_find_eval_links_ignores_fenced_code_blocks(root / "eval-fenced")
        _assert_find_eval_links_returns_all_links_across_files(root / "eval-all")
        _assert_validate_eval_links_returns_empty_when_all_resolve(root / "eval-valid")
        _assert_validate_eval_links_reports_missing_eval_toml(root / "eval-missing")
        _assert_validate_eval_links_rejects_link_to_non_eval_toml(root / "eval-nontoml")
        _assert_validate_eval_links_resolves_paths_relative_to_source(
            root / "eval-deep"
        )
        _assert_validate_eval_links_rejects_target_outside_evals_dir(
            root / "eval-loose"
        )
        _assert_find_test_links_finds_resolvable_link(root / "test-resolvable")
        _assert_find_test_links_ignores_inline_code_spans(root / "test-inline")
        _assert_find_test_links_ignores_fenced_code_blocks(root / "test-fenced")
        _assert_validate_test_links_returns_empty_when_all_resolve(root / "test-valid")
        _assert_validate_test_links_reports_missing_target(root / "test-missing")
        _assert_validate_test_links_rejects_non_test_filename(root / "test-nonname")
        _assert_validate_test_links_rejects_non_python_target(root / "test-nonpython")
        _assert_validate_test_links_resolves_paths_relative_to_source(
            root / "test-deep"
        )
        _assert_validate_test_links_rejects_target_outside_tests_dir(
            root / "test-loose"
        )


def _assert_find_eval_links_finds_resolvable_link(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    write_eval_dir(node_dir, "rule-one")
    spec = node_dir / "spec.md"
    spec.write_text(
        "- NEVER: bad thing ([eval](evals/rule-one/eval.toml))\n",
        encoding="utf-8",
    )

    links = find_eval_links(root)

    assert len(links) == 1
    assert isinstance(links[0], EvalLink)
    assert links[0].source.resolve() == spec.resolve()
    assert (
        links[0].target.resolve()
        == (node_dir / "evals" / "rule-one" / EVAL_TOML_FILENAME).resolve()
    )


def _assert_find_eval_links_ignores_non_eval_markdown_links(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    spec = node_dir / "spec.md"
    spec.write_text(
        "- ALWAYS: do thing ([test](tests/test_thing.conformance.l1.py))\n"
        "- See [related doc](other.md)\n",
        encoding="utf-8",
    )

    assert find_eval_links(root) == []


def _assert_find_eval_links_ignores_inline_code_spans(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    spec = node_dir / "spec.md"
    spec.write_text(
        "Sample link form: `[eval](evals/{rule-slug}/eval.toml)`. "
        "The runner consumes it.\n",
        encoding="utf-8",
    )

    assert find_eval_links(root) == []


def _assert_find_eval_links_ignores_fenced_code_blocks(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    spec = node_dir / "spec.md"
    spec.write_text(
        "Example assertion:\n\n"
        "```markdown\n"
        "- ALWAYS: foo ([eval](evals/example/eval.toml))\n"
        "```\n",
        encoding="utf-8",
    )

    assert find_eval_links(root) == []


def _assert_find_eval_links_returns_all_links_across_files(root: Path) -> None:
    node_a = root / "spx" / "a"
    node_b = root / "spx" / "b"
    node_a.mkdir(parents=True)
    node_b.mkdir(parents=True)
    write_eval_dir(node_a, "rule-a")
    write_eval_dir(node_b, "rule-b")
    (node_a / "spec.md").write_text(
        "([eval](evals/rule-a/eval.toml))\n",
        encoding="utf-8",
    )
    (node_b / "spec.md").write_text(
        "([eval](evals/rule-b/eval.toml))\n",
        encoding="utf-8",
    )

    assert len(find_eval_links(root)) == 2


def _assert_validate_eval_links_returns_empty_when_all_resolve(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    write_eval_dir(node_dir, "rule-one")
    (node_dir / "spec.md").write_text(
        "([eval](evals/rule-one/eval.toml))\n",
        encoding="utf-8",
    )

    assert validate_eval_links(root) == []


def _assert_validate_eval_links_reports_missing_eval_toml(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    (node_dir / "spec.md").write_text(
        "([eval](evals/missing-rule/eval.toml))\n",
        encoding="utf-8",
    )

    broken = validate_eval_links(root)

    assert len(broken) == 1
    assert isinstance(broken[0], BrokenEvalLink)
    assert "missing-rule" in str(broken[0].target)


def _assert_validate_eval_links_rejects_link_to_non_eval_toml(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    (node_dir / "spec.md").write_text(
        "([eval](evals/rule/cases.jsonl))\n",
        encoding="utf-8",
    )
    (node_dir / "evals" / "rule").mkdir(parents=True)
    (node_dir / "evals" / "rule" / "cases.jsonl").write_text("", encoding="utf-8")

    broken = validate_eval_links(root)

    assert len(broken) == 1
    assert "eval.toml" in broken[0].reason


def _assert_validate_eval_links_resolves_paths_relative_to_source(root: Path) -> None:
    deep_node = root / "spx" / "a" / "b" / "c"
    deep_node.mkdir(parents=True)
    write_eval_dir(deep_node, "deep-rule")
    (deep_node / "spec.md").write_text(
        "([eval](evals/deep-rule/eval.toml))\n",
        encoding="utf-8",
    )

    assert validate_eval_links(root) == []


def _assert_validate_eval_links_rejects_target_outside_evals_dir(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    loose_dir = node_dir / "evals"
    loose_dir.mkdir()
    (loose_dir / EVAL_TOML_FILENAME).write_text(
        'title = "x"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
        encoding="utf-8",
    )
    (node_dir / "spec.md").write_text(
        "([eval](evals/eval.toml))\n",
        encoding="utf-8",
    )

    broken = validate_eval_links(root)

    assert len(broken) == 1
    assert "evals/" in broken[0].reason


def _assert_find_test_links_finds_resolvable_link(root: Path) -> None:
    write_test_file(root, "test_thing.conformance.l1.py")
    (root / "spec.md").write_text(
        "Assertion ([test](tests/test_thing.conformance.l1.py))\n",
        encoding="utf-8",
    )

    links = find_test_links(root)

    assert len(links) == 1
    assert isinstance(links[0], TestLink)
    assert links[0].target.name == "test_thing.conformance.l1.py"


def _assert_find_test_links_ignores_inline_code_spans(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "doc.md").write_text(
        "The link form `[test](path/to/test.py)` is required.\n",
        encoding="utf-8",
    )

    assert find_test_links(root) == []


def _assert_find_test_links_ignores_fenced_code_blocks(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "doc.md").write_text(
        "```\nAssertion ([test](tests/test_x.py))\n```\n",
        encoding="utf-8",
    )

    assert find_test_links(root) == []


def _assert_validate_test_links_returns_empty_when_all_resolve(root: Path) -> None:
    write_test_file(root, "test_x.conformance.l1.py")
    (root / "spec.md").write_text(
        "([test](tests/test_x.conformance.l1.py))\n",
        encoding="utf-8",
    )

    assert validate_test_links(root) == []


def _assert_validate_test_links_reports_missing_target(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "spec.md").write_text(
        "([test](tests/missing.py))\n",
        encoding="utf-8",
    )

    broken = validate_test_links(root)

    assert len(broken) == 1
    assert isinstance(broken[0], BrokenTestLink)
    assert "does not exist" in broken[0].reason


def _assert_validate_test_links_rejects_non_test_filename(root: Path) -> None:
    helper = root / "tests" / "helper.py"
    helper.parent.mkdir(parents=True)
    helper.write_text("# helper\n", encoding="utf-8")
    (root / "spec.md").write_text(
        "([test](tests/helper.py))\n",
        encoding="utf-8",
    )

    broken = validate_test_links(root)

    assert len(broken) == 1
    assert "pytest collectable" in broken[0].reason


def _assert_validate_test_links_rejects_non_python_target(root: Path) -> None:
    txt_file = root / "tests" / "test_thing.txt"
    txt_file.parent.mkdir(parents=True)
    txt_file.write_text("not python\n", encoding="utf-8")
    (root / "spec.md").write_text(
        "([test](tests/test_thing.txt))\n",
        encoding="utf-8",
    )

    broken = validate_test_links(root)

    assert len(broken) == 1
    assert "pytest collectable" in broken[0].reason


def _assert_validate_test_links_resolves_paths_relative_to_source(root: Path) -> None:
    deep_node = root / "spx" / "a" / "b"
    deep_node.mkdir(parents=True)
    write_test_file(deep_node, "test_deep.conformance.l1.py")
    (deep_node / "spec.md").write_text(
        "([test](tests/test_deep.conformance.l1.py))\n",
        encoding="utf-8",
    )

    assert validate_test_links(root) == []


def _assert_validate_test_links_rejects_target_outside_tests_dir(root: Path) -> None:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    loose_test = node_dir / "test_loose.conformance.l1.py"
    loose_test.write_text("def test_placeholder() -> None: pass\n", encoding="utf-8")
    (node_dir / "spec.md").write_text(
        "([test](test_loose.conformance.l1.py))\n",
        encoding="utf-8",
    )

    broken = validate_test_links(root)

    assert len(broken) == 1
    assert isinstance(broken[0], BrokenTestLink)
    assert "tests/" in broken[0].reason
