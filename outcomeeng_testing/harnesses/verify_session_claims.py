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
import inspect
import importlib.util
import json
import pathlib
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, TypedDict

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)

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


type ScriptMap = dict[tuple[str, ...], tuple[int, str, str]]


class SessionKwargs(TypedDict, total=False):
    git_ref: str
    git_status: str
    specs: tuple[str, ...]
    files: tuple[str, ...]
    pr_numbers: tuple[str, ...]


SPX_STATUS = ("spx", "spec", "status")
GH_VIEW = ("gh", "pr", "view")
STDLIB_IMPORT_ROOTS = frozenset(
    {
        "__future__",
        "argparse",
        "json",
        "re",
        "subprocess",
        "sys",
        "dataclasses",
        "enum",
        "pathlib",
        "typing",
        "collections",
    }
)
MUTATING_GIT = frozenset(
    {
        "commit",
        "reset",
        "checkout",
        "add",
        "rm",
        "push",
        "restore",
        "switch",
        "stash",
        "merge",
        "rebase",
    }
)
TEST_INVOCATIONS = (
    ("spx", "test"),
    ("pytest",),
    ("python", "-m", "pytest"),
    ("python3", "-m", "pytest"),
)


@dataclass(frozen=True)
class ClaimMappingCase:
    id: str
    build: Callable[[pathlib.Path], tuple[SessionKwargs, ScriptMap]]
    kind: object
    verdict: object


def claim_mapping_cases() -> tuple[ClaimMappingCase, ...]:
    module = load_verify_session_claims_module()
    return (
        ClaimMappingCase(
            "git_ref-sha-reachable",
            lambda repo: ({"git_ref": head_sha(repo)}, {}),
            module.ClaimKind.GIT_REF,
            module.Verdict.CONFIRMED,
        ),
        ClaimMappingCase(
            "git_ref-sha-unreachable",
            lambda repo: ({"git_ref": "0" * 40}, {}),
            module.ClaimKind.GIT_REF,
            module.Verdict.DISCREPANCY,
        ),
        ClaimMappingCase(
            "injected-path-present",
            _present_path,
            module.ClaimKind.INJECTED_PATH,
            module.Verdict.CONFIRMED,
        ),
        ClaimMappingCase(
            "injected-path-missing",
            lambda repo: ({"files": ("absent.md",)}, {}),
            module.ClaimKind.INJECTED_PATH,
            module.Verdict.DISCREPANCY,
        ),
        ClaimMappingCase(
            "node-status-readable",
            _node_ok,
            module.ClaimKind.NODE_STATUS,
            module.Verdict.CONFIRMED,
        ),
        ClaimMappingCase(
            "node-status-unavailable",
            _node_unavailable,
            module.ClaimKind.NODE_STATUS,
            module.Verdict.UNVERIFIABLE,
        ),
        ClaimMappingCase(
            "uncommitted-clean-matches",
            lambda repo: ({"git_status": "clean"}, {}),
            module.ClaimKind.UNCOMMITTED_STATE,
            module.Verdict.CONFIRMED,
        ),
        ClaimMappingCase(
            "uncommitted-clean-now-dirty",
            _dirty_but_recorded_clean,
            module.ClaimKind.UNCOMMITTED_STATE,
            module.Verdict.DISCREPANCY,
        ),
        ClaimMappingCase(
            "external-id-readable",
            lambda repo: (
                {"pr_numbers": ("256",)},
                {GH_VIEW: (0, '{"state": "MERGED"}', "")},
            ),
            module.ClaimKind.EXTERNAL_ID,
            module.Verdict.CONFIRMED,
        ),
        ClaimMappingCase(
            "external-id-unavailable",
            lambda repo: (
                {"pr_numbers": ("256",)},
                {GH_VIEW: (1, "", "gh: not found")},
            ),
            module.ClaimKind.EXTERNAL_ID,
            module.Verdict.UNVERIFIABLE,
        ),
        ClaimMappingCase(
            "git_ref-git-unavailable",
            lambda repo: (
                {"git_ref": head_sha(repo)},
                {("git", "rev-parse"): (128, "", "fatal: not a git repository")},
            ),
            module.ClaimKind.GIT_REF,
            module.Verdict.UNVERIFIABLE,
        ),
        ClaimMappingCase(
            "git_ref-git-launch-failure",
            lambda repo: (
                {"git_ref": head_sha(repo)},
                {
                    ("git", "rev-parse"): (
                        module.COMMAND_UNAVAILABLE_EXIT,
                        "",
                        "No such file or directory: 'git'",
                    )
                },
            ),
            module.ClaimKind.GIT_REF,
            module.Verdict.UNVERIFIABLE,
        ),
        ClaimMappingCase(
            "uncommitted-git-unavailable",
            lambda repo: (
                {"git_status": "clean"},
                {("git", "status"): (128, "", "fatal: not a git repository")},
            ),
            module.ClaimKind.UNCOMMITTED_STATE,
            module.Verdict.UNVERIFIABLE,
        ),
    )


def claim_maps_to_verdict(case: ClaimMappingCase) -> bool:
    with accepted_git_context() as repo:
        session_kwargs, scripted = case.build(repo)
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(**session_kwargs) | scripted,
        )
        matching = [
            verdict
            for verdict in load_verify_session_claims_module().verify(
                SESSION_ID, repo, runner
            )
            if verdict.kind == case.kind
        ]
        assert matching, f"no {case.kind} verdict emitted"
        assert matching[0].verdict == case.verdict
        return True


def all_claim_mapping_cases_map_to_verdict() -> bool:
    for case in claim_mapping_cases():
        assert claim_maps_to_verdict(case)
    return True


def node_status_surfaces_changed_value() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=("spx/21-x.enabler/x.md",))
            | {SPX_STATUS: (0, '{"status": "failing"}', "")},
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.NODE_STATUS
        )
        assert verdict.verdict == module.Verdict.CONFIRMED
        assert "failing" in verdict.evidence
        return True


def node_status_evidence_excludes_child_tree() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=("spx/21-x.enabler/x.md",))
            | {
                SPX_STATUS: (
                    0,
                    json.dumps(
                        {
                            "node": "spx/21-x.enabler",
                            "status": "passing",
                            "children": [
                                {
                                    "node": "spx/21-x.enabler/32-y.enabler",
                                    "status": "failing",
                                }
                            ],
                        }
                    ),
                    "",
                )
            },
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.NODE_STATUS
        )
        assert verdict.verdict == module.Verdict.CONFIRMED
        assert "passing" in verdict.evidence
        assert "32-y.enabler" not in verdict.evidence
        assert "children" not in verdict.evidence
        return True


def external_id_surfaces_changed_state() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(pr_numbers=("256",))
            | {GH_VIEW: (0, '{"state": "CLOSED"}', "")},
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.EXTERNAL_ID
        )
        assert verdict.verdict == module.Verdict.CONFIRMED
        assert "CLOSED" in verdict.evidence
        return True


def spec_entry_emits_both_path_and_node_status() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=("spx/21-x.enabler/x.md",))
            | {SPX_STATUS: (0, '{"status": "passing"}', "")},
        )
        verdicts = module.verify(SESSION_ID, repo, runner)
        path_verdicts = [
            verdict
            for verdict in verdicts
            if verdict.kind == module.ClaimKind.INJECTED_PATH
        ]
        node_verdicts = [
            verdict
            for verdict in verdicts
            if verdict.kind == module.ClaimKind.NODE_STATUS
        ]
        assert len(path_verdicts) == 1
        assert len(node_verdicts) == 1
        assert path_verdicts[0].subject == "spx/21-x.enabler/x.md"
        assert node_verdicts[0].subject == "spx/21-x.enabler"
        return True


def git_ref_branch_on_origin_confirms() -> bool:
    return _branch_ref_confirms("work/pickup-claim")


def hex_like_branch_on_origin_confirms() -> bool:
    return _branch_ref_confirms("deadbee")


def full_hex_branch_on_origin_confirms() -> bool:
    return _branch_ref_confirms("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")


def git_ref_branch_absent_from_origin_is_discrepancy() -> bool:
    module = load_verify_session_claims_module()
    with handoff_git_env() as env:
        runner = RecordingRunner(
            repo=env.root,
            scripted=session_command_scripts(git_ref="work/never-pushed"),
        )
        verdict = _only(
            module.verify(SESSION_ID, env.root, runner), module.ClaimKind.GIT_REF
        )
        assert verdict.verdict == module.Verdict.DISCREPANCY
        return True


def current_session_frontmatter_shape_still_emits_claims() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        (repo / "present.md").write_text("here\n")
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(
                git_ref=head_sha(repo),
                files=("present.md",),
            ),
        )
        verdicts = module.verify(SESSION_ID, repo, runner)
        assert [verdict.kind for verdict in verdicts] == [
            module.ClaimKind.GIT_REF,
            module.ClaimKind.INJECTED_PATH,
        ]
        assert {verdict.verdict for verdict in verdicts} == {module.Verdict.CONFIRMED}
        return True


def session_load_failure_is_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted={
                ("spx", "session", "show", "--json", SESSION_ID): (
                    1,
                    "",
                    "missing session",
                )
            },
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.SESSION_METADATA
        )
        assert verdict.verdict == module.Verdict.UNVERIFIABLE
        assert "missing session" in verdict.evidence
        return True


def verify_accepts_injected_runner() -> bool:
    assert (
        "runner"
        in inspect.signature(load_verify_session_claims_module().verify).parameters
    )
    return True


def script_imports_are_stdlib_only() -> bool:
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    offenders = roots - STDLIB_IMPORT_ROOTS
    assert not offenders, f"non-stdlib imports in shipped script: {sorted(offenders)}"
    return True


def external_calls_go_through_the_runner() -> bool:
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    subprocess_calls: list[tuple[str, str | None]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
        ):
            subprocess_calls.append((func.attr, _enclosing_method(tree, node)))
    assert subprocess_calls == [("run", "SubprocessRunner.run")], (
        "subprocess calls must appear only in SubprocessRunner.run"
    )
    return True


def default_runner_launch_failure_emits_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        verdicts = module.verify(
            SESSION_ID, repo, module.SubprocessRunner(repo, env={"PATH": ""})
        )
    assert len(verdicts) == 1
    assert verdicts[0].kind == module.ClaimKind.SESSION_METADATA
    assert verdicts[0].verdict == module.Verdict.UNVERIFIABLE
    return True


def verification_is_read_only_and_uses_spec_status() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(
                git_ref="0" * 40,
                git_status="clean",
                specs=("spx/21-x.enabler/x.md",),
                pr_numbers=("256",),
            )
            | {
                SPX_STATUS: (0, '{"status": "passing"}', ""),
                GH_VIEW: (0, '{"state": "MERGED"}', ""),
            },
        )
        module.verify(SESSION_ID, repo, runner)
        assert ["spx", "session", "show", "--json", SESSION_ID] in runner.calls
        assert ["spx", "session", "show", SESSION_ID] in runner.calls
        assert any(call[:3] == ["spx", "spec", "status"] for call in runner.calls)
        for call in runner.calls:
            _assert_read_only_call(call)
        assert (
            RecordingRunner(repo=repo).run(["git", "status", "--porcelain"])[1].strip()
            == ""
        )
        return True


def node_status_evidence_keeps_target_node_scalar_fields_only() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=("spx/21-x.enabler/x.md",))
            | {
                SPX_STATUS: (
                    0,
                    json.dumps(
                        {
                            "node": "spx/21-x.enabler",
                            "path": "spx/21-x.enabler/x.md",
                            "spec": "spx/21-x.enabler/x.md",
                            "state": "Specified",
                            "status": "passing",
                            "result": True,
                            "children": [
                                {
                                    "node": "spx/21-x.enabler/32-y.enabler",
                                    "status": "failing",
                                }
                            ],
                            "messages": ["nested list values are excluded"],
                            "metadata": {
                                "summary": "nested object values are excluded"
                            },
                        }
                    ),
                    "",
                )
            },
        )
        verdicts = module.verify(SESSION_ID, repo, runner)
        node_status = [
            verdict
            for verdict in verdicts
            if verdict.kind == module.ClaimKind.NODE_STATUS
        ]
        assert len(node_status) == 1
        assert json.loads(node_status[0].evidence) == {
            "node": "spx/21-x.enabler",
            "path": "spx/21-x.enabler/x.md",
            "result": True,
            "spec": "spx/21-x.enabler/x.md",
            "state": "Specified",
            "status": "passing",
        }
        return True


def invalid_session_metadata_is_unverifiable() -> bool:
    return _session_metadata_error_is_unverifiable("{", "invalid JSON")


def wrong_shape_session_metadata_is_unverifiable() -> bool:
    return _session_metadata_error_is_unverifiable("[]", "expected one session record")


def malformed_session_metadata_fields_are_unverifiable() -> bool:
    malformed_payloads: tuple[dict[str, Any], ...] = (
        {"git_ref": 123, "specs": [], "files": []},
        {"git_ref": None, "specs": "spx/21-x.enabler/x.md", "files": []},
        {"git_ref": None, "specs": [], "files": [123]},
        {"git_ref": None, "files": []},
        {
            "git_ref": None,
            "specs": [pathlib.PurePosixPath("/", "escape.md").as_posix()],
            "files": [],
        },
        {"git_ref": None, "specs": [], "files": ["../escape.md"]},
        {"git_ref": None, "specs": [""], "files": []},
    )
    for payload in malformed_payloads:
        with accepted_git_context() as repo:
            runner = RecordingRunner(
                repo=repo,
                scripted={
                    ("spx", "session", "show", "--json", SESSION_ID): (
                        0,
                        json.dumps(payload),
                        "",
                    )
                },
            )
            verdicts = load_verify_session_claims_module().verify(
                SESSION_ID, repo, runner
            )
            assert len(verdicts) == 1
            assert (
                verdicts[0].kind
                == load_verify_session_claims_module().ClaimKind.SESSION_METADATA
            )
            assert (
                verdicts[0].verdict
                == load_verify_session_claims_module().Verdict.UNVERIFIABLE
            )
            assert "malformed metadata" in verdicts[0].evidence
    return True


def metadata_loading_does_not_require_local_session_file_body() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(git_ref=head_sha(repo)),
        )
        verdicts = module.verify(SESSION_ID, repo, runner)
        assert len(verdicts) == 1
        assert verdicts[0].kind == module.ClaimKind.GIT_REF
        assert verdicts[0].verdict == module.Verdict.CONFIRMED
        return True


def _present_path(repo: pathlib.Path) -> tuple[SessionKwargs, ScriptMap]:
    (repo / "present.md").write_text("here\n")
    return {"files": ("present.md",)}, {}


def _node_ok(repo: pathlib.Path) -> tuple[SessionKwargs, ScriptMap]:
    return {"specs": ("spx/21-x.enabler/x.md",)}, {
        SPX_STATUS: (0, '{"status": "passing"}', "")
    }


def _node_unavailable(repo: pathlib.Path) -> tuple[SessionKwargs, ScriptMap]:
    return {"specs": ("spx/21-x.enabler/x.md",)}, {
        SPX_STATUS: (1, "", "spx: command not found")
    }


def _dirty_but_recorded_clean(repo: pathlib.Path) -> tuple[SessionKwargs, ScriptMap]:
    dirty_tree(repo)
    return {"git_status": "clean"}, {}


def _only(verdicts: list[Any], kind: object) -> Any:
    matching = [verdict for verdict in verdicts if verdict.kind == kind]
    assert matching, f"no {kind} verdict emitted"
    return matching[0]


def _branch_ref_confirms(branch_name: str) -> bool:
    module = load_verify_session_claims_module()
    with handoff_git_env() as env:
        branch = env.push_work_branch(branch_name)
        runner = RecordingRunner(
            repo=env.root, scripted=session_command_scripts(git_ref=branch)
        )
        verdict = _only(
            module.verify(SESSION_ID, env.root, runner), module.ClaimKind.GIT_REF
        )
        assert verdict.verdict == module.Verdict.CONFIRMED
        return True


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


def _assert_read_only_call(call: list[str]) -> None:
    if call and call[0] == "git" and len(call) > 1:
        assert call[1] not in MUTATING_GIT, f"mutating git command issued: {call}"
    for prefix in TEST_INVOCATIONS:
        assert tuple(call[: len(prefix)]) != prefix, f"test suite executed: {call}"


def _session_metadata_error_is_unverifiable(payload: str, evidence: str) -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted={
                ("spx", "session", "show", "--json", SESSION_ID): (0, payload, "")
            },
        )
        verdicts = module.verify(SESSION_ID, repo, runner)
        assert len(verdicts) == 1
        assert verdicts[0].kind == module.ClaimKind.SESSION_METADATA
        assert verdicts[0].verdict == module.Verdict.UNVERIFIABLE
        assert evidence in verdicts[0].evidence
        return True
