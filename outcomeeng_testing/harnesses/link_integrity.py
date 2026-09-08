"""Fixture layouts for evidence-link-integrity tests.

Each writer prepares one markdown layout under a caller-owned root and
returns the paths the linked test needs. No writer calls an assertion API,
accepts an expected outcome, or returns a verdict; every predicate lives in
the linked test.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng_evals.definition import EVAL_TOML_FILENAME


@dataclass(frozen=True)
class LinkLayout:
    """One prepared layout: the markdown source and the evidence target it names."""

    source: Path
    target: Path


@contextmanager
def link_integrity_root() -> Iterator[Path]:
    """Yield a disposable root for one layout and remove it on exit."""
    with TemporaryDirectory() as tmp:
        yield Path(tmp)


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


def _node(root: Path) -> Path:
    node_dir = root / "spx" / "node"
    node_dir.mkdir(parents=True)
    return node_dir


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- eval-link layouts ---------------------------------------------------


def resolvable_eval_layout(root: Path) -> LinkLayout:
    node_dir = _node(root)
    toml_path = write_eval_dir(node_dir, "rule-one")
    spec = _write(
        node_dir / "spec.md",
        "- NEVER: bad thing ([eval](evals/rule-one/eval.toml))\n",
    )
    return LinkLayout(source=spec, target=toml_path)


def non_eval_markdown_link_layout(root: Path) -> Path:
    return _write(
        _node(root) / "spec.md",
        "- ALWAYS: do thing ([test](tests/test_thing.conformance.l1.py))\n"
        "- See [related doc](other.md)\n",
    )


def inline_code_span_eval_layout(root: Path) -> Path:
    return _write(
        _node(root) / "spec.md",
        "Sample link form: `[eval](evals/{rule-slug}/eval.toml)`. "
        "The runner consumes it.\n",
    )


def multi_backtick_inline_eval_layout(root: Path) -> Path:
    return _write(
        _node(root) / "spec.md",
        "A fence (`` ``` ``) wraps examples; the inline form "
        "`[eval](evals/{rule-slug}/eval.toml)` is prose.\n",
    )


def fenced_block_eval_layout(root: Path) -> Path:
    return _write(
        _node(root) / "spec.md",
        "Example assertion:\n\n"
        "```markdown\n"
        "- ALWAYS: foo ([eval](evals/example/eval.toml))\n"
        "```\n",
    )


def two_node_eval_layout(root: Path) -> tuple[LinkLayout, LinkLayout]:
    layouts: list[LinkLayout] = []
    for name in ("a", "b"):
        node_dir = root / "spx" / name
        node_dir.mkdir(parents=True)
        toml_path = write_eval_dir(node_dir, f"rule-{name}")
        spec = _write(node_dir / "spec.md", f"([eval](evals/rule-{name}/eval.toml))\n")
        layouts.append(LinkLayout(source=spec, target=toml_path))
    return layouts[0], layouts[1]


def missing_eval_toml_layout(root: Path) -> LinkLayout:
    node_dir = _node(root)
    spec = _write(node_dir / "spec.md", "([eval](evals/missing-rule/eval.toml))\n")
    return LinkLayout(
        source=spec, target=node_dir / "evals" / "missing-rule" / EVAL_TOML_FILENAME
    )


def non_toml_eval_target_layout(root: Path) -> LinkLayout:
    node_dir = _node(root)
    cases = _write(node_dir / "evals" / "rule" / "cases.jsonl", "")
    spec = _write(node_dir / "spec.md", "([eval](evals/rule/cases.jsonl))\n")
    return LinkLayout(source=spec, target=cases)


def deep_eval_layout(root: Path) -> LinkLayout:
    deep_node = root / "spx" / "a" / "b" / "c"
    deep_node.mkdir(parents=True)
    toml_path = write_eval_dir(deep_node, "deep-rule")
    spec = _write(deep_node / "spec.md", "([eval](evals/deep-rule/eval.toml))\n")
    return LinkLayout(source=spec, target=toml_path)


def loose_eval_toml_layout(root: Path) -> LinkLayout:
    node_dir = _node(root)
    toml_path = _write(
        node_dir / "evals" / EVAL_TOML_FILENAME,
        'title = "x"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
    )
    spec = _write(node_dir / "spec.md", "([eval](evals/eval.toml))\n")
    return LinkLayout(source=spec, target=toml_path)


# --- test-link layouts ---------------------------------------------------


def resolvable_test_layout(root: Path) -> LinkLayout:
    test_path = write_test_file(root, "test_thing.conformance.l1.py")
    spec = _write(
        root / "spec.md",
        "Assertion ([test](tests/test_thing.conformance.l1.py))\n",
    )
    return LinkLayout(source=spec, target=test_path)


def inline_code_span_test_layout(root: Path) -> Path:
    return _write(
        root / "doc.md",
        "The link form `[test](path/to/test.py)` is required.\n",
    )


def multi_backtick_inline_test_layout(root: Path) -> Path:
    return _write(
        root / "doc.md",
        "A fence (`` ``` ``) wraps examples; the inline form "
        "`[test](tests/inline.py)` is prose.\n"
        "\n"
        "```markdown\n"
        "Assertion ([test](tests/fenced.py))\n"
        "```\n",
    )


def fenced_block_test_layout(root: Path) -> Path:
    return _write(root / "doc.md", "```\nAssertion ([test](tests/test_x.py))\n```\n")


def longer_closing_fence_test_layout(root: Path) -> LinkLayout:
    test_path = write_test_file(root, "test_after.conformance.l1.py")
    spec = _write(
        root / "doc.md",
        "```\n"
        "Assertion ([test](tests/fenced.py))\n"
        "````\n"
        "Assertion ([test](tests/test_after.conformance.l1.py))\n",
    )
    return LinkLayout(source=spec, target=test_path)


def tilde_fenced_test_layout(root: Path) -> Path:
    return _write(root / "doc.md", "~~~\nAssertion ([test](tests/test_x.py))\n~~~\n")


def missing_test_target_layout(root: Path) -> LinkLayout:
    spec = _write(root / "spec.md", "([test](tests/missing.py))\n")
    return LinkLayout(source=spec, target=root / "tests" / "missing.py")


def non_test_filename_layout(root: Path) -> LinkLayout:
    helper = _write(root / "tests" / "helper.py", "# helper\n")
    spec = _write(root / "spec.md", "([test](tests/helper.py))\n")
    return LinkLayout(source=spec, target=helper)


def non_python_test_target_layout(root: Path) -> LinkLayout:
    txt_file = _write(root / "tests" / "test_thing.txt", "not python\n")
    spec = _write(root / "spec.md", "([test](tests/test_thing.txt))\n")
    return LinkLayout(source=spec, target=txt_file)


def deep_test_layout(root: Path) -> LinkLayout:
    deep_node = root / "spx" / "a" / "b"
    deep_node.mkdir(parents=True)
    test_path = write_test_file(deep_node, "test_deep.conformance.l1.py")
    spec = _write(
        deep_node / "spec.md",
        "([test](tests/test_deep.conformance.l1.py))\n",
    )
    return LinkLayout(source=spec, target=test_path)


def loose_test_layout(root: Path) -> LinkLayout:
    node_dir = _node(root)
    loose_test = _write(
        node_dir / "test_loose.conformance.l1.py",
        "def test_placeholder() -> None: pass\n",
    )
    spec = _write(node_dir / "spec.md", "([test](test_loose.conformance.l1.py))\n")
    return LinkLayout(source=spec, target=loose_test)
