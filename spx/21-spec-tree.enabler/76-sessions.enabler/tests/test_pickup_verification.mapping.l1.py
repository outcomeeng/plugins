"""Mapping tests for the pickup claim-verification script.

Covers the Mapping assertion in ``../sessions.md``: each recorded session-file
claim kind maps to ``Confirmed`` when current state matches the recorded claim,
``Discrepancy`` when it differs, and ``Unverifiable`` when the check cannot run.

The case table parameterizes over the source-owned ``ClaimKind`` x relation
domain. ``l1`` — git runs for real against a temp repo from ``git_context``; the
injected ``RecordingRunner`` scripts ``spx``/``gh`` and records every call. No
mocking: the runner is an explicit injected double.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypedDict

import pytest

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)
from outcomeeng_testing.harnesses.verify_session_claims import (
    RecordingRunner,
    dirty_tree,
    head_sha,
    load_verify_session_claims_module,
    session_show_response,
    write_session_file,
)

module = load_verify_session_claims_module()
Verdict = module.Verdict
ClaimKind = module.ClaimKind

SpecScripts = dict[tuple[str, ...], tuple[int, str, str]]


class SessionKwargs(TypedDict, total=False):
    """The structured claim fields a case feeds to ``write_session_file``."""

    git_ref: str
    git_status: str
    specs: tuple[str, ...]
    files: tuple[str, ...]
    pr_numbers: tuple[str, ...]


SPX_STATUS = ("spx", "spec", "status")
SPX_SESSION_SHOW = ("spx", "session", "show")
GH_VIEW = ("gh", "pr", "view")


@dataclass(frozen=True)
class Case:
    """One claim kind under one relation, with the verdict the mapping demands."""

    id: str
    build: Callable[[pathlib.Path], tuple[SessionKwargs, SpecScripts]]
    kind: object
    verdict: object


def _present_path(repo: pathlib.Path) -> tuple[SessionKwargs, SpecScripts]:
    (repo / "present.md").write_text("here\n")
    return {"files": ("present.md",)}, {}


def _node_ok(repo: pathlib.Path) -> tuple[SessionKwargs, SpecScripts]:
    return {"specs": ("spx/21-x.enabler/x.md",)}, {
        SPX_STATUS: (0, '{"status": "passing"}', "")
    }


def _node_unavailable(repo: pathlib.Path) -> tuple[SessionKwargs, SpecScripts]:
    return {"specs": ("spx/21-x.enabler/x.md",)}, {
        SPX_STATUS: (1, "", "spx: command not found")
    }


def _dirty_but_recorded_clean(
    repo: pathlib.Path,
) -> tuple[SessionKwargs, SpecScripts]:
    dirty_tree(repo)
    return {"git_status": "clean"}, {}


CASES: tuple[Case, ...] = (
    Case(
        "git_ref-sha-reachable",
        lambda repo: ({"git_ref": head_sha(repo)}, {}),
        ClaimKind.GIT_REF,
        Verdict.CONFIRMED,
    ),
    Case(
        "git_ref-sha-unreachable",
        lambda repo: ({"git_ref": "0" * 40}, {}),
        ClaimKind.GIT_REF,
        Verdict.DISCREPANCY,
    ),
    Case(
        "injected-path-present",
        _present_path,
        ClaimKind.INJECTED_PATH,
        Verdict.CONFIRMED,
    ),
    Case(
        "injected-path-missing",
        lambda repo: ({"files": ("absent.md",)}, {}),
        ClaimKind.INJECTED_PATH,
        Verdict.DISCREPANCY,
    ),
    Case("node-status-readable", _node_ok, ClaimKind.NODE_STATUS, Verdict.CONFIRMED),
    Case(
        "node-status-unavailable",
        _node_unavailable,
        ClaimKind.NODE_STATUS,
        Verdict.UNVERIFIABLE,
    ),
    Case(
        "uncommitted-clean-matches",
        lambda repo: ({"git_status": "clean"}, {}),
        ClaimKind.UNCOMMITTED_STATE,
        Verdict.CONFIRMED,
    ),
    Case(
        "uncommitted-clean-now-dirty",
        _dirty_but_recorded_clean,
        ClaimKind.UNCOMMITTED_STATE,
        Verdict.DISCREPANCY,
    ),
    Case(
        "external-id-readable",
        lambda repo: (
            {"pr_numbers": ("256",)},
            {GH_VIEW: (0, '{"state": "MERGED"}', "")},
        ),
        ClaimKind.EXTERNAL_ID,
        Verdict.CONFIRMED,
    ),
    Case(
        "external-id-unavailable",
        lambda repo: ({"pr_numbers": ("256",)}, {GH_VIEW: (1, "", "gh: not found")}),
        ClaimKind.EXTERNAL_ID,
        Verdict.UNVERIFIABLE,
    ),
    Case(
        "git_ref-git-unavailable",
        lambda repo: (
            {"git_ref": head_sha(repo)},
            {("git", "rev-parse"): (128, "", "fatal: not a git repository")},
        ),
        ClaimKind.GIT_REF,
        Verdict.UNVERIFIABLE,
    ),
    Case(
        "uncommitted-git-unavailable",
        lambda repo: (
            {"git_status": "clean"},
            {("git", "status"): (128, "", "fatal: not a git repository")},
        ),
        ClaimKind.UNCOMMITTED_STATE,
        Verdict.UNVERIFIABLE,
    ),
)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_claim_maps_to_verdict(case: Case, tmp_path: pathlib.Path) -> None:
    with accepted_git_context() as repo:
        session_kwargs, scripted = case.build(repo)
        session = write_session_file(tmp_path, **session_kwargs)
        scripted = {
            SPX_SESSION_SHOW: session_show_response(**session_kwargs),
            **scripted,
        }
        runner = RecordingRunner(repo=repo, scripted=scripted)

        verdicts = module.verify(session, repo, runner)

        matching = [v for v in verdicts if v.kind == case.kind]
        assert matching, f"no {case.kind} verdict emitted"
        assert matching[0].verdict == case.verdict


def _only(verdicts: list[Any], kind: object) -> Any:
    matching = [v for v in verdicts if v.kind == kind]
    assert matching, f"no {kind} verdict emitted"
    return matching[0]


def test_node_status_surfaces_changed_value(tmp_path: pathlib.Path) -> None:
    # An observed status that differs from a 'passing' handoff stays Confirmed —
    # the script has no parsed baseline to diff — but the live value reaches the
    # evidence field so the agent can reconcile it against the session prose.
    with accepted_git_context() as repo:
        session_kwargs: SessionKwargs = {"specs": ("spx/21-x.enabler/x.md",)}
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=repo,
            scripted={
                SPX_SESSION_SHOW: session_show_response(**session_kwargs),
                SPX_STATUS: (0, '{"status": "failing"}', ""),
            },
        )

        verdict = _only(module.verify(session, repo, runner), ClaimKind.NODE_STATUS)

        assert verdict.verdict == Verdict.CONFIRMED
        assert "failing" in verdict.evidence


def test_external_id_surfaces_changed_state(tmp_path: pathlib.Path) -> None:
    # A PR that is no longer MERGED stays Confirmed for the same reason; the live
    # state is surfaced in evidence rather than silently dropped.
    with accepted_git_context() as repo:
        session_kwargs: SessionKwargs = {"pr_numbers": ("256",)}
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=repo,
            scripted={
                SPX_SESSION_SHOW: session_show_response(**session_kwargs),
                GH_VIEW: (0, '{"state": "CLOSED"}', ""),
            },
        )

        verdict = _only(module.verify(session, repo, runner), ClaimKind.EXTERNAL_ID)

        assert verdict.verdict == Verdict.CONFIRMED
        assert "CLOSED" in verdict.evidence


def test_spec_entry_emits_both_path_and_node_status(tmp_path: pathlib.Path) -> None:
    # A specs entry is checked twice: as an injected path (filesystem existence)
    # and as a node (spx spec status). Both verdicts are emitted, the path verdict
    # keyed on the file and the node verdict on its parent directory.
    with accepted_git_context() as repo:
        session_kwargs: SessionKwargs = {"specs": ("spx/21-x.enabler/x.md",)}
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=repo,
            scripted={
                SPX_SESSION_SHOW: session_show_response(**session_kwargs),
                SPX_STATUS: (0, '{"status": "passing"}', ""),
            },
        )

        verdicts = module.verify(session, repo, runner)

        path_verdicts = [v for v in verdicts if v.kind == ClaimKind.INJECTED_PATH]
        node_verdicts = [v for v in verdicts if v.kind == ClaimKind.NODE_STATUS]
        # Exactly one verdict per recorded spec entry — no spurious entry from a
        # YAML delimiter absorbed by the list parser.
        assert len(path_verdicts) == 1
        assert len(node_verdicts) == 1
        assert path_verdicts[0].subject == "spx/21-x.enabler/x.md"
        assert node_verdicts[0].subject == "spx/21-x.enabler"


def test_git_ref_branch_on_origin_confirms(tmp_path: pathlib.Path) -> None:
    with handoff_git_env() as env:
        branch = env.push_work_branch("work/pickup-claim")
        session_kwargs: SessionKwargs = {"git_ref": branch}
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=env.root,
            scripted={SPX_SESSION_SHOW: session_show_response(**session_kwargs)},
        )

        verdict = _only(module.verify(session, env.root, runner), ClaimKind.GIT_REF)

        assert verdict.verdict == Verdict.CONFIRMED


def test_hex_like_branch_on_origin_confirms(tmp_path: pathlib.Path) -> None:
    with handoff_git_env() as env:
        branch = env.push_work_branch("deadbee")
        session_kwargs: SessionKwargs = {"git_ref": branch}
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=env.root,
            scripted={SPX_SESSION_SHOW: session_show_response(**session_kwargs)},
        )

        verdict = _only(module.verify(session, env.root, runner), ClaimKind.GIT_REF)

        assert verdict.verdict == Verdict.CONFIRMED


def test_full_hex_branch_on_origin_confirms(tmp_path: pathlib.Path) -> None:
    with handoff_git_env() as env:
        branch = env.push_work_branch("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
        session_kwargs: SessionKwargs = {"git_ref": branch}
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=env.root,
            scripted={SPX_SESSION_SHOW: session_show_response(**session_kwargs)},
        )

        verdict = _only(module.verify(session, env.root, runner), ClaimKind.GIT_REF)

        assert verdict.verdict == Verdict.CONFIRMED


def test_git_ref_branch_absent_from_origin_is_discrepancy(
    tmp_path: pathlib.Path,
) -> None:
    # A branch-name git_ref with no remote-tracking ref resolves to Discrepancy.
    with handoff_git_env() as env:
        session_kwargs: SessionKwargs = {"git_ref": "work/never-pushed"}
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=env.root,
            scripted={SPX_SESSION_SHOW: session_show_response(**session_kwargs)},
        )

        verdict = _only(module.verify(session, env.root, runner), ClaimKind.GIT_REF)

        assert verdict.verdict == Verdict.DISCREPANCY


def test_current_session_frontmatter_shape_still_emits_claims(
    tmp_path: pathlib.Path,
) -> None:
    with accepted_git_context() as repo:
        (repo / "present.md").write_text("here\n")
        session_kwargs: SessionKwargs = {
            "git_ref": head_sha(repo),
            "files": ("present.md",),
        }
        session = write_session_file(tmp_path, **session_kwargs)
        runner = RecordingRunner(
            repo=repo,
            scripted={SPX_SESSION_SHOW: session_show_response(**session_kwargs)},
        )

        verdicts = module.verify(session, repo, runner)

        assert [v.kind for v in verdicts] == [
            ClaimKind.GIT_REF,
            ClaimKind.INJECTED_PATH,
        ]
        assert {v.verdict for v in verdicts} == {Verdict.CONFIRMED}


def test_session_metadata_load_failure_is_unverifiable(
    tmp_path: pathlib.Path,
) -> None:
    with accepted_git_context() as repo:
        session = write_session_file(tmp_path, git_ref=head_sha(repo))
        runner = RecordingRunner(
            repo=repo,
            scripted={SPX_SESSION_SHOW: (1, "", "session not found")},
        )

        verdicts = module.verify(session, repo, runner)

        assert len(verdicts) == 1
        assert verdicts[0].kind == ClaimKind.SESSION_METADATA
        assert verdicts[0].verdict == Verdict.UNVERIFIABLE
