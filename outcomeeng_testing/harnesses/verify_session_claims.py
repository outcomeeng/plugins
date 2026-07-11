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
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any

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
TEST_NODE_PATH = "spx/21-x.enabler"
TEST_SPEC_PATH = f"{TEST_NODE_PATH}/x.md"
PASSING_STATUS_JSON = '{"status": "passing"}'
PRESENT_FILE_NAME = "present.md"


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


def node_status_surfaces_changed_value() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=(TEST_SPEC_PATH,))
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
            scripted=session_command_scripts(specs=(TEST_SPEC_PATH,))
            | {
                SPX_STATUS: (
                    0,
                    json.dumps(
                        {
                            "node": TEST_NODE_PATH,
                            "status": "passing",
                            "children": [
                                {
                                    "node": f"{TEST_NODE_PATH}/32-y.enabler",
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
            scripted=session_command_scripts(specs=(TEST_SPEC_PATH,))
            | {SPX_STATUS: (0, PASSING_STATUS_JSON, "")},
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
        assert path_verdicts[0].subject == TEST_SPEC_PATH
        assert node_verdicts[0].subject == TEST_NODE_PATH
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
        (repo / PRESENT_FILE_NAME).write_text("here\n")
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(
                git_ref=head_sha(repo),
                files=(PRESENT_FILE_NAME,),
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


def session_prose_load_failure_is_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts()
            | {
                ("spx", "session", "show", SESSION_ID): (
                    1,
                    "",
                    "session prose unavailable",
                )
            },
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.SESSION_METADATA
        )
        assert verdict.verdict == module.Verdict.UNVERIFIABLE
        assert "session prose unavailable" in verdict.evidence
        return True


def missing_injected_path_is_discrepancy() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(files=("absent.md",)),
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.INJECTED_PATH
        )
        assert verdict.verdict == module.Verdict.DISCREPANCY
        return True


def unavailable_node_status_is_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=(TEST_SPEC_PATH,))
            | {SPX_STATUS: (1, "", "spx unavailable")},
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.NODE_STATUS
        )
        assert verdict.verdict == module.Verdict.UNVERIFIABLE
        return True


def dirty_state_is_discrepancy() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        dirty_tree(repo)
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(git_status="clean"),
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner),
            module.ClaimKind.UNCOMMITTED_STATE,
        )
        assert verdict.verdict == module.Verdict.DISCREPANCY
        return True


def clean_state_is_confirmed() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(git_status="clean"),
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner),
            module.ClaimKind.UNCOMMITTED_STATE,
        )
        assert verdict.verdict == module.Verdict.CONFIRMED
        return True


def unavailable_git_ref_is_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(git_ref="unavailable-ref")
            | {
                (
                    "git",
                    "rev-parse",
                    "--verify",
                    "--quiet",
                    "refs/remotes/origin/unavailable-ref",
                ): (module.COMMAND_UNAVAILABLE_EXIT, "", "git unavailable")
            },
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.GIT_REF
        )
        assert verdict.verdict == module.Verdict.UNVERIFIABLE
        return True


def unavailable_git_status_is_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(git_status="clean")
            | {("git", "status", "--porcelain"): (1, "", "git unavailable")},
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner),
            module.ClaimKind.UNCOMMITTED_STATE,
        )
        assert verdict.verdict == module.Verdict.UNVERIFIABLE
        return True


def unavailable_external_id_is_unverifiable() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(pr_numbers=("256",))
            | {GH_VIEW: (1, "", "gh unavailable")},
        )
        verdict = _only(
            module.verify(SESSION_ID, repo, runner), module.ClaimKind.EXTERNAL_ID
        )
        assert verdict.verdict == module.Verdict.UNVERIFIABLE
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
                specs=(TEST_SPEC_PATH,),
                pr_numbers=("256",),
            )
            | {
                SPX_STATUS: (0, PASSING_STATUS_JSON, ""),
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
            scripted=session_command_scripts(specs=(TEST_SPEC_PATH,))
            | {
                SPX_STATUS: (
                    0,
                    json.dumps(
                        {
                            "node": TEST_NODE_PATH,
                            "path": TEST_SPEC_PATH,
                            "spec": TEST_SPEC_PATH,
                            "state": "Specified",
                            "status": "passing",
                            "result": True,
                            "children": [
                                {
                                    "node": f"{TEST_NODE_PATH}/32-y.enabler",
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
            "node": TEST_NODE_PATH,
            "path": TEST_SPEC_PATH,
            "result": True,
            "spec": TEST_SPEC_PATH,
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
        {"git_ref": None, "specs": TEST_SPEC_PATH, "files": []},
        {"git_ref": None, "specs": [], "files": [123]},
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


def optional_session_injection_lists_default_to_empty() -> bool:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted={
                ("spx", "session", "show", "--json", SESSION_ID): (
                    0,
                    json.dumps({"git_ref": None}),
                    "",
                ),
                ("spx", "session", "show", SESSION_ID): (
                    0,
                    "<metadata>\n</metadata>\n",
                    "",
                ),
            },
        )
        assert module.verify(SESSION_ID, repo, runner) == []
        return True


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
