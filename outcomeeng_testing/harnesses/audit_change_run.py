"""Workspace, invocation, and observation harness for the audit-change runner.

Backs the ``[test]`` evidence of ``spx/31-outcomeeng.enabler/32-changes.enabler``.
Each workspace is a fresh Git repository in a temporary directory beside a
separate, initially empty directory the runner receives as its temporary
directory. The harness places whole-payload Change records into the
repository, invokes the shipped runner's entry point as a subprocess with one
JSON request on stdin, and exposes what the invocation printed and which files
changed. It decides nothing: every predicate belongs to the linked test.

The runner treats scope and finding payloads as opaque objects keyed by their
``unitId``, and the SPX CLI accepts any audit payload that satisfies its audit
schema, so the harness builds payloads with the source-owned audit payload
constructors rather than restating a schema.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final, TypeVar

from outcomeeng.validation.audit_artifacts import implementation_languages
from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
    implementation_audit_finding_payload,
    implementation_audit_provenance,
    implementation_audit_scope_payload,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PLUGINS_DIR: Final = REPO_ROOT / "src" / "plugins"
SPEC_TREE_DIR: Final = PLUGINS_DIR / "spec-tree"
RUNNER_SCRIPT: Final = (
    SPEC_TREE_DIR / "skills" / "audit-change" / "scripts" / "audit_change_run.py"
)
SPEC_TREE_MANIFEST: Final = SPEC_TREE_DIR / ".claude-plugin" / "plugin.json"
CHANGE_RECORD_RULES: Final = (
    SPEC_TREE_DIR / "skills" / "change-standards" / "references" / "change-record.md"
)

#: The author-change record template, a source-owned Change record.
CHANGE_TEMPLATE: Final = (
    SPEC_TREE_DIR / "skills" / "author-change" / "templates" / "change.md"
)
#: An abridged capture of Change outcomeeng/changes#162, an Executable record.
CAPTURED_CHANGE_RECORD: Final = (
    REPO_ROOT
    / "outcomeeng_testing"
    / "fixtures"
    / "audit_change_run"
    / "change-record.md.txt"
)

#: Directory the SPX CLI keeps its run journals and verification contexts in.
SPX_STORE_DIRNAME: Final = ".spx"
_GIT_DIRNAME: Final = ".git"
_CANDIDATE_DIRNAME: Final = "changes"
_FIXTURE_SUFFIX: Final = ".txt"
_TEMPORARY_DIRECTORY_VARIABLES: Final = ("TMPDIR", "TMP", "TEMP")
_RULE_ID: Final = re.compile(r'<rule id="([a-z0-9-]+)"')
_CANDIDATE_EDIT: Final = "\n"

_T = TypeVar("_T")


def load_runner() -> ModuleType:
    """Load the shipped runner module by path, once per session."""
    cached = sys.modules.get("audit_change_run")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("audit_change_run", RUNNER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the audit-change runner from {RUNNER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_change_run"] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class RunnerCall:
    """What one runner invocation produced."""

    request: Mapping[str, object]
    exit_code: int
    stdout_lines: tuple[str, ...]
    result: Mapping[str, object]
    stderr: str


@dataclass(frozen=True)
class FileChanges:
    """Paths created, changed, or removed between two snapshots."""

    in_repository_outside_store: tuple[str, ...]
    in_runner_temporary_directory: tuple[str, ...]


def _snapshot(root: Path, *, excluded: frozenset[str]) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in excluded:
            continue
        if path.is_file():
            digests[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def _changed(before: Mapping[str, str], after: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for path in before.keys() | after.keys()
            if before.get(path) != after.get(path)
        )
    )


@dataclass
class AuditWorkspace:
    """A Git repository holding Change candidates, and the runner's temporary directory."""

    root: Path
    runner_temporary_directory: Path

    def place(self, source: Path) -> str:
        """Copy a whole-payload record into the repository; return its relative path."""
        name = source.name.removesuffix(_FIXTURE_SUFFIX)
        target = self.root / _CANDIDATE_DIRNAME / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        return target.relative_to(self.root).as_posix()

    def edit(self, relative: str) -> None:
        """Change a placed candidate's content, as another session editing it would."""
        with (self.root / relative).open("a", encoding="utf-8") as handle:
            handle.write(_CANDIDATE_EDIT)

    def content(self, relative: str) -> str:
        """Return a placed candidate's current content exactly as stored."""
        return (self.root / relative).read_bytes().decode("utf-8")

    def snapshot(self) -> tuple[dict[str, str], dict[str, str]]:
        """Record every file outside the Git and SPX stores, and the runner's temporary files."""
        return (
            _snapshot(self.root, excluded=frozenset({_GIT_DIRNAME, SPX_STORE_DIRNAME})),
            _snapshot(self.runner_temporary_directory, excluded=frozenset()),
        )

    def changes_since(
        self, snapshot: tuple[dict[str, str], dict[str, str]]
    ) -> FileChanges:
        """Return the files that differ from ``snapshot``."""
        repository, temporary = self.snapshot()
        return FileChanges(
            in_repository_outside_store=_changed(snapshot[0], repository),
            in_runner_temporary_directory=_changed(snapshot[1], temporary),
        )

    def invoke(self, request: Mapping[str, object]) -> RunnerCall:
        """Run the runner's entry point with ``request`` on stdin."""
        environment = dict(os.environ)
        for variable in _TEMPORARY_DIRECTORY_VARIABLES:
            environment[variable] = str(self.runner_temporary_directory)
        completed = subprocess.run(  # noqa: S603
            [sys.executable, str(RUNNER_SCRIPT)],
            cwd=self.root,
            env=environment,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            check=False,
        )
        lines = tuple(completed.stdout.splitlines())
        result = json.loads(lines[-1]) if lines else {}
        return RunnerCall(
            request=request,
            exit_code=completed.returncode,
            stdout_lines=lines,
            result=result,
            stderr=completed.stderr,
        )

    def invoke_racing_start(self, request: Mapping[str, object]) -> RunnerCall:
        """Run one request in process while another session edits the candidate.

        ``/test`` Stage 5 exception 3, time and concurrency: the edit lands after
        the runner reads the candidate and before SPX retains it, an interval no
        real session can be scheduled into. The collaborator delegates every
        command to the real subprocess runner and only times the edit.
        """
        runner = load_runner()
        relative = str(request[runner.RequestField.PATH])
        edited = False

        def racing(argv: Sequence[str], /, *, cwd: Path, stdin: str | None) -> object:
            nonlocal edited
            if argv[0] == runner.SPX_EXECUTABLE and not edited:
                self.edit(relative)
                edited = True
            return runner.run_subprocess(argv, cwd=cwd, stdin=stdin)

        exit_code, result = runner.execute(
            json.dumps(request), cwd=self.root, runner=racing
        )
        line = json.dumps(result, sort_keys=True)
        return RunnerCall(
            request=request,
            exit_code=int(exit_code),
            stdout_lines=(line,),
            result=json.loads(line),
            stderr="",
        )

    def render(self, render_command: str) -> dict[str, object]:
        """Execute a rendered-projection command from the repository root."""
        completed = subprocess.run(  # noqa: S603
            shlex.split(render_command),
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        projection = json.loads(completed.stdout.splitlines()[-1])
        if not isinstance(projection, dict):
            raise RuntimeError("the render command printed no projection object")
        return projection


@contextmanager
def audit_workspace() -> Iterator[AuditWorkspace]:
    """Yield a fresh repository and an empty runner temporary directory."""
    with TemporaryDirectory() as temporary:
        base = Path(temporary)
        root = base / "repository"
        runner_temporary_directory = base / "runner-temporary"
        root.mkdir()
        runner_temporary_directory.mkdir()
        subprocess.run(  # noqa: S603
            ["git", "init", "--quiet", str(root)],  # noqa: S607
            check=True,
        )
        yield AuditWorkspace(
            root=root, runner_temporary_directory=runner_temporary_directory
        )


def run_in_parallel(work: Callable[[_T], object], items: Sequence[_T]) -> list[object]:
    """Run ``work`` for every item at once and return the results in item order."""
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        return list(pool.map(work, items))


def change_record_rule_ids() -> tuple[str, ...]:
    """Return the common Change record rule identifiers the shipped standards declare."""
    return tuple(_RULE_ID.findall(CHANGE_RECORD_RULES.read_text(encoding="utf-8")))


def spec_tree_plugin_version() -> str:
    """Return the authored spec-tree plugin version."""
    manifest = json.loads(SPEC_TREE_MANIFEST.read_text(encoding="utf-8"))
    return str(manifest["version"])


@dataclass(frozen=True)
class AuditPayloads:
    """Scope and finding payloads for one candidate."""

    scopes: tuple[dict[str, object], ...]
    findings: tuple[dict[str, object], ...]


def audit_payloads(*, subject: str, content: str, tool_version: str) -> AuditPayloads:
    """Build one scope unit per audit concern and one finding per record rule.

    Every finding quotes the complete candidate as its observed state, so the
    rendered projection grows with the record rather than with the harness.
    """
    runner_field = load_runner().SpxField
    language = implementation_languages(PLUGINS_DIR)[0]
    version = spec_tree_plugin_version()
    provenance = implementation_audit_provenance(
        agent_plugin_version=version,
        language_plugin_version=version,
        tool_version=tool_version,
    )
    concerns = tuple(ImplementationAuditConcern)
    root, *children = (
        implementation_audit_scope_payload(
            language, concern, subject_path=subject, producer_provenance=provenance
        )
        for concern in concerns
    )
    # A file-scoped SPX run records exactly one root unit; every other unit
    # names that root as its parent.
    parent = {runner_field.PARENT_UNIT_ID: root[runner_field.UNIT_ID]}
    scopes = (root, *({**child, **parent} for child in children))
    findings = tuple(
        implementation_audit_finding_payload(
            language,
            concerns[index % len(concerns)],
            rule=rule,
            subject_path=subject,
            message=rule,
            observed=content,
            expected=rule,
            producer_provenance=provenance,
        )
        for index, rule in enumerate(change_record_rule_ids())
    )
    return AuditPayloads(scopes=scopes, findings=findings)
