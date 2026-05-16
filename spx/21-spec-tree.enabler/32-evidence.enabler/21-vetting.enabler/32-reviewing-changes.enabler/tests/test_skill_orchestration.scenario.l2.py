"""End-to-end scenario test for the reviewing-changes script chain.

Covers this clause in ``../reviewing-changes.md``:

Scenarios
- Given a ``pr.json`` with ``base_ref`` set under the configured
  thread-store backend, the script chain reads it, computes the diff
  against ``base_ref``, emits a review result, validates it through the
  arbiter CLI, and writes both ``review-result.json`` and ``review.md``
  for the current branch slug.

The test wires the chain end-to-end against a synthetic git repository
seeded under a ``tmp_path``-rooted thread store:

1. Initialise a git product in ``tmp_path``, commit a base file,
   create a branch, and commit a follow-up modification — the branch
   tip differs from the base by a real diff.
2. Write a ``pr.json`` record (via ``write_record.py``) describing the
   PR shape: ``baseRefName`` = the base branch name.
3. Invoke ``compute_diff.py`` to produce a non-empty diff on stdout.
4. Pipe a synthesised, conforming ``review-result.json`` through
   ``validate_review_result.py`` and then ``write_record.py``.
5. Invoke ``render_review.py`` to produce ``review.md`` and persist it
   through ``write_record.py``.
6. Assert both records are retrievable through ``read_record.py``
   under the branch's slug.

The test is ``l2`` because it spawns ``git`` and multiple Python
subprocesses; it does not depend on remote services or credentials.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    COMPUTE_DIFF_SCRIPT,
    RENDER_REVIEW_SCRIPT,
    VALIDATE_REVIEW_RESULT_SCRIPT,
    make_review_result_dict,
)
from outcomeeng_testing.harnesses.thread_store import (
    READ_RECORD_SCRIPT,
    WRITE_RECORD_SCRIPT,
    load_branch_slug_module,
    run_script,
)


def _run_git(*args: str, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """Run a git command rooted at ``cwd`` with isolated config.

    The git invocation suppresses global config and signing so the
    test does not inherit operator identity or commit-signing settings.
    """
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    return subprocess.run(  # noqa: S603 — args come from the test, not user input
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def _init_repo_with_branch(repo: pathlib.Path) -> str:
    """Set up a tiny git repo with ``main`` and a feature branch.

    Returns the base ref name (``main``).
    """
    _run_git("init", "-q", "-b", "main", str(repo), cwd=pathlib.Path.cwd())
    _run_git("config", "commit.gpgsign", "false", cwd=repo)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _run_git("add", "README.md", cwd=repo)
    _run_git("commit", "-q", "-m", "initial", cwd=repo)
    _run_git("switch", "-c", "feature/x", cwd=repo)
    (repo / "README.md").write_text("hello\nworld\n", encoding="utf-8")
    _run_git("add", "README.md", cwd=repo)
    _run_git("commit", "-q", "-m", "add world", cwd=repo)
    return "main"


def _make_env_for_temp_store(
    store_root: pathlib.Path, cwd: pathlib.Path
) -> dict[str, str]:
    """Return an env dict that points the thread store at ``store_root``.

    ``compute_diff.py`` runs ``git`` inside ``cwd``; the env also wipes
    git's global configuration so the subprocess does not pick up
    workstation-level identity.
    """
    env = {
        **os.environ,
        "SPX_VET_BACKEND": "local",
        "SPX_VET_LOCAL_ROOT": str(store_root),
        "PWD": str(cwd),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }
    return env


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists()
    or not RENDER_REVIEW_SCRIPT.exists()
    or not VALIDATE_REVIEW_RESULT_SCRIPT.exists(),
    reason=(
        "Reviewing-changes scripts are not yet present; the orchestration "
        "test runs once the lens scripts are implemented."
    ),
)
class TestSkillOrchestrationChain:
    """End-to-end chain: pr.json → diff → review-result → arbiter → render."""

    def test_chain_persists_review_result_and_review_md(
        self, tmp_path: pathlib.Path
    ) -> None:
        # 1. Real git repo with a base branch and a feature branch.
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = _init_repo_with_branch(repo)

        # 2. Thread-store root sits outside the repo so the .spx writes
        #    never interfere with git status.
        store_root = tmp_path / "store"
        store_root.mkdir()
        env = _make_env_for_temp_store(store_root, cwd=repo)

        # 3. Derive the slug for the current branch via the canonical helper.
        branch_slug_module = load_branch_slug_module()
        slug = branch_slug_module.branch_slug("feature/x")

        # 4. Seed pr.json into the thread store.
        pr_payload = json.dumps(
            {
                "baseRefName": base_ref,
                "headRefName": "feature/x",
                "number": 1,
                "title": "Synthetic PR",
            }
        )
        result = run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "pr.json",
            stdin=pr_payload,
            env=env,
        )
        assert result.returncode == 0, result.stderr

        # 5. compute_diff.py reads pr.json (via the thread store), runs
        #    git diff against the base, and emits the diff to stdout.
        diff_result = subprocess.run(  # noqa: S603 — script path is from the harness
            [
                sys.executable,
                str(COMPUTE_DIFF_SCRIPT),
                "--slug",
                slug,
            ],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert diff_result.returncode == 0, diff_result.stderr
        # The diff must reference the modified file. A truly empty diff
        # means compute_diff did not pick up the base ref correctly.
        assert "README.md" in diff_result.stdout

        # 6. Synthesise a conforming review-result.json. The "model emit"
        #    step in production is the LLM agent; the test substitutes a
        #    fixed conforming document and validates it through the
        #    arbiter to exercise the validation hand-off.
        review_result_payload = json.dumps(make_review_result_dict())
        arbiter_result = run_script(
            VALIDATE_REVIEW_RESULT_SCRIPT,
            stdin=review_result_payload,
            env=env,
        )
        assert arbiter_result.returncode == 0, arbiter_result.stderr

        # 7. Persist the validated review-result.json.
        write_rr = run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "review-result.json",
            stdin=review_result_payload,
            env=env,
        )
        assert write_rr.returncode == 0, write_rr.stderr

        # 8. render_review.py reads the review-result and writes review.md.
        render_result = subprocess.run(  # noqa: S603 — script path is from the harness
            [
                sys.executable,
                str(RENDER_REVIEW_SCRIPT),
                "--slug",
                slug,
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert render_result.returncode == 0, render_result.stderr
        rendered_markdown = render_result.stdout

        # 9. Persist the rendered review.md.
        write_md = run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "review.md",
            stdin=rendered_markdown,
            env=env,
        )
        assert write_md.returncode == 0, write_md.stderr

        # 10. Both records are retrievable through read_record.py.
        read_rr = run_script(
            READ_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "review-result.json",
            env=env,
        )
        assert read_rr.returncode == 0
        assert json.loads(read_rr.stdout)["decision"] in {
            "approve",
            "request_changes",
            "comment",
        }

        read_md = run_script(
            READ_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "review.md",
            env=env,
        )
        assert read_md.returncode == 0
        assert read_md.stdout.strip() != ""
