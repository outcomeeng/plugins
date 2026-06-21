"""Compliance tests for pickup claim verification.

Covers the script-behavior Compliance assertions in ``../sessions.md``:

- the verification script resolves node status from ``spx spec status``, reaches
  ``spx``/``gh``/``git`` only through the injected runner, and never executes a
  node's test suite or mutates the working tree, index, or session file.

The workflow-ordering rules (sync before presenting, reconcile before the
checkpoint) carry ``[audit]`` — the skill body is the implementation, judged by
the skill auditor — so they are not asserted here as behavioral tests.

``l1`` — exercises the script in-process with the injected recording runner. No
mocking.
"""

from __future__ import annotations

import ast
import inspect

from outcomeeng_testing.harnesses.git_context import accepted_git_context
from outcomeeng_testing.harnesses.verify_session_claims import (
    VERIFY_MODULE_PATH,
    RecordingRunner,
    load_verify_session_claims_module,
    write_session_file,
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


def test_external_calls_go_through_the_runner() -> None:
    source = VERIFY_MODULE_PATH.read_text()
    assert source.count("subprocess.run(") == 1, (
        "subprocess.run must appear only in the default runner"
    )


def test_verification_is_read_only_and_uses_spec_status() -> None:
    module = load_verify_session_claims_module()
    with accepted_git_context() as repo:
        session = write_session_file(
            repo.parent,
            git_ref="0" * 40,
            git_status="clean",
            specs=("spx/21-x.enabler/x.md",),
            pr_numbers=("256",),
        )
        before = session.read_bytes()
        runner = RecordingRunner(
            repo=repo,
            scripted={
                ("spx", "spec", "status"): (0, '{"status": "passing"}', ""),
                ("gh", "pr", "view"): (0, '{"state": "MERGED"}', ""),
            },
        )

        module.verify(session, repo, runner)

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
        assert session.read_bytes() == before, "session file must not be mutated"
        dirty = RecordingRunner(repo=repo).run(["git", "status", "--porcelain"])[1]
        assert dirty.strip() == "", "verification must not mutate the working tree"
