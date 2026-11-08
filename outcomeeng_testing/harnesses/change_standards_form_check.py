"""Workspace and observation harness for the change-standards form check.

Backs the ``[test]`` evidence of the change-standards Node. Each workspace is a
fresh Git repository in a temporary directory: the inert Base tree under
``fixtures/change_standards_form_check/repository`` is copied into it and
committed, so a Draft's ``base`` key names a commit that holds exactly that
tree. The harness loads the shipped form-check script by its path, builds the
request for a Draft fixture, runs the check, and exposes what it observed: the
result, the git commands the check issued, and the files of the workspace
before and after.

The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cache
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, Final

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SCRIPT: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "product-tree"
    / "skills"
    / "change-standards"
    / "scripts"
    / "form_check.py"
)
SPEC: Final = (
    REPO_ROOT
    / "spx"
    / "31-outcomeeng.enabler"
    / "32-changes.enabler"
    / "60-change-standards.enabler"
    / "change-standards.md"
)
FIXTURE_ROOT: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "change_standards_form_check"
)
REPOSITORY_DIR: Final = FIXTURE_ROOT / "repository"
NO_TREE_REPOSITORY_DIR: Final = FIXTURE_ROOT / "repository-no-tree"
TESTS_ALIAS: Final = "tests-directory"
TESTS_DIRECTORY: Final = "tests"
DRAFT_DIR: Final = FIXTURE_ROOT / "drafts"
BASE_PLACEHOLDER: Final = "{{BASE}}"
SIDECAR_SUFFIX: Final = ".request.json"
DRAFT_SUFFIX: Final = ".md"
VALID_DRAFT: Final = "valid"
GIT_IDENTITY: Final = (
    "-c",
    "user.name=harness",
    "-c",
    "user.email=harness@example.invalid",
)
MODULE_NAME: Final = "change_standards_form_check_under_test"


@cache
def load_form_check() -> ModuleType:
    """Return the shipped form-check module, loaded from its script path."""
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Workspace:
    """A temporary Git repository whose one commit holds the Base tree."""

    root: Path
    base: str


@dataclass(frozen=True)
class Observation:
    """What the check returned and did for one request."""

    result: Mapping[str, Any]
    commands: tuple[tuple[str, ...], ...]
    files_before: Mapping[str, tuple[int, int]]
    files_after: Mapping[str, tuple[int, int]]
    findings: tuple[Mapping[str, str], ...] = field(default=())

    @property
    def status(self) -> str:
        """The status the result holds."""
        return str(self.result[load_form_check().ResultField.STATUS])

    @property
    def rules(self) -> tuple[str, ...]:
        """The rule slug of each finding, in the order the result lists them."""
        key = load_form_check().FindingField.RULE
        return tuple(str(item[key]) for item in self.findings)

    @property
    def located(self) -> tuple[tuple[str, str], ...]:
        """The rule slug and the place each finding names."""
        form = load_form_check()
        return tuple(
            (str(item[form.FindingField.RULE]), str(item[form.FindingField.WHERE]))
            for item in self.findings
        )


@dataclass(frozen=True)
class CliObservation:
    """What the script printed and returned when run as a command."""

    exit_code: int
    stdout: str
    result: Mapping[str, Any]


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(  # noqa: S603
        ["git", *GIT_IDENTITY, *args],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


@contextmanager
def base_workspace(repository: Path = REPOSITORY_DIR) -> Iterator[Workspace]:
    """Yield a workspace whose commit holds the fixture Base tree of ``repository``.

    A fixture directory stored under the alias name stands as a tests directory
    in the workspace, because test-infrastructure files live outside any tests
    directory of this repository.
    """
    with TemporaryDirectory() as directory:
        root = Path(directory) / "checkout"
        shutil.copytree(repository, root, symlinks=True)
        for aliased in sorted(root.rglob(TESTS_ALIAS)):
            aliased.rename(aliased.with_name(TESTS_DIRECTORY))
        _git(root, "init", "--quiet")
        _git(root, "add", "--all")
        _git(root, "commit", "--quiet", "--message", "base")
        yield Workspace(root=root, base=_git(root, "rev-parse", "HEAD"))


def draft_text(workspace: Workspace, name: str) -> str:
    """Return the Draft fixture ``name`` with its base key naming the Base."""
    text = (DRAFT_DIR / f"{name}{DRAFT_SUFFIX}").read_text(encoding="utf-8")
    return text.replace(BASE_PLACEHOLDER, workspace.base)


def sidecar(name: str) -> dict[str, Any]:
    """Return the request fields a Draft fixture's sidecar file adds."""
    path = DRAFT_DIR / f"{name}{SIDECAR_SUFFIX}"
    if not path.exists():
        return {}
    fields: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return fields


def request_for(
    workspace: Workspace,
    text: str,
    **fields: Any,
) -> dict[str, Any]:
    """Return a complete request for the Draft ``text`` with ``fields`` applied."""
    module = load_form_check()
    request: dict[str, Any] = {
        module.RequestField.DRAFT_TEXT: text,
        module.RequestField.CHECKOUT_ROOT: str(workspace.root),
        module.RequestField.OPERATION: module.Operation.PUBLISH,
        module.RequestField.STORED_RECORD: None,
        module.RequestField.SIZE_LIMIT: module.GITHUB_STORE,
    }
    request.update(fields)
    return request


def snapshot(root: Path) -> dict[str, tuple[int, int]]:
    """Return every file under ``root`` with its size and modification time."""
    return {
        str(path.relative_to(root)): (path.lstat().st_size, path.lstat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if not path.is_dir()
    }


class RecordingRunner:
    """The check's command runner, recording every command it receives."""

    def __init__(self) -> None:
        self.commands: list[tuple[str, ...]] = []
        self._run = load_form_check().run_command

    def __call__(self, args: Sequence[str], cwd: str) -> Any:
        self.commands.append(tuple(args))
        return self._run(args, cwd)


def observe(workspace: Workspace, request: Mapping[str, Any]) -> Observation:
    """Run the check on ``request`` and expose what it did."""
    runner = RecordingRunner()
    before = snapshot(workspace.root)
    result = load_form_check().check(dict(request), runner)
    after = snapshot(workspace.root)
    return Observation(
        result=result,
        commands=tuple(runner.commands),
        files_before=before,
        files_after=after,
        findings=tuple(result.get(load_form_check().ResultField.FINDINGS, [])),
    )


def check_draft(workspace: Workspace, name: str, **fields: Any) -> Observation:
    """Run the check on the Draft fixture ``name`` with its sidecar fields."""
    text = draft_text(workspace, name)
    return observe(
        workspace, request_for(workspace, text, **{**sidecar(name), **fields})
    )


def check_text(workspace: Workspace, text: str, **fields: Any) -> Observation:
    """Run the check on Draft ``text`` with ``fields`` applied."""
    return observe(workspace, request_for(workspace, text, **fields))


@contextmanager
def draft_on_disk(workspace: Workspace, name: str) -> Iterator[Path]:
    """Yield the path of a file outside the checkout that holds Draft fixture ``name``."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / f"{name.rsplit('/', 1)[-1]}{DRAFT_SUFFIX}"
        path.write_text(draft_text(workspace, name), encoding="utf-8")
        yield path


def run_cli(request_text: str) -> CliObservation:
    """Run the script as a command with ``request_text`` on stdin."""
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-I", str(SCRIPT)],
        input=request_text,
        capture_output=True,
        check=False,
        text=True,
    )
    parsed = json.loads(completed.stdout) if completed.stdout.strip() else {}
    return CliObservation(
        exit_code=completed.returncode, stdout=completed.stdout, result=parsed
    )


def run_main(request_text: str) -> CliObservation:
    """Run the module's ``main`` on ``request_text`` in this process."""
    module = load_form_check()
    sink = StringIO()
    exit_code = module.main(StringIO(request_text), sink)
    text = sink.getvalue()
    parsed = json.loads(text) if text.strip() else {}
    return CliObservation(exit_code=exit_code, stdout=text, result=parsed)
