"""Harness for the pickup claim-verification script's ``l1`` tests.

Provides:

- An importlib loader for ``verify_session_claims.py``. The module ships under a
  hyphenated skill path that is not importable by package name; tests load it
  through ``importlib`` (mirroring ``sync_base``).
- ``RecordingRunner`` -- a dependency-injected ``CommandRunner`` double that runs
  real ``git`` against a temp repo (Stage 4: git is cheap, deterministic, and
  observable at ``l1``), returns scripted output for ``spx`` and ``gh`` (Stage 5
  exceptions: contract probe and failure simulation), and records every command
  so the read-only / no-mutation rules are inspectable (exception 6).
- ``session_command_scripts`` -- scripts the ``spx session show`` JSON and prose
  outputs the verifier consumes.

No framework mocks: the runner is an explicit injected object, and git runs for
real against a temp repository built by ``git_context``.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import pathlib
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from types import ModuleType
from typing import Protocol, TypedDict

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFY_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "pickup"
    / "scripts"
    / "verify_session_claims.py"
)
SESSION_ID = "2026-01-01_00-00-00"
SINGLE_VERDICT_COUNT = 1
RUNNER_PARAMETER = "runner"
EXPECTED_SUBPROCESS_CALL_SITES = (("run", "SubprocessRunner.run"),)
UNREACHABLE_SHA = "0" * 40
NODE_SPEC = "spx/21-x.enabler/x.md"
NODE_PATH = "spx/21-x.enabler"
CHILD_NODE_PATH = "spx/21-x.enabler/32-y.enabler"
PRESENT_FILE = "present.md"
ABSENT_FILE = "absent.md"
PR_NUMBER = "256"
PASSING_STATUS = "passing"
FAILING_STATUS = "failing"
CLEAN_GIT_STATUS = "clean"
CLOSED_PR_STATE = "CLOSED"
MISSING_SESSION_ERROR = "missing session"
INVALID_JSON_FRAGMENT = "{"
WRONG_SHAPE_JSON = "[]"
INVALID_JSON_ERROR = "invalid JSON"
WRONG_SHAPE_ERROR = "expected one session record"
MALFORMED_METADATA_ERROR = "malformed metadata"
REACHABLE_WORK_BRANCH = "work/pickup-claim"
ABSENT_WORK_BRANCH = "work/never-pushed"
HEX_LIKE_WORK_BRANCH = "deadbee"
FULL_HEX_WORK_BRANCH = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


type ScriptMap = dict[tuple[str, ...], tuple[int, str, str]]


class SessionKwargs(TypedDict, total=False):
    """Structured claim fields supplied by a mapping case."""

    git_ref: str
    git_status: str
    specs: tuple[str, ...]
    files: tuple[str, ...]
    pr_numbers: tuple[str, ...]


class ClaimVerdictLike(Protocol):
    """Structural view of the shipped script's verdict record."""

    kind: object
    subject: str
    verdict: object
    evidence: str


@dataclass(frozen=True)
class MappingCase:
    """One finite claim relation and its source-contract verdict."""

    id: str
    build: Callable[[pathlib.Path], tuple[SessionKwargs, ScriptMap]]
    kind: object
    verdict: object


def load_verify_session_claims_module() -> ModuleType:
    """Load the ``verify_session_claims`` module via importlib and cache it."""
    cached = sys.modules.get("verify_session_claims")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "verify_session_claims", VERIFY_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load verify_session_claims from {VERIFY_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_session_claims"] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class RecordingRunner:
    """Delegates ``git`` to a real temp repo, scripts ``spx``/``gh``, records calls."""

    repo: pathlib.Path
    scripted: dict[tuple[str, ...], tuple[int, str, str]] = field(default_factory=dict)
    calls: list[list[str]] = field(default_factory=list)

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        self.calls.append(list(cmd))
        cmd_tuple = tuple(cmd)
        for prefix, response in self.scripted.items():
            if cmd_tuple == prefix:
                return response
        for prefix, response in self.scripted.items():
            if cmd_tuple[: len(prefix)] == prefix:
                return response
        if cmd and cmd[0] == "git":
            proc = subprocess.run(cmd, cwd=self.repo, capture_output=True, text=True)
            return proc.returncode, proc.stdout, proc.stderr
        return (1, "", f"not scripted: {' '.join(cmd)}")


def head_sha(repo: pathlib.Path) -> str:
    """Return the repo's current HEAD commit SHA."""
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def dirty_tree(repo: pathlib.Path, name: str = "scratch.txt") -> None:
    """Leave an uncommitted untracked file so ``git status`` reports dirty."""
    (repo / name).write_text("uncommitted\n")


def session_command_scripts(
    *,
    git_ref: str | None = None,
    git_status: str | None = None,
    specs: tuple[str, ...] = (),
    files: tuple[str, ...] = (),
    pr_numbers: tuple[str, ...] = (),
) -> dict[tuple[str, ...], tuple[int, str, str]]:
    """Return ``spx session show`` outputs carrying structured claims."""
    record: dict[str, object] = {
        "id": SESSION_ID,
        "status": "doing",
        "git_ref": git_ref,
        "specs": list(specs),
        "files": list(files),
    }
    front = ["---"]
    for key, value in record.items():
        front.append(f'"{key}": {json.dumps(value)}')
    front.append("---")
    body = ["<metadata>"]
    if git_status is not None:
        body.append(f"  git_status: {git_status}")
    body.append("</metadata>")
    if pr_numbers:
        body.append("<coordination>")
        body.extend(f"- shipped PR #{number}" for number in pr_numbers)
        body.append("</coordination>")
    raw = "\n".join(front + body) + "\n"
    return {
        ("spx", "session", "show", "--json", SESSION_ID): (
            0,
            json.dumps(record),
            "",
        ),
        ("spx", "session", "show", SESSION_ID): (0, raw, ""),
    }


def claim_mapping_cases(module: ModuleType) -> tuple[MappingCase, ...]:
    """Return the finite ``ClaimKind`` x observed-relation mapping domain."""
    claim_kind = module.ClaimKind
    verdict = module.Verdict
    spx_status = tuple(module.SPX_SPEC_STATUS_COMMAND)
    gh_view = tuple(module.GH_PR_VIEW_COMMAND)
    git_verify = tuple(module.GIT_VERIFY_REF_COMMAND)
    git_status = tuple(module.GIT_STATUS_COMMAND[:2])
    return (
        MappingCase(
            "git_ref-sha-reachable",
            lambda repo: ({"git_ref": head_sha(repo)}, {}),
            claim_kind.GIT_REF,
            verdict.CONFIRMED,
        ),
        MappingCase(
            "git_ref-sha-unreachable",
            lambda repo: ({"git_ref": "0" * 40}, {}),
            claim_kind.GIT_REF,
            verdict.DISCREPANCY,
        ),
        MappingCase(
            "injected-path-present",
            _present_path,
            claim_kind.INJECTED_PATH,
            verdict.CONFIRMED,
        ),
        MappingCase(
            "injected-path-missing",
            lambda repo: ({"files": (ABSENT_FILE,)}, {}),
            claim_kind.INJECTED_PATH,
            verdict.DISCREPANCY,
        ),
        MappingCase(
            "node-status-readable",
            lambda repo: (
                {"specs": (NODE_SPEC,)},
                {spx_status: (0, node_status_json(module, status=PASSING_STATUS), "")},
            ),
            claim_kind.NODE_STATUS,
            verdict.CONFIRMED,
        ),
        MappingCase(
            "node-status-unavailable",
            lambda repo: (
                {"specs": (NODE_SPEC,)},
                {spx_status: (1, "", "spx: command not found")},
            ),
            claim_kind.NODE_STATUS,
            verdict.UNVERIFIABLE,
        ),
        MappingCase(
            "uncommitted-clean-matches",
            lambda repo: ({"git_status": "clean"}, {}),
            claim_kind.UNCOMMITTED_STATE,
            verdict.CONFIRMED,
        ),
        MappingCase(
            "uncommitted-clean-now-dirty",
            _dirty_but_recorded_clean,
            claim_kind.UNCOMMITTED_STATE,
            verdict.DISCREPANCY,
        ),
        MappingCase(
            "external-id-readable",
            lambda repo: (
                {"pr_numbers": (PR_NUMBER,)},
                {gh_view: (0, json.dumps({"state": "MERGED"}), "")},
            ),
            claim_kind.EXTERNAL_ID,
            verdict.CONFIRMED,
        ),
        MappingCase(
            "external-id-unavailable",
            lambda repo: (
                {"pr_numbers": (PR_NUMBER,)},
                {gh_view: (1, "", "gh: not found")},
            ),
            claim_kind.EXTERNAL_ID,
            verdict.UNVERIFIABLE,
        ),
        MappingCase(
            "git_ref-git-unavailable",
            lambda repo: (
                {"git_ref": head_sha(repo)},
                {git_verify: (128, "", "fatal: not a git repository")},
            ),
            claim_kind.GIT_REF,
            verdict.UNVERIFIABLE,
        ),
        MappingCase(
            "git_ref-git-launch-failure",
            lambda repo: (
                {"git_ref": head_sha(repo)},
                {
                    git_verify: (
                        module.COMMAND_UNAVAILABLE_EXIT,
                        "",
                        "No such file or directory: 'git'",
                    )
                },
            ),
            claim_kind.GIT_REF,
            verdict.UNVERIFIABLE,
        ),
        MappingCase(
            "uncommitted-git-unavailable",
            lambda repo: (
                {"git_status": "clean"},
                {git_status: (128, "", "fatal: not a git repository")},
            ),
            claim_kind.UNCOMMITTED_STATE,
            verdict.UNVERIFIABLE,
        ),
    )


def _present_path(repo: pathlib.Path) -> tuple[SessionKwargs, ScriptMap]:
    create_present_file(repo)
    return {"files": (PRESENT_FILE,)}, {}


def _dirty_but_recorded_clean(
    repo: pathlib.Path,
) -> tuple[SessionKwargs, ScriptMap]:
    dirty_tree(repo)
    return {"git_status": "clean"}, {}


def verdict_for_kind(
    verdicts: Iterable[ClaimVerdictLike], kind: object
) -> ClaimVerdictLike:
    """Return the sole verdict for ``kind`` or fail with an evidence diagnostic."""
    matching = [item for item in verdicts if item.kind == kind]
    if not matching:
        raise AssertionError(f"no {kind} verdict emitted")
    return matching[0]


def node_status_json(
    module: ModuleType,
    *,
    status: str,
    include_child: bool = False,
    include_non_scalar: bool = False,
) -> str:
    """Build an SPX status payload from the producer's source-owned field set."""
    fields = tuple(module.NODE_STATUS_SCALAR_FIELDS)
    payload: dict[str, object] = {
        fields[0]: NODE_PATH,
        fields[1]: NODE_SPEC,
        fields[2]: NODE_SPEC,
        fields[3]: status,
        fields[4]: "Specified",
        fields[5]: True,
    }
    if include_child:
        payload["children"] = [{fields[0]: CHILD_NODE_PATH, fields[3]: "failing"}]
    if include_non_scalar:
        payload["messages"] = ["nested list values are excluded"]
        payload["metadata"] = {"summary": "nested object values are excluded"}
    return json.dumps(payload)


def node_status_script(
    module: ModuleType,
    *,
    status: str,
    include_child: bool = False,
    include_non_scalar: bool = False,
) -> ScriptMap:
    """Script one source-owned SPX node-status observation."""
    return {
        tuple(module.SPX_SPEC_STATUS_COMMAND): (
            0,
            node_status_json(
                module,
                status=status,
                include_child=include_child,
                include_non_scalar=include_non_scalar,
            ),
            "",
        )
    }


def create_present_file(repo: pathlib.Path) -> pathlib.Path:
    """Create the finite present-path mapping input and return its path."""
    path = repo / PRESENT_FILE
    path.write_text("here\n")
    return path


def expected_node_status_evidence(
    module: ModuleType, *, status: str
) -> dict[str, object]:
    """Return the scalar evidence shape declared by the source contract."""
    payload = json.loads(node_status_json(module, status=status))
    return {key: payload[key] for key in module.NODE_STATUS_SCALAR_FIELDS}


def session_show_json_command(module: ModuleType) -> list[str]:
    """Return the exact source-owned session metadata command."""
    return [*module.SPX_SESSION_SHOW_COMMAND, "--json", SESSION_ID]


def session_show_command(module: ModuleType) -> list[str]:
    """Return the exact source-owned session prose command."""
    return [*module.SPX_SESSION_SHOW_COMMAND, SESSION_ID]


def external_state_script(module: ModuleType, state: str) -> ScriptMap:
    """Script one source-owned GitHub PR state observation."""
    return {tuple(module.GH_PR_VIEW_COMMAND): (0, json.dumps({"state": state}), "")}


def unexpected_runner_calls(
    module: ModuleType, calls: Iterable[list[str]]
) -> tuple[list[str], ...]:
    """Return calls outside the source-owned read-only command registry."""
    prefixes = (
        tuple(module.SPX_SESSION_SHOW_COMMAND),
        tuple(module.SPX_SPEC_STATUS_COMMAND),
        tuple(module.GIT_VERIFY_REF_COMMAND),
        tuple(module.GIT_STATUS_COMMAND),
        tuple(module.GH_PR_VIEW_COMMAND),
    )
    return tuple(
        call
        for call in calls
        if not any(tuple(call[: len(prefix)]) == prefix for prefix in prefixes)
    )


def non_stdlib_import_roots() -> tuple[str, ...]:
    """Return shipped-script imports outside Python's standard library."""
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    allowed = sys.stdlib_module_names | {"__future__"}
    return tuple(sorted(roots - allowed))


def subprocess_call_sites() -> tuple[tuple[str, str | None], ...]:
    """Return every direct subprocess call and its enclosing class method."""
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    calls: list[tuple[str, str | None]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "subprocess"
        ):
            calls.append((function.attr, _enclosing_method(tree, node)))
    return tuple(calls)


def _enclosing_method(tree: ast.AST, target: ast.AST) -> str | None:
    for class_node in ast.walk(tree):
        if not isinstance(class_node, ast.ClassDef):
            continue
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and any(
                child is target for child in ast.walk(node)
            ):
                return f"{class_node.name}.{node.name}"
    return None


def verify_runner_parameter_name(module: ModuleType) -> str:
    """Return the dependency parameter exposed by ``verify``."""
    parameters = inspect.signature(module.verify).parameters
    return next(name for name in parameters if name == RUNNER_PARAMETER)


def empty_path_environment() -> dict[str, str]:
    """Return an environment that forces command-launch failure."""
    return {"PATH": ""}


def malformed_metadata_payloads(module: ModuleType) -> tuple[dict[str, object], ...]:
    """Return the finite invalid shapes for the source-owned metadata contract."""
    git_ref = module.SESSION_GIT_REF_FIELD
    specs = module.SESSION_SPECS_FIELD
    files = module.SESSION_FILES_FIELD
    return (
        {git_ref: 123, specs: [], files: []},
        {git_ref: None, specs: NODE_SPEC, files: []},
        {git_ref: None, specs: [], files: [123]},
        {git_ref: None, files: []},
        {git_ref: None, specs: ["/tmp/escape.md"], files: []},
        {git_ref: None, specs: [], files: ["../escape.md"]},
        {git_ref: None, specs: [""], files: []},
    )


def metadata_script(
    module: ModuleType,
    output: str,
    *,
    exit_code: int = 0,
    stderr: str = "",
) -> ScriptMap:
    """Script the source-owned session metadata command."""
    return {tuple(session_show_json_command(module)): (exit_code, output, stderr)}


def metadata_payload_script(module: ModuleType, payload: object) -> ScriptMap:
    """Script one JSON-serializable session metadata payload."""
    return metadata_script(module, json.dumps(payload))


def missing_session_script(module: ModuleType) -> ScriptMap:
    """Script an unavailable session metadata lookup."""
    return metadata_script(
        module,
        output="",
        exit_code=module.COMMAND_UNAVAILABLE_EXIT,
        stderr=MISSING_SESSION_ERROR,
    )


__all__ = [
    "ABSENT_WORK_BRANCH",
    "CHILD_NODE_PATH",
    "CLEAN_GIT_STATUS",
    "CLOSED_PR_STATE",
    "ClaimVerdictLike",
    "EXPECTED_SUBPROCESS_CALL_SITES",
    "FAILING_STATUS",
    "FULL_HEX_WORK_BRANCH",
    "HEX_LIKE_WORK_BRANCH",
    "INVALID_JSON_ERROR",
    "INVALID_JSON_FRAGMENT",
    "MALFORMED_METADATA_ERROR",
    "MISSING_SESSION_ERROR",
    "MappingCase",
    "NODE_PATH",
    "NODE_SPEC",
    "PASSING_STATUS",
    "PRESENT_FILE",
    "PR_NUMBER",
    "REACHABLE_WORK_BRANCH",
    "RUNNER_PARAMETER",
    "RecordingRunner",
    "SESSION_ID",
    "SINGLE_VERDICT_COUNT",
    "UNREACHABLE_SHA",
    "VERIFY_MODULE_PATH",
    "WRONG_SHAPE_ERROR",
    "WRONG_SHAPE_JSON",
    "claim_mapping_cases",
    "create_present_file",
    "dirty_tree",
    "empty_path_environment",
    "expected_node_status_evidence",
    "external_state_script",
    "head_sha",
    "load_verify_session_claims_module",
    "malformed_metadata_payloads",
    "metadata_payload_script",
    "metadata_script",
    "missing_session_script",
    "node_status_json",
    "node_status_script",
    "non_stdlib_import_roots",
    "session_command_scripts",
    "session_show_command",
    "session_show_json_command",
    "subprocess_call_sites",
    "unexpected_runner_calls",
    "verdict_for_kind",
    "verify_runner_parameter_name",
]
