"""Workspace, invocation, and observation harness for the audit-change runner.

Backs the ``[test]`` evidence that an audit-change run writes no file.
Each workspace is a fresh Git repository in a temporary directory beside three
initially empty directories: one the runner receives as its temporary
directory, one it receives as its home directory, and one outside both that
holds link targets. The harness places whole-payload Change records into the
repository and starts the shipped runner as a subprocess, with one request on
stdin, under the process observer in ``audit_change_run_observer``. Every
invocation therefore exposes what the runner printed, every file the runner
process wrote wherever the path lies, and every process it started. Directory
snapshots add what changed in the repository, the SPX store, and the runner's
temporary and home directories, which covers the processes the runner starts.

Generated requests enter the runner's entry point in this process instead,
under one observer ``Recorder`` installed here for that purpose, from one
empty working directory that stays in place for the whole property run. No
per-case repository, file, or process is involved: the generated domain is the
request, and the subprocess invocations above exercise the real stdin, stdout,
and process boundary. The harness owns each property's seed, example count,
and replay command.

The harness decides nothing: every predicate belongs to the linked test.

The runner treats scope and finding payloads as opaque objects keyed by their
``unitId``, and the SPX CLI accepts any audit payload that satisfies its audit
schema, so the harness builds payloads with the source-owned audit payload
constructors rather than restating a schema.
"""

from __future__ import annotations

import functools
import hashlib
import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import chdir, contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp
from types import ModuleType
from typing import Final, TypeVar

from hypothesis import given, seed, settings

from outcomeeng.validation.audit_artifacts import implementation_languages
from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
    implementation_audit_finding_payload,
    implementation_audit_provenance,
    implementation_audit_scope_payload,
)
from outcomeeng_testing.generators.audit_change_run import (
    malformed_request_objects,
    unparseable_request_texts,
)
from outcomeeng_testing.harnesses import audit_change_run_observer as observer
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PLUGINS_DIR: Final = REPO_ROOT / "src" / "plugins"
SPEC_TREE_DIR: Final = PLUGINS_DIR / "spec-tree"
RUNNER_SCRIPT: Final = (
    SPEC_TREE_DIR / "skills" / "audit-change" / "scripts" / "audit_change_run.py"
)
OBSERVER_SCRIPT: Final = Path(observer.__file__).resolve()
SPEC_TREE_MANIFEST: Final = SPEC_TREE_DIR / ".claude-plugin" / "plugin.json"
CHANGE_RECORD_RULES: Final = (
    SPEC_TREE_DIR / "skills" / "change-standards" / "references" / "change-record.md"
)

#: The author-change record template, a source-owned Change record.
CHANGE_TEMPLATE: Final = (
    SPEC_TREE_DIR / "skills" / "author-change" / "templates" / "change.md"
)
_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "audit_change_run"
)
#: An abridged capture of Change outcomeeng/changes#162, an Executable record.
CAPTURED_CHANGE_RECORD: Final = _FIXTURES_DIR / "change-record.md.txt"

# An editor applying typographic apostrophes and saving in Windows-1252 writes
# U+2019 as a byte no UTF-8 sequence starts with, so the saved record is not
# UTF-8 text. The re-encoded record exists only inside a disposable workspace.
_WINDOWS_1252_CODEC: Final = "cp1252"
_WINDOWS_1252_PREFIX: Final = "windows-1252-"
_TYPEWRITER_APOSTROPHE: Final = "'"
_TYPOGRAPHIC_APOSTROPHE: Final = "\N{RIGHT SINGLE QUOTATION MARK}"

# Windows PowerShell's Out-File saves text as UTF-16 with a byte-order mark,
# whose first byte no UTF-8 sequence starts with.
_UTF16_CODEC: Final = "utf-16"
#: Text appended to a candidate, as another session editing it would.
CANDIDATE_EDIT: Final = "\n"
# A mode that grants no permission, so the process cannot open the file.
_NO_PERMISSIONS: Final = 0

#: Property run configuration for generated requests.
MALFORMED_REQUEST_PROPERTY_SEED: Final = 20260929
MALFORMED_REQUEST_PROPERTY_EXAMPLES: Final = settings().max_examples
MALFORMED_REQUEST_PROPERTY_REPLAY: Final = (
    "just test spx/31-outcomeeng.enabler/32-changes.enabler/tests/"
    "test_audit_change_run.compliance.l1.py"
)

#: Directory the SPX CLI keeps its run journals and verification contexts in.
SPX_STORE_DIRNAME: Final = ".spx"
_GIT_DIRNAME: Final = ".git"
_CANDIDATE_DIRNAME: Final = "changes"
_FIXTURE_SUFFIX: Final = ".txt"
_TEMPORARY_DIRECTORY_VARIABLES: Final = ("TMPDIR", "TMP", "TEMP")
_HOME_VARIABLE: Final = "HOME"
_REPORT_SUFFIX: Final = ".json"

_T = TypeVar("_T")
_R = TypeVar("_R")


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
    """What one runner invocation produced, and what its process did."""

    request_text: str
    exit_code: int
    stdout_lines: tuple[str, ...]
    result: Mapping[str, object]
    stderr: str
    #: Every filesystem mutation the runner process performed, as
    #: ``(event, path)``, wherever the path lies.
    runner_writes: tuple[tuple[str, ...], ...]
    #: The argument vector of every process the runner process started.
    spawned_commands: tuple[tuple[str, ...], ...]

    @property
    def request(self) -> Mapping[str, object]:
        """The request object sent on stdin."""
        value = json.loads(self.request_text)
        if not isinstance(value, dict):
            raise TypeError("the request sent on stdin is not a JSON object")
        return value

    @property
    def json_object_arguments(self) -> tuple[object, ...]:
        """Every argument of a started process that decodes as a JSON object."""
        decoded: list[object] = []
        for command in self.spawned_commands:
            for argument in command:
                try:
                    value = json.loads(argument)
                except ValueError:
                    continue
                if isinstance(value, dict):
                    decoded.append(value)
        return tuple(decoded)


@dataclass(frozen=True)
class StartedRun:
    """The ``read-candidate`` and ``start`` calls that opened one audit run."""

    read: RunnerCall
    started: RunnerCall

    @property
    def run_token(self) -> object:
        """The run token the ``start`` result carries."""
        return self.started.result.get(load_runner().ResultField.RUN_TOKEN)


def json_strings(value: object) -> tuple[str, ...]:
    """Return every string a decoded JSON value holds, keys and values alike."""
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(
            text
            for key, item in value.items()
            for text in (*json_strings(key), *json_strings(item))
        )
    if isinstance(value, list | tuple):
        return tuple(text for item in value for text in json_strings(item))
    return ()


@dataclass(frozen=True)
class FileChanges:
    """Paths created, changed, or removed between two snapshots."""

    in_repository_outside_store: tuple[str, ...]
    in_spx_store: tuple[str, ...]
    in_runner_temporary_directory: tuple[str, ...]
    in_runner_home_directory: tuple[str, ...]


@dataclass(frozen=True)
class Snapshot:
    """Content digests of every file in each observed directory."""

    repository_outside_store: Mapping[str, str]
    spx_store: Mapping[str, str]
    runner_temporary_directory: Mapping[str, str]
    runner_home_directory: Mapping[str, str]


def _fingerprint(path: Path) -> str:
    """Digest a file's content, or its mode, size, and modification time when unreadable."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except PermissionError:
        status = path.stat()
        return f"{status.st_mode:o}:{status.st_size}:{status.st_mtime_ns}"


def _digests(root: Path, *, excluded: frozenset[str] = frozenset()) -> dict[str, str]:
    digests: dict[str, str] = {}
    if not root.exists():
        return digests
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in excluded:
            continue
        if path.is_file():
            digests[relative.as_posix()] = _fingerprint(path)
    return digests


def _changed(before: Mapping[str, str], after: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for path in before.keys() | after.keys()
            if before.get(path) != after.get(path)
        )
    )


class CandidateCondition(StrEnum):
    """A candidate path the runner contract names as refused or missing."""

    ABSENT = "absent"
    DIRECTORY = "directory"
    UNREADABLE = "unreadable"
    LINKED_OUTSIDE = "linked-outside"
    WINDOWS_1252 = "windows-1252"


@dataclass
class AuditWorkspace:
    """A Git repository holding Change candidates, and the runner's own directories."""

    root: Path
    runner_temporary_directory: Path
    runner_home_directory: Path
    outside_directory: Path
    observation_directory: Path

    def path_for(self, source: Path) -> str:
        """Return the relative path ``place`` gives ``source``, without placing it."""
        name = source.name.removesuffix(_FIXTURE_SUFFIX)
        return (Path(_CANDIDATE_DIRNAME) / name).as_posix()

    def place(self, source: Path) -> str:
        """Copy a whole-payload record into the repository; return its relative path."""
        relative = self.path_for(source)
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        return relative

    def place_windows_1252(self, source: Path) -> str:
        """Place ``source`` as an editor saving it in Windows-1252 would.

        The UTF-8 record's apostrophes become typographic apostrophes and the
        text is encoded in Windows-1252, so the placed candidate is the same
        record in bytes that are not UTF-8 text. Return its relative path.
        """
        text = source.read_text(encoding="utf-8")
        if _TYPEWRITER_APOSTROPHE not in text:
            raise RuntimeError(
                f"{source} carries no apostrophe to re-encode as Windows-1252"
            )
        name = source.name.removesuffix(_FIXTURE_SUFFIX)
        relative = (
            Path(_CANDIDATE_DIRNAME) / f"{_WINDOWS_1252_PREFIX}{name}"
        ).as_posix()
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(
            text.replace(_TYPEWRITER_APOSTROPHE, _TYPOGRAPHIC_APOSTROPHE).encode(
                _WINDOWS_1252_CODEC
            )
        )
        return relative

    def place_link_outside(self, source: Path) -> str:
        """Copy a record outside the repository and link a candidate path to it."""
        relative = self.path_for(source)
        outside = self.outside_directory / Path(relative).name
        shutil.copyfile(source, outside)
        link = self.root / relative
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(outside)
        return relative

    def place_unreadable(self, source: Path) -> str:
        """Copy a record into the repository with no permission to read it."""
        relative = self.place(source)
        target = self.root / relative
        target.chmod(_NO_PERMISSIONS)
        if os.access(target, os.R_OK):
            raise RuntimeError(
                f"this user can read {target} with no permissions; "
                "an unreadable candidate cannot be placed"
            )
        return relative

    def place_directory(self, source: Path) -> str:
        """Create a directory where ``place`` would put ``source``."""
        relative = self.path_for(source)
        (self.root / relative).mkdir(parents=True)
        return relative

    def place_in_condition(self, condition: CandidateCondition, source: Path) -> str:
        """Put ``source`` at a candidate path in ``condition``; return the path."""
        placements: Mapping[CandidateCondition, Callable[[Path], str]] = {
            CandidateCondition.ABSENT: self.path_for,
            CandidateCondition.DIRECTORY: self.place_directory,
            CandidateCondition.UNREADABLE: self.place_unreadable,
            CandidateCondition.LINKED_OUTSIDE: self.place_link_outside,
            CandidateCondition.WINDOWS_1252: self.place_windows_1252,
        }
        return placements[condition](source)

    def edit(self, relative: str) -> None:
        """Change a placed candidate's content, as another session editing it would."""
        encoding = load_runner().TEXT_ENCODING
        with (self.root / relative).open("a", encoding=encoding) as handle:
            handle.write(CANDIDATE_EDIT)

    def content(self, relative: str) -> str:
        """Return a placed candidate's current content exactly as stored."""
        return (self.root / relative).read_bytes().decode(load_runner().TEXT_ENCODING)

    def start_run(self, relative: str) -> StartedRun:
        """Read a placed candidate and start a run over the content that read returned.

        Both calls are returned as observed; a read that returns no digest
        starts nothing the runner accepts, and the start call shows that.
        """
        runner = load_runner()
        field = runner.RequestField
        operation = runner.Operation
        read = self.invoke(
            {field.OPERATION: operation.READ_CANDIDATE, field.PATH: relative}
        )
        started = self.invoke(
            {
                field.OPERATION: operation.START,
                field.PATH: relative,
                field.CANDIDATE_SHA256: read.result.get(runner.ResultField.SHA256),
            }
        )
        return StartedRun(read=read, started=started)

    def snapshot(self) -> Snapshot:
        """Record every file in each directory the runner could write to."""
        return Snapshot(
            repository_outside_store=_digests(
                self.root, excluded=frozenset({_GIT_DIRNAME, SPX_STORE_DIRNAME})
            ),
            spx_store=_digests(self.root / SPX_STORE_DIRNAME),
            runner_temporary_directory=_digests(self.runner_temporary_directory),
            runner_home_directory=_digests(self.runner_home_directory),
        )

    def changes_since(self, before: Snapshot) -> FileChanges:
        """Return the files that differ from ``before``."""
        after = self.snapshot()
        return FileChanges(
            in_repository_outside_store=_changed(
                before.repository_outside_store, after.repository_outside_store
            ),
            in_spx_store=_changed(before.spx_store, after.spx_store),
            in_runner_temporary_directory=_changed(
                before.runner_temporary_directory, after.runner_temporary_directory
            ),
            in_runner_home_directory=_changed(
                before.runner_home_directory, after.runner_home_directory
            ),
        )

    def invoke(self, request: Mapping[str, object]) -> RunnerCall:
        """Run the runner's entry point with ``request`` on stdin."""
        return self.invoke_text(json.dumps(request))

    def invoke_text(self, request_text: str) -> RunnerCall:
        """Run the runner's entry point with ``request_text`` on stdin, unparsed."""
        return self._observe(
            request_text, request_text.encode(load_runner().TEXT_ENCODING)
        )

    def invoke_utf16(self, request: Mapping[str, object]) -> RunnerCall:
        """Run the runner with ``request`` saved as Windows PowerShell's Out-File saves it."""
        request_text = json.dumps(request)
        return self._observe(request_text, request_text.encode(_UTF16_CODEC))

    def _environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        for variable in _TEMPORARY_DIRECTORY_VARIABLES:
            environment[variable] = str(self.runner_temporary_directory)
        environment[_HOME_VARIABLE] = str(self.runner_home_directory)
        return environment

    def _observe(self, request_text: str, request_bytes: bytes) -> RunnerCall:
        handle, report = mkstemp(dir=self.observation_directory, suffix=_REPORT_SUFFIX)
        os.close(handle)
        completed = subprocess.run(  # noqa: S603
            [sys.executable, str(OBSERVER_SCRIPT), str(RUNNER_SCRIPT), report],
            cwd=self.root,
            env=self._environment(),
            input=request_bytes,
            capture_output=True,
            check=False,
        )
        observation = json.loads(Path(report).read_text(encoding="utf-8"))
        encoding = load_runner().TEXT_ENCODING
        lines = tuple(completed.stdout.decode(encoding).splitlines())
        return RunnerCall(
            request_text=request_text,
            exit_code=completed.returncode,
            stdout_lines=lines,
            result=json.loads(lines[-1]) if lines else {},
            stderr=completed.stderr.decode(encoding, "backslashreplace"),
            runner_writes=tuple(tuple(write) for write in observation[observer.WRITES]),
            spawned_commands=tuple(
                tuple(command) for command in observation[observer.SPAWNS]
            ),
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
    """Yield a fresh repository and the runner's empty temporary and home directories."""
    with TemporaryDirectory() as temporary:
        base = Path(temporary)
        workspace = AuditWorkspace(
            root=base / "repository",
            runner_temporary_directory=base / "runner-temporary",
            runner_home_directory=base / "runner-home",
            outside_directory=base / "outside",
            observation_directory=base / "observations",
        )
        for directory in (
            workspace.root,
            workspace.runner_temporary_directory,
            workspace.runner_home_directory,
            workspace.outside_directory,
            workspace.observation_directory,
        ):
            directory.mkdir()
        subprocess.run(  # noqa: S603
            ["git", "init", "--quiet", str(workspace.root)],  # noqa: S607
            check=True,
        )
        yield workspace


def run_in_parallel(work: Callable[[_T], _R], items: Sequence[_T]) -> list[_R]:
    """Run ``work`` for every item at once and return the results in item order."""
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        return list(pool.map(work, items))


def change_record_rule_ids() -> tuple[str, ...]:
    """Return the common Change record rule identifiers the shipped standards declare."""
    rule_id = re.compile(f'<rule id="({load_runner().RULE_ID_PATTERN.pattern})"')
    return tuple(rule_id.findall(CHANGE_RECORD_RULES.read_text(encoding="utf-8")))


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


@dataclass(frozen=True)
class EntryPointCall:
    """What one call of the runner's entry point in this process produced."""

    exit_code: int
    stdout: str
    #: Every filesystem mutation the call performed, as ``(event, path)``.
    runner_writes: tuple[tuple[str, ...], ...]
    #: The argument vector of every process the call started.
    spawned_commands: tuple[tuple[str, ...], ...]

    @property
    def stdout_lines(self) -> tuple[str, ...]:
        """The lines the call printed on stdout."""
        return tuple(self.stdout.splitlines())


@functools.cache
def _entry_point_recorder() -> observer.Recorder:
    """Install one audit hook in this process for entry-point observation."""
    recorder = observer.Recorder()
    sys.addaudithook(recorder)
    return recorder


def _call_entry_point(runner: ModuleType, request_text: str) -> EntryPointCall:
    recorder = _entry_point_recorder()
    sink = io.StringIO()
    recorder.start(thread=threading.get_ident())
    try:
        exit_code = int(runner.main(stdin=io.StringIO(request_text), stdout=sink))
    finally:
        writes, spawns = recorder.stop()
    return EntryPointCall(
        exit_code=exit_code,
        stdout=sink.getvalue(),
        runner_writes=tuple(tuple(write) for write in writes),
        spawned_commands=tuple(tuple(command) for command in spawns),
    )


@contextmanager
def _entry_point_directory() -> Iterator[None]:
    """Hold an empty working directory, outside every repository, for a property run."""
    with TemporaryDirectory() as temporary, chdir(temporary):
        yield


def exercise_malformed_request_objects(
    assert_case: Callable[[Mapping[str, object], EntryPointCall], None],
) -> None:
    """Send every generated refused request object to the entry point.

    ``assert_case`` receives the request and what the entry point did with
    its JSON text.
    """
    runner = load_runner()

    @seed(MALFORMED_REQUEST_PROPERTY_SEED)
    @settings(max_examples=MALFORMED_REQUEST_PROPERTY_EXAMPLES, print_blob=True)
    @given(request=malformed_request_objects(runner))
    def run_cases(request: dict[str, object]) -> None:
        assert_case(request, _call_entry_point(runner, json.dumps(request)))

    with _entry_point_directory():
        run_replayable_property(
            run_cases,
            seed_value=MALFORMED_REQUEST_PROPERTY_SEED,
            replay_path=MALFORMED_REQUEST_PROPERTY_REPLAY,
        )


def exercise_unparseable_request_texts(
    assert_case: Callable[[EntryPointCall], None],
) -> None:
    """Send every generated request text the runner cannot parse as one JSON object.

    ``assert_case`` receives what the entry point did with the text; a failing
    case reports the generated text itself.
    """
    runner = load_runner()

    @seed(MALFORMED_REQUEST_PROPERTY_SEED)
    @settings(max_examples=MALFORMED_REQUEST_PROPERTY_EXAMPLES, print_blob=True)
    @given(request_text=unparseable_request_texts(runner))
    def run_cases(request_text: str) -> None:
        assert_case(_call_entry_point(runner, request_text))

    with _entry_point_directory():
        run_replayable_property(
            run_cases,
            seed_value=MALFORMED_REQUEST_PROPERTY_SEED,
            replay_path=MALFORMED_REQUEST_PROPERTY_REPLAY,
        )
