"""Resource and generated-domain harnesses for producer prompt evidence."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from hypothesis import seed, settings

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
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCER_FIXTURE_DIRECTORY = (
    Path(__file__).parent.parent / "fixtures" / "producer_prompt"
)
PRODUCER_FIXTURE_PATHS = tuple(
    reversed(sorted(PRODUCER_FIXTURE_DIRECTORY.glob("*.md")))
)
PRODUCER_RELATIVE_PATHS = tuple(
    (Path("producers") / fixture_path.name).as_posix()
    for fixture_path in PRODUCER_FIXTURE_PATHS
)
PRODUCER_PROMPT_PROPERTY_SEED = 20260717
PRODUCER_PROMPT_PROPERTY_EXAMPLES = 30
PRODUCER_PROMPT_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
    "test_producer_prompt.property.l1.py"
)


@dataclass(frozen=True)
class ProducerFilesWorkspace:
    """A real temporary repository carrying one plural-producer eval."""

    repo_root: Path
    eval_root: Path
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


@contextmanager
def with_producer_files_workspace() -> Iterator[ProducerFilesWorkspace]:
    """Yield a plural-producer eval backed by real temporary files."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
    ) as workspace:
        yield workspace


@contextmanager
def with_repository_producer_files_workspace() -> Iterator[ProducerFilesWorkspace]:
    """Yield a plural-producer eval addressable by repository Just recipes."""
    with _producer_files_workspace(
        producer_fixture_paths=PRODUCER_FIXTURE_PATHS,
        repository_root=REPO_ROOT,
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


def producer_prompt_property(property_run: Callable[[], None]) -> Callable[[], None]:
    """Apply the shared Hypothesis policy for producer-prompt properties."""
    configured = seed(PRODUCER_PROMPT_PROPERTY_SEED)(
        settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)(property_run)
    )

    def run_property() -> None:
        run_replayable_property(
            configured,
            seed_value=PRODUCER_PROMPT_PROPERTY_SEED,
            replay_path=PRODUCER_PROMPT_PROPERTY_REPLAY_PATH,
        )

    return run_property


def invoke_materialize_prompts_recipe(
    workspace: ProducerFilesWorkspace,
    *,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    """Run the repository prompt-materialization recipe for one workspace."""
    recipe = "eval-materialize-prompts-check" if check else "eval-materialize-prompts"
    return subprocess.run(
        ["just", recipe, str(workspace.eval_root)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


@contextmanager
def _producer_files_workspace(
    *,
    producer_fixture_paths: tuple[Path, ...],
    absolute_source_paths: bool = False,
    parent_traversal_source_paths: bool = False,
    include_section: bool = False,
    producer_files_placeholder_count: int = 1,
    repository_root: Path | None = None,
) -> Iterator[ProducerFilesWorkspace]:
    with TemporaryDirectory(dir=repository_root) as temp_dir:
        workspace_root = Path(temp_dir)
        repo_root = repository_root or workspace_root / "repo"
        eval_root = (
            workspace_root / "node"
            if repository_root is not None
            else repo_root / "spx" / "node"
        )
        eval_dir = eval_root / "evals" / "rule"
        eval_dir.mkdir(parents=True)
        producer_relative_paths = tuple(
            (
                (workspace_root / "producers" / fixture_path.name)
                .relative_to(repo_root)
                .as_posix()
                if repository_root is not None
                else (Path("producers") / fixture_path.name).as_posix()
            )
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
            eval_root=eval_root,
            eval_toml_path=eval_toml_path,
            prompt_path=eval_dir / MATERIALIZED_PROMPT_FILENAME,
            producer_relative_paths=producer_relative_paths,
            producer_texts=producer_texts,
        )
