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
from typing import TypedDict

import pytest

from outcomeeng_testing.harnesses.git_context import accepted_git_context
from outcomeeng_testing.harnesses.verify_session_claims import (
    RecordingRunner,
    dirty_tree,
    head_sha,
    load_verify_session_claims_module,
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
        runner = RecordingRunner(repo=repo, scripted=scripted)

        verdicts = module.verify(session, repo, runner)

        matching = [v for v in verdicts if v.kind == case.kind]
        assert matching, f"no {case.kind} verdict emitted"
        assert matching[0].verdict == case.verdict
