"""Workspace, invocation, and observation harness for the audit-change runner.

Backs the ``[test]`` evidence that an audit-change run writes no file and reads
the Change Store only through ``gh``. Each workspace is a fresh Git repository in
a temporary directory beside four initially empty directories: one the runner
receives as its temporary directory, one as its home directory, one outside
both, and one holding an executable ``gh`` that replays recorded store answers
from a store file beside the repository. The harness places whole-payload store
issues into the store file and starts the shipped runner as a subprocess, with
one request on stdin, under the process observer in
``audit_change_run_observer``. Every invocation therefore exposes what the
runner printed, every file the runner process wrote wherever the path lies, and
every process it started. Directory snapshots add what changed in the
repository, the SPX store, and the runner's temporary and home directories,
which covers the processes the runner starts.

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
import shlex
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import chdir, contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp
from types import ModuleType
from typing import Final, TypeVar

from hypothesis import given, seed, settings

from outcomeeng.distribution.installation import (
    HOME_ENV,
    PLUGIN_MANIFEST_VERSION_FIELD,
)
from outcomeeng.hygiene.clean import GIT_METADATA_DIR, SPX_STORE_DIR
from outcomeeng.validation.audit_artifacts import implementation_languages
from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
    implementation_audit_finding_payload,
    implementation_audit_provenance,
    implementation_audit_scope_payload,
)
from outcomeeng_testing.generators.audit_change_run import (
    malformed_request_objects,
    rule_identifiers,
    unparseable_request_texts,
)
from outcomeeng_testing.harnesses import audit_change_run_observer as observer
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PLUGINS_DIR: Final = REPO_ROOT / "src" / "plugins"
PRODUCT_TREE_DIR: Final = PLUGINS_DIR / "product-tree"
RUNNER_SCRIPT: Final = (
    PRODUCT_TREE_DIR / "skills" / "audit-change" / "scripts" / "audit_change_run.py"
)
OBSERVER_SCRIPT: Final = Path(observer.__file__).resolve()
PRODUCT_TREE_MANIFEST: Final = PRODUCT_TREE_DIR / ".claude-plugin" / "plugin.json"
#: How many finding rule identifiers one generated audit records.
RULE_IDENTIFIER_COUNT: Final = 10

_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "audit_change_run"
)
#: A capture of a Sliced Leaf as the Change Store answers for it, the whole
#: payload of the ``issue`` object of one GraphQL answer.
STORE_ISSUE: Final = _FIXTURES_DIR / "store-issue.json"
#: The executable that stands in for ``gh``, saved with a ``.txt`` suffix.
GH_REPLAY: Final = _FIXTURES_DIR / "gh-replay.py.txt"
_GH_REPLAY_NAME: Final = "gh"
#: The executable that stands in for the Product's format command.
FORMATTER: Final = _FIXTURES_DIR / "format-strip.py.txt"
_FORMATTER_NAME: Final = "format-strip"
_EXECUTABLE_MODE: Final = 0o755
_COMMITTER: Final = "Audit Change Harness"
_COMMITTER_EMAIL: Final = "harness@example.invalid"
_DEFAULT_BRANCH: Final = "main"

# Windows PowerShell's Out-File saves text as UTF-16 with a byte-order mark,
# whose first byte no UTF-8 sequence starts with.
_UTF16_CODEC: Final = "utf-16"
#: Text appended to a stored body, as another session editing the record would.
BODY_EDIT: Final = "\n"

#: Property run configuration for generated requests.
MALFORMED_REQUEST_PROPERTY_SEED: Final = 20260929
MALFORMED_REQUEST_PROPERTY_EXAMPLES: Final = settings().max_examples
MALFORMED_REQUEST_PROPERTY_REPLAY: Final = (
    "just test spx/31-outcomeeng.enabler/32-changes.enabler/61-audit-change.enabler/"
    "tests/test_audit_change_run.compliance.l1.py"
)

_TEMPORARY_DIRECTORY_VARIABLES: Final = ("TMPDIR", "TMP", "TEMP")
#: The variable through which the replayed ``gh`` finds its store file.
STORE_VARIABLE: Final = "AUDIT_CHANGE_STORE"
_PATH_VARIABLE: Final = "PATH"
# The GitHub CLI records a device identifier under its state directory on its
# first run, in the home directory unless the host sets XDG_STATE_HOME. The
# record is the CLI's own telemetry state, so the runner's environment turns
# telemetry off and the home directory snapshot sees only what the audit wrote.
_GH_TELEMETRY_VARIABLE: Final = "GH_TELEMETRY"
_GH_TELEMETRY_OFF: Final = "false"
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


def stored_issue() -> dict[str, object]:
    """Return the captured store issue, decoded afresh."""
    value = json.loads(STORE_ISSUE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{STORE_ISSUE} holds no JSON object")
    return value


def issue_identity(issue: Mapping[str, object]) -> str:
    """Return the ``owner/repository#number`` identity of a store issue."""
    repository = issue["repository"]
    if not isinstance(repository, Mapping):
        raise TypeError("the store issue names no repository")
    return f"{repository['nameWithOwner']}#{issue['number']}"


#: Whole-payload files the format scenarios commit and declare: one the format
#: command leaves unchanged, one it changes, and the first with a linked tag.
FORMAT_CLEAN: Final = _FIXTURES_DIR / "format-clean.md.txt"
FORMAT_DIRTY: Final = _FIXTURES_DIR / "format-dirty.md.txt"
FORMAT_TAGGED: Final = _FIXTURES_DIR / "format-tagged.md.txt"


def body_declaring(path: str, text: str) -> str:
    """Return a record body whose one Declarations subsection replaces ``path`` with ``text``."""
    return (
        "## Statement of Intent\n\n- Output: a file replaced\n\n"
        f"## Declarations\n\n### `{path}`\n\n````markdown\n{text}````\n"
    )


#: The identity of the captured store issue.
FIXTURE_IDENTITY: Final = issue_identity(stored_issue())


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
    """The ``read-record`` and ``start`` calls that opened one audit run."""

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


@dataclass
class AuditWorkspace:
    """A Git repository, a replayed Change Store, and the runner's own directories."""

    root: Path
    runner_temporary_directory: Path
    runner_home_directory: Path
    outside_directory: Path
    observation_directory: Path
    bin_directory: Path
    store_file: Path

    def _store(self) -> dict[str, object]:
        return json.loads(self.store_file.read_text(encoding="utf-8"))

    def put_issue(self, issue: Mapping[str, object]) -> str:
        """Store ``issue`` where the replayed ``gh`` finds it; return its identity."""
        store = self._store()
        store[str(issue["number"])] = dict(issue)
        self.store_file.write_text(json.dumps(store), encoding="utf-8")
        return issue_identity(issue)

    def place_issue(self, number: int | None = None) -> str:
        """Store the captured issue, under ``number`` when given; return its identity."""
        issue = stored_issue()
        if number is not None:
            issue["number"] = number
            issue["title"] = f"{issue['title']} ({number})"
        return self.put_issue(issue)

    def absent_identity(self) -> str:
        """Return an identity the store holds no issue for."""
        owner_repository, _separator, _number = FIXTURE_IDENTITY.partition("#")
        return f"{owner_repository}#{int(_number) + 1000}"

    def body(self, identity: str) -> str:
        """Return the stored body of ``identity`` exactly as stored."""
        number = identity.partition("#")[2]
        issue = self._store()[number]
        if not isinstance(issue, dict):
            raise TypeError(f"the store holds no issue {identity}")
        return str(issue["body"])

    def edit(self, identity: str) -> None:
        """Change a stored body, as another session publishing the record would."""
        number = identity.partition("#")[2]
        store = self._store()
        issue = store[number]
        if not isinstance(issue, dict):
            raise TypeError(f"the store holds no issue {identity}")
        issue["body"] = f"{issue['body']}{BODY_EDIT}"
        self.store_file.write_text(json.dumps(store), encoding="utf-8")

    def set_title(self, identity: str, title: str) -> None:
        """Replace a stored title, as a publish that writes only metadata would."""
        number = identity.partition("#")[2]
        store = self._store()
        issue = store[number]
        if not isinstance(issue, dict):
            raise TypeError(f"the store holds no issue {identity}")
        issue["title"] = title
        self.store_file.write_text(json.dumps(store), encoding="utf-8")

    def set_field(self, identity: str, name: str, value: str) -> None:
        """Replace the stored value of the issue field ``name``."""
        number = identity.partition("#")[2]
        store = self._store()
        issue = store[number]
        if not isinstance(issue, dict):
            raise TypeError(f"the store holds no issue {identity}")
        for entry in issue["issueFieldValues"]["nodes"]:
            if entry["field"]["name"] == name:
                entry["value"] = value
        self.store_file.write_text(json.dumps(store), encoding="utf-8")

    def set_body(self, identity: str, body: str) -> None:
        """Replace a stored body."""
        number = identity.partition("#")[2]
        store = self._store()
        issue = store[number]
        if not isinstance(issue, dict):
            raise TypeError(f"the store holds no issue {identity}")
        issue["body"] = body
        self.store_file.write_text(json.dumps(store), encoding="utf-8")

    def commit(self, files: Mapping[str, str], *, message: str) -> str:
        """Commit ``files`` in the repository; return the full id of the new commit."""
        for relative, content in files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        for argv in (
            ["git", "add", "--", *files],
            [
                "git",
                "-c",
                f"user.name={_COMMITTER}",
                "-c",
                f"user.email={_COMMITTER_EMAIL}",
                "commit",
                "--quiet",
                "-m",
                message,
            ],
        ):
            subprocess.run(argv, cwd=self.root, check=True)  # noqa: S603
        completed = subprocess.run(  # noqa: S603
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()

    def publish_default_branch(self, commit: str) -> str:
        """Point the remote-tracking default branch at ``commit``; return its short name."""
        for argv in (
            ["git", "update-ref", f"refs/remotes/origin/{_DEFAULT_BRANCH}", commit],
            [
                "git",
                "symbolic-ref",
                "refs/remotes/origin/HEAD",
                f"refs/remotes/origin/{_DEFAULT_BRANCH}",
            ],
        ):
            subprocess.run(argv, cwd=self.root, check=True)  # noqa: S603
        return f"origin/{_DEFAULT_BRANCH}"

    def install_formatter(self) -> Path:
        """Place the stand-in format command in the replayed tools; return its path."""
        formatter = self.bin_directory / _FORMATTER_NAME
        shutil.copyfile(FORMATTER, formatter)
        formatter.chmod(_EXECUTABLE_MODE)
        return formatter

    def start_run(self, identity: str) -> StartedRun:
        """Read a stored record and start a run over the body and Base that read returned.

        Both calls are returned as observed; a read that returns no digest
        starts nothing the runner accepts, and the start call shows that.
        """
        runner = load_runner()
        field = runner.RequestField
        operation = runner.Operation
        read = self.invoke(
            {
                field.OPERATION: operation.READ_RECORD,
                field.ISSUE: identity,
                field.ROOT: str(self.root),
            }
        )
        started = self.invoke(
            {
                field.OPERATION: operation.START,
                field.ISSUE: identity,
                field.ROOT: str(self.root),
                field.BODY_SHA256: read.result.get(runner.ResultField.BODY_SHA256),
                field.BASE: read.result.get(runner.ResultField.BASE),
            }
        )
        return StartedRun(read=read, started=started)

    def snapshot(self) -> Snapshot:
        """Record every file in each directory the runner could write to."""
        return Snapshot(
            repository_outside_store=_digests(
                self.root, excluded=frozenset({GIT_METADATA_DIR, SPX_STORE_DIR})
            ),
            spx_store=_digests(self.root / SPX_STORE_DIR),
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

    def invoke(
        self, request: Mapping[str, object], *, launched_from: Path | None = None
    ) -> RunnerCall:
        """Run the runner's entry point with ``request`` on stdin.

        The process starts in ``launched_from``, the repository root by
        default, as a session working in another directory would start it.
        """
        return self.invoke_text(json.dumps(request), launched_from=launched_from)

    def invoke_text(
        self, request_text: str, *, launched_from: Path | None = None
    ) -> RunnerCall:
        """Run the runner's entry point with ``request_text`` on stdin, unparsed."""
        return self._observe(
            request_text,
            request_text.encode(load_runner().TEXT_ENCODING),
            launched_from=launched_from,
        )

    def invoke_utf16(self, request: Mapping[str, object]) -> RunnerCall:
        """Run the runner with ``request`` saved as Windows PowerShell's Out-File saves it."""
        request_text = json.dumps(request)
        return self._observe(request_text, request_text.encode(_UTF16_CODEC))

    def _environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        for variable in _TEMPORARY_DIRECTORY_VARIABLES:
            environment[variable] = str(self.runner_temporary_directory)
        environment[HOME_ENV] = str(self.runner_home_directory)
        environment[_GH_TELEMETRY_VARIABLE] = _GH_TELEMETRY_OFF
        environment[STORE_VARIABLE] = str(self.store_file)
        environment[_PATH_VARIABLE] = os.pathsep.join(
            (str(self.bin_directory), environment.get(_PATH_VARIABLE, ""))
        )
        return environment

    def _observe(
        self,
        request_text: str,
        request_bytes: bytes,
        *,
        launched_from: Path | None = None,
    ) -> RunnerCall:
        handle, report = mkstemp(dir=self.observation_directory, suffix=_REPORT_SUFFIX)
        os.close(handle)
        completed = subprocess.run(  # noqa: S603
            [sys.executable, str(OBSERVER_SCRIPT), str(RUNNER_SCRIPT), report],
            cwd=self.root if launched_from is None else launched_from,
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
    """Yield a fresh repository, a replayed store, and the runner's empty directories."""
    with TemporaryDirectory() as temporary:
        base = Path(temporary)
        workspace = AuditWorkspace(
            root=base / "repository",
            runner_temporary_directory=base / "runner-temporary",
            runner_home_directory=base / "runner-home",
            outside_directory=base / "outside",
            observation_directory=base / "observations",
            bin_directory=base / "bin",
            store_file=base / "store.json",
        )
        for directory in (
            workspace.root,
            workspace.runner_temporary_directory,
            workspace.runner_home_directory,
            workspace.outside_directory,
            workspace.observation_directory,
            workspace.bin_directory,
        ):
            directory.mkdir()
        replay = workspace.bin_directory / _GH_REPLAY_NAME
        shutil.copyfile(GH_REPLAY, replay)
        replay.chmod(_EXECUTABLE_MODE)
        workspace.store_file.write_text("{}", encoding="utf-8")
        subprocess.run(  # noqa: S603
            ["git", "init", "--quiet", str(workspace.root)],  # noqa: S607
            check=True,
        )
        yield workspace


def run_in_parallel(work: Callable[[_T], _R], items: Sequence[_T]) -> list[_R]:
    """Run ``work`` for every item at once and return the results in item order."""
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        return list(pool.map(work, items))


def product_tree_plugin_version() -> str:
    """Return the authored product-tree plugin version."""
    manifest = json.loads(PRODUCT_TREE_MANIFEST.read_text(encoding="utf-8"))
    return str(manifest[PLUGIN_MANIFEST_VERSION_FIELD])


@dataclass(frozen=True)
class AuditPayloads:
    """Scope and finding payloads for one record."""

    scopes: tuple[dict[str, object], ...]
    findings: tuple[dict[str, object], ...]


def audit_payloads(*, subject: str, content: str, tool_version: str) -> AuditPayloads:
    """Build one scope unit per audit concern and one finding per record rule.

    Every finding quotes the complete Draft as its observed state, so the
    rendered projection grows with the record rather than with the harness.
    """
    runner_field = load_runner().SpxField
    language = implementation_languages(PLUGINS_DIR)[0]
    version = product_tree_plugin_version()
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
        for index, rule in enumerate(
            rule_identifiers(load_runner(), RULE_IDENTIFIER_COUNT)
        )
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
