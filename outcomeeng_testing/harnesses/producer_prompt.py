"""Resource and generated-domain harnesses for producer prompt evidence."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    MATERIALIZED_PROMPT_FILENAME,
    PRODUCERS_FIELD,
    PRODUCER_FILES_KIND,
    PRODUCER_FILES_PLACEHOLDER,
    PRODUCER_PATHS_PLACEHOLDER,
    PROMPT_FIELD,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
)

PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
PRODUCER_FIXTURE_DIRECTORY = (
    Path(__file__).parent.parent / "fixtures" / "producer_prompt"
)
PRODUCER_FIXTURE_PATHS = tuple(sorted(PRODUCER_FIXTURE_DIRECTORY.glob("*.md")))
PRODUCER_RELATIVE_PATHS = tuple(
    (Path("producers") / fixture_path.name).as_posix()
    for fixture_path in PRODUCER_FIXTURE_PATHS
)
PRODUCER_FILES_PROPERTY_SEED = 20260717
PRODUCER_FILES_PROPERTY_EXAMPLES = 30
PRODUCER_FILES_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
    "test_producer_prompt.property.l1.py::"
    "test_materialized_prompt_changes_with_each_producer_file"
)
PRODUCER_TEXT_SUFFIXES = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),
        blacklist_characters=["\x00"],
    ),
    min_size=1,
    max_size=64,
)


@dataclass(frozen=True)
class ProducerFilesWorkspace:
    """A real temporary repository carrying one plural-producer eval."""

    repo_root: Path
    eval_toml_path: Path
    prompt_path: Path
    producer_relative_paths: tuple[str, ...]
    producer_texts: tuple[str, ...]

    def read_prompt(self) -> str:
        """Read the materialized prompt from the temporary eval."""
        return self.prompt_path.read_text(encoding="utf-8")

    def append_to_producer(self, producer_index: int, suffix: str) -> None:
        """Append generated text to one selected producer file."""
        producer_path = self.repo_root / self.producer_relative_paths[producer_index]
        producer_path.write_text(
            producer_path.read_text(encoding="utf-8") + suffix,
            encoding="utf-8",
        )


@dataclass(frozen=True)
class ProducerFileMutation:
    """One generated mutation of a producer in an ordered source set."""

    producer_index: int
    suffix: str


@contextmanager
def with_producer_files_workspace() -> Iterator[ProducerFilesWorkspace]:
    """Yield a plural-producer eval backed by real temporary files."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
    ) as workspace:
        yield workspace


@contextmanager
def with_empty_producer_files_workspace() -> Iterator[ProducerFilesWorkspace]:
    """Yield a plural-producer eval whose declared source set is empty."""
    with _producer_files_workspace(
        producer_fixture_paths=(),
    ) as workspace:
        yield workspace


@contextmanager
def with_duplicate_producer_files_workspace() -> Iterator[ProducerFilesWorkspace]:
    """Yield a plural-producer eval whose source set repeats one path."""
    with _producer_files_workspace(
        producer_fixture_paths=(
            PRODUCER_FIXTURE_PATHS[0],
            PRODUCER_FIXTURE_PATHS[0],
        ),
    ) as workspace:
        yield workspace


@contextmanager
def with_absolute_producer_files_workspace() -> Iterator[ProducerFilesWorkspace]:
    """Yield a plural-producer eval whose source path is absolute."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
        absolute_source_paths=True,
    ) as workspace:
        yield workspace


@contextmanager
def with_parent_traversal_producer_files_workspace() -> Iterator[
    ProducerFilesWorkspace
]:
    """Yield a plural-producer eval whose source path escapes its repository."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
        parent_traversal_source_paths=True,
    ) as workspace:
        yield workspace


@contextmanager
def with_sectioned_producer_files_workspace() -> Iterator[ProducerFilesWorkspace]:
    """Yield a plural-producer eval with a forbidden section selector."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
        include_section=True,
    ) as workspace:
        yield workspace


@contextmanager
def with_missing_producer_files_placeholder_workspace() -> Iterator[
    ProducerFilesWorkspace
]:
    """Yield a plural-producer eval whose template omits producer bodies."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
        producer_files_placeholder_count=0,
    ) as workspace:
        yield workspace


@contextmanager
def with_duplicate_producer_files_placeholder_workspace() -> Iterator[
    ProducerFilesWorkspace
]:
    """Yield a plural-producer eval whose template repeats producer bodies."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
        producer_files_placeholder_count=2,
    ) as workspace:
        yield workspace


def run_producer_files_change_property(
    assertion: Callable[[ProducerFileMutation], None],
) -> None:
    """Run generated producer mutations through a test-owned predicate."""

    @seed(PRODUCER_FILES_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_FILES_PROPERTY_EXAMPLES)
    @given(
        producer_index=st.integers(
            min_value=0,
            max_value=len(PRODUCER_RELATIVE_PATHS) - 1,
        ),
        suffix=PRODUCER_TEXT_SUFFIXES,
    )
    def generated_assertion(producer_index: int, suffix: str) -> None:
        assertion(
            ProducerFileMutation(
                producer_index=producer_index,
                suffix=suffix,
            )
        )

    try:
        generated_assertion()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {PRODUCER_FILES_PROPERTY_SEED}")
        error.add_note(f"Replay path: {PRODUCER_FILES_PROPERTY_REPLAY_PATH}")
        raise


@contextmanager
def _producer_files_workspace(
    *,
    producer_fixture_paths: tuple[Path, ...],
    absolute_source_paths: bool = False,
    parent_traversal_source_paths: bool = False,
    include_section: bool = False,
    producer_files_placeholder_count: int = 1,
) -> Iterator[ProducerFilesWorkspace]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        eval_dir = repo_root / "spx" / "node" / "evals" / "rule"
        eval_dir.mkdir(parents=True)
        producer_relative_paths = tuple(
            (Path("producers") / fixture_path.name).as_posix()
            for fixture_path in producer_fixture_paths
        )
        producer_texts = tuple(
            fixture_path.read_text(encoding="utf-8")
            for fixture_path in producer_fixture_paths
        )
        if absolute_source_paths:
            producer_definition_paths = tuple(
                (repo_root / relative_path).as_posix()
                for relative_path in producer_relative_paths
            )
        elif parent_traversal_source_paths:
            producer_definition_paths = tuple(
                (Path("..") / Path(relative_path).name).as_posix()
                for relative_path in producer_relative_paths
            )
        else:
            producer_definition_paths = producer_relative_paths
        for relative_path, fixture_path in zip(
            producer_relative_paths,
            producer_fixture_paths,
            strict=True,
        ):
            producer_path = repo_root / relative_path
            producer_path.parent.mkdir(parents=True, exist_ok=True)
            copyfile(fixture_path, producer_path)

        template_path = eval_dir / PROMPT_TEMPLATE_FILENAME
        template_lines = [
            "Producers:",
            PRODUCER_PATHS_PLACEHOLDER,
            "",
            *([PRODUCER_FILES_PLACEHOLDER] * producer_files_placeholder_count),
            "",
        ]
        template_path.write_text("\n".join(template_lines), encoding="utf-8")
        eval_toml_path = eval_dir / EVAL_TOML_FILENAME
        section_definition = (
            [f'{SECTION_FIELD} = "{SECTION_FIELD}"'] if include_section else []
        )
        eval_toml_path.write_text(
            "\n".join(
                [
                    'title = "producer files prompt"',
                    'cases = "cases.jsonl"',
                    f'{PROMPT_FIELD} = "{MATERIALIZED_PROMPT_FILENAME}"',
                    "",
                    f"[{PROMPT_SOURCE_TABLE}]",
                    f'{KIND_FIELD} = "{PRODUCER_FILES_KIND}"',
                    f"{PRODUCERS_FIELD} = {json.dumps(producer_definition_paths)}",
                    f'{TEMPLATE_FIELD} = "{PROMPT_TEMPLATE_FILENAME}"',
                    *section_definition,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
        yield ProducerFilesWorkspace(
            repo_root=repo_root,
            eval_toml_path=eval_toml_path,
            prompt_path=eval_dir / MATERIALIZED_PROMPT_FILENAME,
            producer_relative_paths=producer_relative_paths,
            producer_texts=producer_texts,
        )
