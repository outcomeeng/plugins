"""End-to-end scenario tests for the review-changes script chain.

Covers the Scenario clauses in ``../reviewing-changes.md`` that govern
how ``compute_diff.py`` resolves refs and how the end-to-end chain validates
and renders outputs:

1. ``SPX_VERIFY_BASE_REF`` env set -> env value is used as ``base_ref``.
2. No env + ``refs/remotes/origin/HEAD`` resolves -> derived from that symbolic
   ref, stripped of the prefix.
3. No source available -> non-zero exit; stderr names the env and git sources.
4. ``SPX_VERIFY_HEAD_REF`` env set -> env value is used as ``head_ref``.
5. No ``SPX_VERIFY_HEAD_REF`` env -> ``HEAD`` is used as ``head_ref``.

The tests are ``l2`` because they spawn ``git`` and multiple Python
subprocesses against a synthetic git repository seeded under ``tmp_path``;
they do not depend on remote services or credentials.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess

import pytest

from outcomeeng_testing.harnesses.changeset_scope import build_stale_local_base_repo
from outcomeeng_testing.harnesses.reviewing_changes import (
    COMPUTE_DIFF_SCRIPT,
    RENDER_REVIEW_SCRIPT,
    VALIDATE_REVIEW_RESULT_SCRIPT,
    make_review_result_dict,
    run_compute_diff_in_process,
    run_render_review_in_process,
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


def _make_env(cwd: pathlib.Path) -> dict[str, str]:
    """Return an env dict for isolated git subprocesses.

    ``compute_diff.py`` runs ``git`` inside ``cwd``; the env wipes git's global
    configuration so the subprocess does not pick up workstation-level identity.
    """
    env = {
        **os.environ,
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
        "test runs once the verification skill scripts are implemented."
    ),
)
class TestSkillOrchestrationChain:
    """End-to-end chain: diff -> review-result -> arbiter -> render."""

    def test_chain_validates_and_renders_review_result(
        self, tmp_path: pathlib.Path
    ) -> None:
        # 1. Real git repo with a base branch and a feature branch.
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = _init_repo_with_branch(repo)

        # 2. compute_diff.py reads the explicit base ref, runs git diff against
        #    that base, and emits the diff to stdout.
        env = _make_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        diff_result = run_compute_diff_in_process(repo=repo, env=env)
        assert diff_result.returncode == 0, diff_result.stderr
        # The diff must reference the modified file. A truly empty diff
        # means compute_diff did not pick up the base ref correctly.
        assert "README.md" in diff_result.stdout

        # 3. Synthesise a conforming review-result JSON payload. The "model emit"
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

        # 4. render_review.py reads the validated JSON payload and writes the
        #    human-readable surface to stdout.
        render_result = run_render_review_in_process(stdin=review_result_payload)
        assert render_result.returncode == 0, render_result.stderr
        rendered = render_result.stdout
        # Two-severity render shape (matches the REVIEW.template.md
        # taxonomy): the default fixture has one debt-severity finding and
        # no blocking. Render reports both severities uniformly — the empty
        # BLOCKING bucket as its `none` census marker, the debt finding as a
        # DEBT heading. FOLLOW-UP is no longer part of the taxonomy and must
        # not appear; the legacy class labels NEEDS-ANSWER and NOTE must not
        # appear either.
        assert "## Change Review" in rendered, (
            "review.md must carry the Change Review title from document.md template"
        )
        assert "BLOCKING: none" in rendered, (
            "empty BLOCKING bucket must render its none-blocking.md census marker"
        )
        assert "### DEBT [standards]:" in rendered, (
            "debt-severity finding must render as DEBT via finding-debt.md"
        )
        # Both BLOCKING and DEBT render message as Evidence and action as
        # Required.
        assert "Evidence: " in rendered, (
            "DEBT finding must render its message under the Evidence label"
        )
        assert "Required: " in rendered, (
            "DEBT finding must render its action under the Required label"
        )
        # The removed FOLLOW-UP severity and the legacy four-class headings
        # must not appear — the taxonomy is the two severities blocking/debt
        # over six categories.
        for forbidden in ("FOLLOW-UP", "### NEEDS-ANSWER", "### NOTE"):
            assert forbidden not in rendered, (
                f"render must not emit {forbidden!r} — it is not part of the "
                f"two-severity taxonomy from REVIEW.template.md"
            )
        # The legacy table format must NOT appear — confirms the
        # template-driven render replaces the f-string-table render.
        assert "| Severity |" not in rendered, (
            "legacy findings table must not appear in the rendered markdown"
        )

    def test_render_emits_census_marker_for_every_empty_severity(
        self, tmp_path: pathlib.Path
    ) -> None:
        # A fully-clean review (no findings) leaves both severity buckets
        # empty, so render reports each uniformly as its `<SEVERITY>: none`
        # census marker — privileging no severity. The default fixture
        # carries a debt finding, so the none-debt.md path is exercised here.
        clean_payload = json.dumps(make_review_result_dict(findings=[]))
        arbiter = run_script(VALIDATE_REVIEW_RESULT_SCRIPT, stdin=clean_payload)
        assert arbiter.returncode == 0, arbiter.stderr

        render = run_script(RENDER_REVIEW_SCRIPT, stdin=clean_payload)
        assert render.returncode == 0, render.stderr
        rendered = render.stdout
        for marker in ("BLOCKING: none", "DEBT: none"):
            assert marker in rendered, (
                f"empty severity bucket must render its census marker {marker!r}"
            )
        assert "FOLLOW-UP" not in rendered, (
            "FOLLOW-UP is not part of the two-severity taxonomy"
        )


def _set_origin_head(repo: pathlib.Path, branch: str) -> None:
    """Manually set ``refs/remotes/origin/HEAD`` without needing a real remote.

    The synthetic repo has no remote; ``git symbolic-ref`` lets us point
    ``refs/remotes/origin/HEAD`` directly at a local branch so
    ``compute_diff``'s strict origin-HEAD derivation has something to find.
    """
    _run_git(
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        f"refs/remotes/origin/{branch}",
        cwd=repo,
    )
    # The symbolic ref above only exists if the target ref exists too.
    # Mirror the local branch's tip into the remote-tracking namespace.
    rev = _run_git("rev-parse", branch, cwd=repo).stdout.strip()
    _run_git("update-ref", f"refs/remotes/origin/{branch}", rev, cwd=repo)


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists(),
    reason="compute_diff.py is not yet present.",
)
class TestComputeDiffBaseRefDerivation:
    """compute_diff.py resolves base_ref from env -> git, in that order."""

    def _setup_repo(self, tmp_path: pathlib.Path) -> tuple[pathlib.Path, str]:
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = _init_repo_with_branch(repo)
        return repo, base_ref

    def _run_compute_diff(
        self, repo: pathlib.Path, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return run_compute_diff_in_process(repo=repo, env=env)

    def test_env_base_ref_works(self, tmp_path: pathlib.Path) -> None:
        repo, base_ref = self._setup_repo(tmp_path)
        env = _make_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        result = self._run_compute_diff(repo, env)
        assert result.returncode == 0, result.stderr
        assert "README.md" in result.stdout

    def test_includes_committed_staged_unstaged_and_untracked_diffs(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref = self._setup_repo(tmp_path)
        env = _make_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref

        (repo / "STAGED.md").write_text("staged\n", encoding="utf-8")
        _run_git("add", "STAGED.md", cwd=repo)
        (repo / "README.md").write_text("hello\nworld\nunstaged\n", encoding="utf-8")
        (repo / "UNTRACKED.md").write_text("untracked\n", encoding="utf-8")

        result = self._run_compute_diff(repo, env)
        assert result.returncode == 0, result.stderr
        assert "### Committed diff" in result.stdout
        assert "### Staged diff" in result.stdout
        assert "### Unstaged diff" in result.stdout
        assert "### Untracked files" in result.stdout
        assert "world" in result.stdout
        assert "STAGED.md" in result.stdout
        assert "unstaged" in result.stdout
        assert "UNTRACKED.md" in result.stdout
        assert "untracked" in result.stdout

    def test_git_origin_head_works_without_changes_or_env(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref = self._setup_repo(tmp_path)
        _set_origin_head(repo, base_ref)
        env = _make_env(cwd=repo)
        env.pop("SPX_VERIFY_BASE_REF", None)
        result = self._run_compute_diff(repo, env)
        assert result.returncode == 0, result.stderr
        assert "README.md" in result.stdout

    def test_aborts_when_no_source_yields_base_ref(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, _base_ref = self._setup_repo(tmp_path)
        env = _make_env(cwd=repo)
        env.pop("SPX_VERIFY_BASE_REF", None)
        # No env; no origin/HEAD symbolic ref.
        result = self._run_compute_diff(repo, env)
        assert result.returncode != 0
        # The error must name every source so the operator can pick one.
        for token in ("SPX_VERIFY_BASE_REF", "origin/HEAD"):
            assert token in result.stderr, (
                f"stderr should name {token!r}; got: {result.stderr!r}"
            )


def _add_secondary_branch(repo: pathlib.Path, branch: str, filename: str) -> None:
    """Create ``branch`` off ``main`` carrying a single distinct file commit.

    The resulting branch differs from ``feature/x`` so a diff against ``main``
    over the secondary branch surfaces the unique filename rather than the
    feature/x payload — that is the signal the head_ref tests assert on.
    Returns to ``feature/x`` so subsequent commands run from the same HEAD
    the other tests assume.
    """
    _run_git("switch", "main", cwd=repo)
    _run_git("switch", "-c", branch, cwd=repo)
    (repo / filename).write_text("secondary branch content\n", encoding="utf-8")
    _run_git("add", filename, cwd=repo)
    _run_git("commit", "-q", "-m", f"add {filename} on {branch}", cwd=repo)
    _run_git("switch", "feature/x", cwd=repo)


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists(),
    reason="compute_diff.py is not yet present.",
)
class TestComputeDiffHeadRefDerivation:
    """compute_diff.py resolves head_ref from env -> literal HEAD.

    Asserts the parallel precedence chain to TestComputeDiffBaseRefDerivation
    so the spec's new head_ref scenarios carry executed evidence. A secondary
    branch with its own distinct filename gives each scenario a falsifiable
    signal: when head_ref selects the secondary branch, the diff surfaces
    that file; when head_ref defaults to literal HEAD (feature/x), it does
    not.
    """

    def _setup_repo_with_secondary(
        self, tmp_path: pathlib.Path
    ) -> tuple[pathlib.Path, str, str]:
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = _init_repo_with_branch(repo)
        secondary = "feature/y"
        _add_secondary_branch(repo, secondary, "SECONDARY.md")
        return repo, base_ref, secondary

    def _run_compute_diff(
        self, repo: pathlib.Path, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return run_compute_diff_in_process(repo=repo, env=env)

    def test_env_head_ref_selects_alternate_head(self, tmp_path: pathlib.Path) -> None:
        repo, base_ref, secondary = self._setup_repo_with_secondary(tmp_path)
        env = _make_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env["SPX_VERIFY_HEAD_REF"] = secondary
        result = self._run_compute_diff(repo, env)
        assert result.returncode == 0, result.stderr
        # head_ref pointed at the secondary branch — its file appears, not
        # feature/x's README change. This is what distinguishes head_ref
        # selection from the default-HEAD behaviour.
        assert "SECONDARY.md" in result.stdout
        assert "world" not in result.stdout

    def test_head_ref_defaults_to_literal_head_when_no_source(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, base_ref, _secondary = self._setup_repo_with_secondary(tmp_path)
        env = _make_env(cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env.pop("SPX_VERIFY_HEAD_REF", None)
        # No SPX_VERIFY_HEAD_REF; HEAD is feature/x, so the diff must surface
        # feature/x's payload, not secondary's SECONDARY.md.
        result = self._run_compute_diff(repo, env)
        assert result.returncode == 0, result.stderr
        assert "world" in result.stdout
        assert "SECONDARY.md" not in result.stdout


@pytest.mark.skipif(
    not COMPUTE_DIFF_SCRIPT.exists(),
    reason="compute_diff.py is not yet present.",
)
class TestComputeDiffStaleLocalBase:
    """A git-derived base scopes against origin/<base>, not a stale local ref.

    Reproduces the multi-worktree staleness bug: the feature branch holds a
    commit already merged into ``origin/main`` while the local ``main`` ref lags
    behind it. With no ``SPX_VERIFY_BASE_REF``, ``compute_diff`` auto-derives
    the base from ``origin/HEAD``; the derived base must resolve to the
    remote-tracking ref ``origin/main`` so the already-merged commit stays out
    of the diff. Diffing against the bare local ``main`` would re-include it.
    """

    def test_git_derived_base_excludes_already_merged_commit(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        stale = build_stale_local_base_repo(repo)
        env = _make_env(cwd=stale.repo)
        env.pop("SPX_VERIFY_BASE_REF", None)

        result = run_compute_diff_in_process(repo=stale.repo, env=env)
        assert result.returncode == 0, result.stderr
        # The feature change is in scope; the already-merged commit is not —
        # auto-derivation must scope against origin/<base>, not the stale local
        # ref.
        assert stale.feature_file in result.stdout
        assert stale.merged_file not in result.stdout
