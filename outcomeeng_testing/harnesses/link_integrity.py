"""Workspace and observation infrastructure for evidence-link validation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng.validation.link_integrity import (
    BrokenEvalLink,
    BrokenTestLink,
    EvalLink,
    TestLink,
    find_eval_links,
    find_test_links,
    validate_eval_links,
    validate_test_links,
)


class LinkIntegrityCase(StrEnum):
    EVAL_RESOLVABLE = "eval-resolvable"
    EVAL_NON_LINK = "eval-non-link"
    EVAL_INLINE = "eval-inline"
    EVAL_FENCED = "eval-fenced"
    EVAL_ALL = "eval-all"
    EVAL_VALID = "eval-valid"
    EVAL_MISSING = "eval-missing"
    EVAL_NOT_FILE = "eval-not-file"
    EVAL_NON_TOML = "eval-non-toml"
    EVAL_DEEP = "eval-deep"
    EVAL_LOOSE = "eval-loose"
    TEST_RESOLVABLE = "test-resolvable"
    TEST_INLINE = "test-inline"
    TEST_FENCED = "test-fenced"
    TEST_VALID = "test-valid"
    TEST_MISSING = "test-missing"
    TEST_NOT_FILE = "test-not-file"
    TEST_NON_DEFAULT_NAME = "test-non-default-name"
    TEST_NON_PYTHON = "test-non-python"
    TEST_DEEP = "test-deep"
    TEST_LOOSE = "test-loose"


@dataclass(frozen=True)
class LinkIntegrityObservation:
    case: LinkIntegrityCase
    eval_links: tuple[EvalLink, ...] = ()
    test_links: tuple[TestLink, ...] = ()
    broken_eval_links: tuple[BrokenEvalLink, ...] = ()
    broken_test_links: tuple[BrokenTestLink, ...] = ()
    source_path: Path | None = None
    target_path: Path | None = None


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


def run_link_integrity_contract(
    predicate: Callable[[LinkIntegrityObservation], None],
) -> None:
    """Deliver every rule-derived link case to the linked test predicate."""
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for case in LinkIntegrityCase:
            predicate(_observe_link_case(root / case.value, case))


def _observe_link_case(root: Path, case: LinkIntegrityCase) -> LinkIntegrityObservation:
    if case is LinkIntegrityCase.EVAL_RESOLVABLE:
        node_dir = root / "spx" / "node"
        node_dir.mkdir(parents=True)
        target = write_eval_dir(node_dir, "rule-one")
        source = node_dir / "spec.md"
        source.write_text(
            "- NEVER: bad thing ([eval](evals/rule-one/eval.toml))\n",
            encoding="utf-8",
        )
        return LinkIntegrityObservation(
            case=case,
            eval_links=tuple(find_eval_links(root)),
            source_path=source,
            target_path=target,
        )
    if case is LinkIntegrityCase.EVAL_NON_LINK:
        root.mkdir(parents=True)
        (root / "spec.md").write_text(
            "- ALWAYS: do thing ([test](tests/test_thing.conformance.l1.py))\n"
            "- See [related doc](other.md)\n",
            encoding="utf-8",
        )
        return LinkIntegrityObservation(
            case=case, eval_links=tuple(find_eval_links(root))
        )
    if case is LinkIntegrityCase.EVAL_INLINE:
        root.mkdir(parents=True)
        (root / "spec.md").write_text(
            "Sample link form: `[eval](evals/{rule-slug}/eval.toml)`.\n",
            encoding="utf-8",
        )
        return LinkIntegrityObservation(
            case=case, eval_links=tuple(find_eval_links(root))
        )
    if case is LinkIntegrityCase.EVAL_FENCED:
        root.mkdir(parents=True)
        (root / "spec.md").write_text(
            "```markdown\n([eval](evals/example/eval.toml))\n```\n",
            encoding="utf-8",
        )
        return LinkIntegrityObservation(
            case=case, eval_links=tuple(find_eval_links(root))
        )
    if case is LinkIntegrityCase.EVAL_ALL:
        node_a = root / "spx" / "a"
        node_b = root / "spx" / "b"
        node_a.mkdir(parents=True)
        node_b.mkdir(parents=True)
        write_eval_dir(node_a, "rule-a")
        write_eval_dir(node_b, "rule-b")
        (node_a / "spec.md").write_text(
            "([eval](evals/rule-a/eval.toml))\n", encoding="utf-8"
        )
        (node_b / "spec.md").write_text(
            "([eval](evals/rule-b/eval.toml))\n", encoding="utf-8"
        )
        return LinkIntegrityObservation(
            case=case, eval_links=tuple(find_eval_links(root))
        )
    if case in {LinkIntegrityCase.EVAL_VALID, LinkIntegrityCase.EVAL_DEEP}:
        node_dir = root / "spx" / "node"
        if case is LinkIntegrityCase.EVAL_DEEP:
            node_dir = root / "spx" / "a" / "b" / "c"
        node_dir.mkdir(parents=True)
        write_eval_dir(node_dir, "rule-one")
        (node_dir / "spec.md").write_text(
            "([eval](evals/rule-one/eval.toml))\n", encoding="utf-8"
        )
        return LinkIntegrityObservation(
            case=case,
            broken_eval_links=tuple(validate_eval_links(root)),
        )
    if case is LinkIntegrityCase.EVAL_MISSING:
        root.mkdir(parents=True)
        source = root / "spec.md"
        source.write_text("([eval](evals/missing-rule/eval.toml))\n", encoding="utf-8")
        return LinkIntegrityObservation(
            case=case,
            broken_eval_links=tuple(validate_eval_links(root)),
            source_path=source,
            target_path=root / "evals" / "missing-rule" / EVAL_TOML_FILENAME,
        )
    if case is LinkIntegrityCase.EVAL_NOT_FILE:
        root.mkdir(parents=True)
        target = root / "evals" / "rule" / EVAL_TOML_FILENAME
        target.mkdir(parents=True)
        (root / "spec.md").write_text(
            f"([eval](evals/rule/{EVAL_TOML_FILENAME}))\n", encoding="utf-8"
        )
        return LinkIntegrityObservation(
            case=case,
            broken_eval_links=tuple(validate_eval_links(root)),
            target_path=target,
        )
    if case is LinkIntegrityCase.EVAL_NON_TOML:
        root.mkdir(parents=True)
        target = root / "evals" / "rule" / "cases.jsonl"
        target.parent.mkdir(parents=True)
        target.write_text("", encoding="utf-8")
        (root / "spec.md").write_text(
            "([eval](evals/rule/cases.jsonl))\n", encoding="utf-8"
        )
        return LinkIntegrityObservation(
            case=case,
            broken_eval_links=tuple(validate_eval_links(root)),
            target_path=target,
        )
    if case is LinkIntegrityCase.EVAL_LOOSE:
        root.mkdir(parents=True)
        target = root / "evals" / EVAL_TOML_FILENAME
        target.parent.mkdir()
        target.write_text(
            'title = "x"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
            encoding="utf-8",
        )
        (root / "spec.md").write_text("([eval](evals/eval.toml))\n", encoding="utf-8")
        return LinkIntegrityObservation(
            case=case,
            broken_eval_links=tuple(validate_eval_links(root)),
            target_path=target,
        )
    if case is LinkIntegrityCase.TEST_RESOLVABLE:
        root.mkdir(parents=True)
        target = write_test_file(root, "test_thing.conformance.l1.py")
        source = root / "spec.md"
        source.write_text(
            "Assertion ([test](tests/test_thing.conformance.l1.py))\n",
            encoding="utf-8",
        )
        return LinkIntegrityObservation(
            case=case,
            test_links=tuple(find_test_links(root)),
            source_path=source,
            target_path=target,
        )
    if case in {LinkIntegrityCase.TEST_INLINE, LinkIntegrityCase.TEST_FENCED}:
        root.mkdir(parents=True)
        (root / "doc.md").write_text(
            {
                LinkIntegrityCase.TEST_INLINE: (
                    "The link form `[test](path/to/test.py)` is required.\n"
                ),
                LinkIntegrityCase.TEST_FENCED: (
                    "```\nAssertion ([test](tests/test_x.py))\n```\n"
                ),
            }[case],
            encoding="utf-8",
        )
        return LinkIntegrityObservation(
            case=case, test_links=tuple(find_test_links(root))
        )
    if case in {LinkIntegrityCase.TEST_VALID, LinkIntegrityCase.TEST_DEEP}:
        node_dir = root
        if case is LinkIntegrityCase.TEST_DEEP:
            node_dir = root / "spx" / "a" / "b"
        node_dir.mkdir(parents=True)
        write_test_file(node_dir, "test_x.conformance.l1.py")
        (node_dir / "spec.md").write_text(
            "([test](tests/test_x.conformance.l1.py))\n", encoding="utf-8"
        )
        return LinkIntegrityObservation(
            case=case,
            broken_test_links=tuple(validate_test_links(root)),
        )
    if case is LinkIntegrityCase.TEST_MISSING:
        root.mkdir(parents=True)
        target = root / "tests" / "missing.py"
        (root / "spec.md").write_text("([test](tests/missing.py))\n", encoding="utf-8")
        return LinkIntegrityObservation(
            case=case,
            broken_test_links=tuple(validate_test_links(root)),
            target_path=target,
        )
    if case is LinkIntegrityCase.TEST_NOT_FILE:
        root.mkdir(parents=True)
        target = root / "tests" / "test_dir.conformance.l1.py"
        target.mkdir(parents=True)
        (root / "spec.md").write_text(
            f"([test](tests/{target.name}))\n", encoding="utf-8"
        )
        return LinkIntegrityObservation(
            case=case,
            broken_test_links=tuple(validate_test_links(root)),
            target_path=target,
        )
    if case in {
        LinkIntegrityCase.TEST_NON_DEFAULT_NAME,
        LinkIntegrityCase.TEST_NON_PYTHON,
    }:
        root.mkdir(parents=True)
        target = (
            root
            / "tests"
            / (
                "helper.py"
                if case is LinkIntegrityCase.TEST_NON_DEFAULT_NAME
                else "test_thing.txt"
            )
        )
        target.parent.mkdir(parents=True)
        target.write_text("", encoding="utf-8")
        (root / "spec.md").write_text(
            f"([test](tests/{target.name}))\n", encoding="utf-8"
        )
        return LinkIntegrityObservation(
            case=case,
            broken_test_links=tuple(validate_test_links(root)),
            target_path=target,
        )
    root.mkdir(parents=True)
    target = root / "test_loose.conformance.l1.py"
    target.write_text("def test_placeholder() -> None: pass\n", encoding="utf-8")
    (root / "spec.md").write_text(
        "([test](test_loose.conformance.l1.py))\n", encoding="utf-8"
    )
    return LinkIntegrityObservation(
        case=case,
        broken_test_links=tuple(validate_test_links(root)),
        target_path=target,
    )
