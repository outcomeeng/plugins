"""End-to-end scenario tests for the reviewing-changes script chain.

Covers the Scenario clauses in ``../reviewing-changes.md`` that govern
how ``compute_diff.py`` resolves ``base_ref`` and how the end-to-end
chain persists outputs:

1. ``changes.json`` with ``base_ref`` set → chain reads it and uses
   that ref end-to-end (review-result.json + review.md both persisted).
2. No ``changes.json`` + ``SPX_VERIFY_BASE_REF`` env set → env value is
   used as ``base_ref``.
3. No ``changes.json`` + no env + ``refs/remotes/origin/HEAD`` resolves
   → derived from that symbolic ref, stripped of the prefix.
4. Env set + file set → env wins (precedence).
5. No source available → non-zero exit; stderr names all three sources
   so the operator can identify which to populate.

The tests are ``l2`` because they spawn ``git`` and multiple Python
subprocesses against a synthetic git repository seeded under a
``tmp_path``-rooted thread store; they do not depend on remote services
or credentials.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

from outcomeeng_testing.harnesses.changeset_scope import build_stale_local_base_repo
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
        "SPX_VERIFY_BACKEND": "local",
        "SPX_VERIFY_LOCAL_ROOT": str(store_root),
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
    """End-to-end chain: changes.json → diff → review-result → arbiter → render."""

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

        # 4. Seed changes.json into the thread store. The verification skill reads
        #    only `base_ref`; the override file is the platform-neutral
        #    file the consumer may author when overriding auto-derivation.
        changes_payload = json.dumps({"base_ref": base_ref})
        result = run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "changes.json",
            stdin=changes_payload,
            env=env,
        )
        assert result.returncode == 0, result.stderr

        # 5. compute_diff.py reads changes.json (via the thread store), runs
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
        render_result = run_script(RENDER_REVIEW_SCRIPT, "--slug", slug, env=env)
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
        persisted = json.loads(read_rr.stdout)
        assert "findings" in persisted
        assert "decision" not in persisted

        read_md = run_script(
            READ_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "review.md",
            env=env,
        )
        assert read_md.returncode == 0
        rendered = read_md.stdout
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
        store_root = tmp_path / "store"
        store_root.mkdir()
        env = _make_env_for_temp_store(store_root, cwd=tmp_path)
        slug = load_branch_slug_module().branch_slug("feature/clean")

        clean_payload = json.dumps(make_review_result_dict(findings=[]))
        arbiter = run_script(
            VALIDATE_REVIEW_RESULT_SCRIPT, stdin=clean_payload, env=env
        )
        assert arbiter.returncode == 0, arbiter.stderr
        write_rr = run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "review-result.json",
            stdin=clean_payload,
            env=env,
        )
        assert write_rr.returncode == 0, write_rr.stderr

        render = run_script(RENDER_REVIEW_SCRIPT, "--slug", slug, env=env)
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
    """compute_diff.py resolves base_ref from env → file → git, in that order."""

    def _setup_repo_and_store(
        self, tmp_path: pathlib.Path
    ) -> tuple[pathlib.Path, pathlib.Path, str]:
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = _init_repo_with_branch(repo)
        store_root = tmp_path / "store"
        store_root.mkdir()
        return repo, store_root, base_ref

    def _slug_for(self, branch: str) -> str:
        return load_branch_slug_module().branch_slug(branch)

    def _run_compute_diff(
        self, repo: pathlib.Path, env: dict[str, str], slug: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 — script path is from the harness
            [sys.executable, str(COMPUTE_DIFF_SCRIPT), "--slug", slug],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_env_base_ref_works_without_changes_json(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, store_root, base_ref = self._setup_repo_and_store(tmp_path)
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        result = self._run_compute_diff(repo, env, slug)
        assert result.returncode == 0, result.stderr
        assert "README.md" in result.stdout

    def test_git_origin_head_works_without_changes_or_env(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, store_root, base_ref = self._setup_repo_and_store(tmp_path)
        _set_origin_head(repo, base_ref)
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        env.pop("SPX_VERIFY_BASE_REF", None)
        result = self._run_compute_diff(repo, env, slug)
        assert result.returncode == 0, result.stderr
        assert "README.md" in result.stdout

    def test_env_overrides_changes_json_when_both_set(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, store_root, base_ref = self._setup_repo_and_store(tmp_path)
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        # Seed changes.json with a bogus ref. If the file wins, git diff
        # will fail; if env wins, the run succeeds.
        run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "changes.json",
            stdin=json.dumps({"base_ref": "ref-that-does-not-exist"}),
            env=env,
        )
        env["SPX_VERIFY_BASE_REF"] = base_ref
        result = self._run_compute_diff(repo, env, slug)
        assert result.returncode == 0, result.stderr
        assert "README.md" in result.stdout

    def test_aborts_when_no_source_yields_base_ref(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, store_root, _base_ref = self._setup_repo_and_store(tmp_path)
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        env.pop("SPX_VERIFY_BASE_REF", None)
        # No changes.json seeded; no env; no origin/HEAD symbolic ref.
        result = self._run_compute_diff(repo, env, slug)
        assert result.returncode != 0
        # The error must name every source so the operator can pick one.
        for token in ("SPX_VERIFY_BASE_REF", "changes.json", "origin/HEAD"):
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
    """compute_diff.py resolves head_ref from env → file → literal HEAD.

    Asserts the parallel precedence chain to TestComputeDiffBaseRefDerivation
    so the spec's new head_ref scenarios carry executed evidence. A secondary
    branch with its own distinct filename gives each scenario a falsifiable
    signal: when head_ref selects the secondary branch, the diff surfaces
    that file; when head_ref defaults to literal HEAD (feature/x), it does
    not.
    """

    def _setup_repo_with_secondary(
        self, tmp_path: pathlib.Path
    ) -> tuple[pathlib.Path, pathlib.Path, str, str]:
        repo = tmp_path / "repo"
        repo.mkdir()
        base_ref = _init_repo_with_branch(repo)
        secondary = "feature/y"
        _add_secondary_branch(repo, secondary, "SECONDARY.md")
        store_root = tmp_path / "store"
        store_root.mkdir()
        return repo, store_root, base_ref, secondary

    def _slug_for(self, branch: str) -> str:
        return load_branch_slug_module().branch_slug(branch)

    def _run_compute_diff(
        self, repo: pathlib.Path, env: dict[str, str], slug: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 — script path is from the harness
            [sys.executable, str(COMPUTE_DIFF_SCRIPT), "--slug", slug],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_env_head_ref_selects_alternate_head(self, tmp_path: pathlib.Path) -> None:
        repo, store_root, base_ref, secondary = self._setup_repo_with_secondary(
            tmp_path
        )
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env["SPX_VERIFY_HEAD_REF"] = secondary
        result = self._run_compute_diff(repo, env, slug)
        assert result.returncode == 0, result.stderr
        # head_ref pointed at the secondary branch — its file appears, not
        # feature/x's README change. This is what distinguishes head_ref
        # selection from the default-HEAD behaviour.
        assert "SECONDARY.md" in result.stdout
        assert "world" not in result.stdout

    def test_changes_json_head_ref_selects_alternate_head(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, store_root, base_ref, secondary = self._setup_repo_with_secondary(
            tmp_path
        )
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "changes.json",
            stdin=json.dumps({"base_ref": base_ref, "head_ref": secondary}),
            env=env,
        )
        result = self._run_compute_diff(repo, env, slug)
        assert result.returncode == 0, result.stderr
        assert "SECONDARY.md" in result.stdout
        assert "world" not in result.stdout

    def test_env_head_ref_overrides_changes_json_head_ref(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, store_root, base_ref, secondary = self._setup_repo_with_secondary(
            tmp_path
        )
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        # Seed changes.json with the secondary as head_ref; env points back
        # to feature/x. If env wins, the diff surfaces feature/x's payload;
        # if file wins, the diff surfaces SECONDARY.md.
        run_script(
            WRITE_RECORD_SCRIPT,
            "--slug",
            slug,
            "--name",
            "changes.json",
            stdin=json.dumps({"base_ref": base_ref, "head_ref": secondary}),
            env=env,
        )
        env["SPX_VERIFY_HEAD_REF"] = "feature/x"
        result = self._run_compute_diff(repo, env, slug)
        assert result.returncode == 0, result.stderr
        assert "world" in result.stdout
        assert "SECONDARY.md" not in result.stdout

    def test_head_ref_defaults_to_literal_head_when_no_source(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo, store_root, base_ref, _secondary = self._setup_repo_with_secondary(
            tmp_path
        )
        slug = self._slug_for("feature/x")
        env = _make_env_for_temp_store(store_root, cwd=repo)
        env["SPX_VERIFY_BASE_REF"] = base_ref
        env.pop("SPX_VERIFY_HEAD_REF", None)
        # No changes.json head_ref field; no SPX_VERIFY_HEAD_REF; HEAD is
        # feature/x, so the diff must surface feature/x's payload, not
        # secondary's SECONDARY.md.
        result = self._run_compute_diff(repo, env, slug)
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
    behind it. With no ``changes.json`` and no ``SPX_VERIFY_BASE_REF``,
    ``compute_diff`` auto-derives the base from ``origin/HEAD``; the derived base
    must resolve to the remote-tracking ref ``origin/main`` so the already-merged
    commit stays out of the diff. Diffing against the bare local ``main`` would
    re-include it.
    """

    def _slug_for(self, branch: str) -> str:
        return load_branch_slug_module().branch_slug(branch)

    def test_git_derived_base_excludes_already_merged_commit(
        self, tmp_path: pathlib.Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        stale = build_stale_local_base_repo(repo)
        store_root = tmp_path / "store"
        store_root.mkdir()
        env = _make_env_for_temp_store(store_root, cwd=stale.repo)
        env.pop("SPX_VERIFY_BASE_REF", None)
        slug = self._slug_for(stale.feature_branch)

        result = subprocess.run(  # noqa: S603 — script path is from the harness
            [sys.executable, str(COMPUTE_DIFF_SCRIPT), "--slug", slug],
            cwd=stale.repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        # The feature change is in scope; the already-merged commit is not —
        # auto-derivation must scope against origin/<base>, not the stale local
        # ref.
        assert stale.feature_file in result.stdout
        assert stale.merged_file not in result.stdout
