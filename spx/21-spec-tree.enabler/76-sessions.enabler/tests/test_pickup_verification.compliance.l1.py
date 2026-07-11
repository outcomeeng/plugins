"""Compliance tests for pickup claim verification.

Covers the script-behavior Compliance assertions in ``../sessions.md``:

- the verification script resolves node status from ``spx spec status``, reaches
  ``spx``/``gh``/``git`` only through the injected runner, and never executes a
  node's test suite or mutates the working tree, index, or session file.

The workflow-ordering rules (sync before presenting, reconcile before the
checkpoint) carry ``[audit]`` -- the skill body is the implementation, judged by
the skill auditor -- so they are not asserted here as behavioral tests.

``l1`` -- exercises the script in-process with the injected recording runner. No
mocking.
"""

from __future__ import annotations

import ast
import inspect
import json

from outcomeeng_testing.harnesses.git_context import accepted_git_context
from outcomeeng_testing.harnesses.verify_session_claims import (
    VERIFY_MODULE_PATH,
    RecordingRunner,
    SESSION_ID,
    head_sha,
    load_verify_session_claims_module,
    session_command_scripts,
)

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


def test_verify_accepts_injected_runner() -> None:
    module = load_verify_session_claims_module()
    params = inspect.signature(module.verify).parameters
    assert "runner" in params, "verify must accept a dependency-injected runner"


def test_script_imports_are_stdlib_only() -> None:
    tree = ast.parse(VERIFY_MODULE_PATH.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    offenders = roots - STDLIB_IMPORT_ROOTS
    assert not offenders, f"non-stdlib imports in shipped script: {sorted(offenders)}"


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


def test_external_calls_go_through_the_runner() -> None:
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


def test_default_runner_launch_failure_emits_unverifiable() -> None:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        verdicts = module.verify(
            SESSION_ID, repo, module.SubprocessRunner(repo, env={"PATH": ""})
        )

    assert len(verdicts) == 1
    assert verdicts[0].kind == module.ClaimKind.SESSION_METADATA
    assert verdicts[0].verdict == module.Verdict.UNVERIFIABLE


def test_verification_is_read_only_and_uses_spec_status() -> None:
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
                ("spx", "spec", "status"): (0, '{"status": "passing"}', ""),
                ("gh", "pr", "view"): (0, '{"state": "MERGED"}', ""),
            },
        )

        module.verify(SESSION_ID, repo, runner)

        assert any(
            call == ["spx", "session", "show", "--json", SESSION_ID]
            for call in runner.calls
        ), "session claims must come from spx session show --json"
        assert any(
            call == ["spx", "session", "show", SESSION_ID] for call in runner.calls
        ), "session prose must come from spx session show"
        assert any(call[:3] == ["spx", "spec", "status"] for call in runner.calls), (
            "node status must come from spx spec status"
        )
        for call in runner.calls:
            if call and call[0] == "git" and len(call) > 1:
                assert call[1] not in MUTATING_GIT, (
                    f"mutating git command issued: {call}"
                )
            for prefix in TEST_INVOCATIONS:
                assert tuple(call[: len(prefix)]) != prefix, (
                    f"test suite executed: {call}"
                )
        dirty = RecordingRunner(repo=repo).run(["git", "status", "--porcelain"])[1]
        assert dirty.strip() == "", "verification must not mutate the working tree"


def test_node_status_evidence_keeps_target_node_scalar_fields_only() -> None:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted=session_command_scripts(specs=("spx/21-x.enabler/x.md",))
            | {
                ("spx", "spec", "status"): (
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
        evidence = json.loads(node_status[0].evidence)
        assert evidence == {
            "node": "spx/21-x.enabler",
            "path": "spx/21-x.enabler/x.md",
            "result": True,
            "spec": "spx/21-x.enabler/x.md",
            "state": "Specified",
            "status": "passing",
        }


def test_invalid_session_metadata_is_unverifiable() -> None:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted={("spx", "session", "show", "--json", SESSION_ID): (0, "{", "")},
        )

        verdicts = module.verify(SESSION_ID, repo, runner)

        assert len(verdicts) == 1
        assert verdicts[0].kind == module.ClaimKind.SESSION_METADATA
        assert verdicts[0].verdict == module.Verdict.UNVERIFIABLE
        assert "invalid JSON" in verdicts[0].evidence


def test_wrong_shape_session_metadata_is_unverifiable() -> None:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        runner = RecordingRunner(
            repo=repo,
            scripted={("spx", "session", "show", "--json", SESSION_ID): (0, "[]", "")},
        )

        verdicts = module.verify(SESSION_ID, repo, runner)

        assert len(verdicts) == 1
        assert verdicts[0].kind == module.ClaimKind.SESSION_METADATA
        assert verdicts[0].verdict == module.Verdict.UNVERIFIABLE
        assert "expected one session record" in verdicts[0].evidence


def test_malformed_session_metadata_fields_are_unverifiable() -> None:
    module = load_verify_session_claims_module()
    cases: tuple[dict[str, object], ...] = (
        {"git_ref": 123, "specs": [], "files": []},
        {"git_ref": None, "specs": "spx/21-x.enabler/x.md", "files": []},
        {"git_ref": None, "specs": [], "files": [123]},
        {"git_ref": None, "files": []},
        {"git_ref": None, "specs": ["/tmp/escape.md"], "files": []},
        {"git_ref": None, "specs": [], "files": ["../escape.md"]},
        {"git_ref": None, "specs": [""], "files": []},
    )
    for payload in cases:
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

            verdicts = module.verify(SESSION_ID, repo, runner)

            assert len(verdicts) == 1
            assert verdicts[0].kind == module.ClaimKind.SESSION_METADATA
            assert verdicts[0].verdict == module.Verdict.UNVERIFIABLE
            assert "malformed metadata" in verdicts[0].evidence


def test_metadata_loading_does_not_require_local_session_file_body() -> None:
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
