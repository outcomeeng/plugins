"""Harness for the link-conversion script's evidence.

Exposes:

- ``load_link_conversion_module``. An importlib loader for ``convert_links.py``;
  the script ships as one standalone file and is not importable by package name.
- Path providers for the inert fixture set under
  ``outcomeeng_testing/fixtures/link_conversion/``: the input and expected trees
  and the files that record the expected rewritten list, the expected report, and
  the files the conversion must leave as written.
- ``copied_tree`` and ``converted_copy``. Copy a fixture tree into a temporary
  directory and run the script over the copy through its command-line boundary.
- ``tree_files``. The bytes of every file under a root, keyed by path.
- ``exercise_generated_trees``. Replayable generated trees, each converted twice.

The harness owns temporary resources, subprocess execution, and replay
configuration. Executed test files own every expectation and assertion.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.link_conversion import (
    GeneratedTree,
    link_conversion_trees,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
CONVERSION_SCRIPT_PATH: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "migrate-3-to-4"
    / "scripts"
    / "convert_links.py"
)
FIXTURE_ROOT: Final = REPO_ROOT / "outcomeeng_testing" / "fixtures" / "link_conversion"
INPUT_TREE: Final = FIXTURE_ROOT / "input"
EXPECTED_TREE: Final = FIXTURE_ROOT / "expected"
EXPECTED_REWRITTEN_FILE: Final = FIXTURE_ROOT / "expected-rewrote.txt"
EXPECTED_REPORT_FILE: Final = FIXTURE_ROOT / "expected-report.tsv"
UNTOUCHED_FILES_FILE: Final = FIXTURE_ROOT / "untouched-forms.txt"
OUTSIDE_SPEC_TREE_FIXTURE: Final = INPUT_TREE / "docs"
CONVERTIBLE_ONLY_TREE: Final = FIXTURE_ROOT / "convertible-only"
# A fixture tree models a product tree whose nodes carry a `tests/` directory, but the
# placement rule bans a `tests/` directory under the test-infrastructure home, so the
# stored tree names it `test-files` and each copy restores the name the script sees.
STORED_TESTS_DIRECTORY: Final = "test-files"
MATERIALIZED_TESTS_DIRECTORY: Final = "tests"

LINK_CONVERSION_PROPERTY_SEED: Final = 20261006
LINK_CONVERSION_PROPERTY_EXAMPLES: Final = 25
LINK_CONVERSION_PROPERTY_REPLAY: Final = (
    "just test spx/21-spec-tree.enabler/54-migrating.enabler/tests/"
    "test_migrating.property.l1.py"
)
CONVERSION_TIMEOUT_SECONDS: Final = 60


@dataclass(frozen=True)
class UnconvertibleCitation:
    file: str
    line: int
    form: str
    target: str


@dataclass(frozen=True)
class ConversionObservation:
    """What one run of the script returned."""

    exit_code: int
    stderr: str
    rewritten: tuple[str, ...]
    unconvertible: tuple[UnconvertibleCitation, ...]


@dataclass(frozen=True)
class ConvertedCopy:
    root: Path
    observation: ConversionObservation


@dataclass(frozen=True)
class ConversionPass:
    """One conversion run and the tree it left behind."""

    files: dict[str, bytes]
    observation: ConversionObservation


def _load_source_module(name: str, path: Path) -> ModuleType:
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        message = f"Cannot load {name} from {path}"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_link_conversion_module() -> ModuleType:
    """Load the conversion script through its shipped file boundary."""
    return _load_source_module("convert_links", CONVERSION_SCRIPT_PATH)


def _materialized_path(relative: Path) -> str:
    """Return a path from a tree root with each stored tests directory renamed."""
    return "/".join(
        MATERIALIZED_TESTS_DIRECTORY if part == STORED_TESTS_DIRECTORY else part
        for part in relative.parts
    )


def tree_files(root: Path) -> dict[str, bytes]:
    """Return the bytes of every file under a root, keyed by path from that root.

    A stored tests directory keys as the directory the script sees, so a stored
    fixture tree and a materialized copy of it compare equal.
    """
    return {
        _materialized_path(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def convert_product_root(root: Path, *paths: str) -> ConversionObservation:
    """Run the script over a product root and parse its result document.

    Each given path is passed to the script as an explicit PATH argument.
    """
    fields = load_link_conversion_module().ResultField
    completed = subprocess.run(  # noqa: S603 — argv is the script's own command contract.
        [sys.executable, str(CONVERSION_SCRIPT_PATH), str(root), *paths],
        capture_output=True,
        text=True,
        check=False,
        timeout=CONVERSION_TIMEOUT_SECONDS,
    )
    if not completed.stdout.strip():
        return ConversionObservation(completed.returncode, completed.stderr, (), ())
    document = json.loads(completed.stdout)
    return ConversionObservation(
        exit_code=completed.returncode,
        stderr=completed.stderr,
        rewritten=tuple(document[fields.REWRITTEN]),
        unconvertible=tuple(
            UnconvertibleCitation(
                file=item[fields.FILE],
                line=item[fields.LINE],
                form=item[fields.FORM],
                target=item[fields.TARGET],
            )
            for item in document[fields.UNCONVERTIBLE]
        ),
    )


@contextmanager
def copied_tree(source: Path) -> Iterator[Path]:
    """Yield a temporary copy of a tree, with its tests directories restored."""
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        shutil.copytree(source, root)
        for stored in sorted(
            root.rglob(STORED_TESTS_DIRECTORY),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            if stored.is_dir():
                stored.rename(stored.with_name(MATERIALIZED_TESTS_DIRECTORY))
        yield root


@contextmanager
def converted_copy(source: Path) -> Iterator[ConvertedCopy]:
    """Copy a tree, convert the copy, and yield the converted root and result."""
    with copied_tree(source) as root:
        yield ConvertedCopy(root, convert_product_root(root))


def exercise_generated_trees(
    assert_case: Callable[[ConversionPass, ConversionPass], None],
) -> None:
    """Supply each generated tree's first and second conversion to the assertion."""
    node_kinds = load_link_conversion_module().NODE_KINDS

    @seed(LINK_CONVERSION_PROPERTY_SEED)
    @settings(
        max_examples=LINK_CONVERSION_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(tree=link_conversion_trees(node_kinds))
    def run_cases(tree: GeneratedTree) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative_path, content in tree.files.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            first_observation = convert_product_root(root)
            first = ConversionPass(tree_files(root), first_observation)
            second_observation = convert_product_root(root)
            second = ConversionPass(tree_files(root), second_observation)
        assert_case(first, second)

    run_replayable_property(
        run_cases,
        seed_value=LINK_CONVERSION_PROPERTY_SEED,
        replay_path=LINK_CONVERSION_PROPERTY_REPLAY,
    )
