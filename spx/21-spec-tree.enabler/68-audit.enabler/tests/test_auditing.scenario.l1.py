"""Scenario tests for the ``audit_orchestrator`` helpers and CLI.

Covers the helpers the ``/audit`` skill and the ``audit-orchestrator``
agent delegate to so deterministic computations stay out of skill prose
and agent prompts:

- ``detect_base_ref`` / ``detect_current_branch`` — base-ref derivation
  and a stable label refusing detached HEAD.
- ``expand_diff_range`` / ``branch_scope`` / ``modified_since`` /
  ``uncommitted_scope`` — git plumbing wrappers.
- ``is_sha_reachable`` — prior-run-SHA reachability guard.
- ``branch_slug`` — stable branch label derivation.
- ``compute_verdict_diff`` — journal run-set projection of resolved and
  reopened findings.

``compute_scope_hash`` is covered by ``test_auditing.property.l1.py``.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest
from outcomeeng_testing.harnesses.audit_orchestrator import (
    AUDIT_ORCHESTRATOR_MODULE_PATH,
    load_audit_orchestrator_module,
)
from outcomeeng_testing.harnesses.verdict_toolchain import load_verdict_module

DEFAULT_BASE_REF = "main"


def _git(repo: pathlib.Path, *args: str) -> str:
    """Run a git command in ``repo`` and return its stdout (text mode)."""
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell, repo is tmp_path
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _init_repo(repo: pathlib.Path, default_branch: str = "main") -> None:
    """Initialize a git repo in ``repo`` with one commit on ``default_branch``."""
    _git(repo, "init", "--initial-branch", default_branch, "--quiet")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / "README").write_text("seed\n")
    _git(repo, "add", "README")
    _git(repo, "commit", "-m", "seed", "--quiet")


def _commit_files(repo: pathlib.Path, files: dict[str, str], message: str) -> str:
    """Write ``files`` (path → content) into ``repo``, commit, return SHA."""
    for relpath, content in files.items():
        target = repo / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        _git(repo, "add", relpath)
    _git(repo, "commit", "-m", message, "--quiet")
    return _git(repo, "rev-parse", "HEAD").strip()


def _snapshot_origin(repo: pathlib.Path, base_ref: str) -> str:
    """Write ``.git/refs/remotes/origin/<base_ref>`` pointing at current HEAD."""
    head_sha = _git(repo, "rev-parse", "HEAD").strip()
    target = repo / ".git" / "refs" / "remotes" / "origin" / base_ref
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{head_sha}\n", encoding="utf-8")
    return head_sha


@pytest.fixture
def repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """tmp_path-rooted git repo on branch ``main`` with one commit."""
    _init_repo(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# detect_base_ref
# ---------------------------------------------------------------------------


def test_detect_base_ref_strips_origin_head_prefix(repo: pathlib.Path) -> None:
    """When ``refs/remotes/origin/HEAD`` exists, return the bare branch name."""
    module = load_audit_orchestrator_module()
    (repo / ".git" / "refs" / "remotes" / "origin").mkdir(parents=True)
    (repo / ".git" / "refs" / "remotes" / "origin" / "main").write_text(
        _git(repo, "rev-parse", "HEAD")
    )
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    base = module.detect_base_ref(repo)

    assert base == "main"


def test_detect_base_ref_defaults_to_main_when_origin_absent(
    repo: pathlib.Path,
) -> None:
    """Repos without an ``origin`` remote default to ``main``."""
    module = load_audit_orchestrator_module()

    base = module.detect_base_ref(repo)

    assert base == DEFAULT_BASE_REF


# ---------------------------------------------------------------------------
# detect_current_branch
# ---------------------------------------------------------------------------


def test_detect_current_branch_returns_named_branch(repo: pathlib.Path) -> None:
    """On a named branch, return the bare branch name."""
    module = load_audit_orchestrator_module()
    _git(repo, "switch", "-c", "feature/audit-helpers", "--quiet")

    branch = module.detect_current_branch(repo)

    assert branch == "feature/audit-helpers"


def test_detect_current_branch_raises_on_detached_head(repo: pathlib.Path) -> None:
    """Detached HEAD raises ``DetachedHeadError`` so state naming refuses HEAD."""
    module = load_audit_orchestrator_module()
    head_sha = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "checkout", "--detach", head_sha, "--quiet")

    with pytest.raises(module.DetachedHeadError):
        module.detect_current_branch(repo)


# ---------------------------------------------------------------------------
# branch_slug
# ---------------------------------------------------------------------------


def test_branch_slug_replaces_slashes_with_double_underscore(
    tmp_path: pathlib.Path,
) -> None:
    """``feature/foo`` slugs to ``feature__foo`` when no collision exists."""
    module = load_audit_orchestrator_module()

    slug = module.branch_slug("feature/foo", tmp_path)

    assert slug == "feature__foo"


def test_branch_slug_collision_appends_hash_suffix(tmp_path: pathlib.Path) -> None:
    """A branch literally named like another branch's slug gets a distinct slug."""
    module = load_audit_orchestrator_module()
    (tmp_path / "feature__foo.md").write_text(
        "---\nbranch: feature/foo\n---\n\n# state\n",
        encoding="utf-8",
    )

    slug = module.branch_slug("feature__foo", tmp_path)

    assert slug.startswith("feature__foo--")
    assert slug != "feature__foo"


# ---------------------------------------------------------------------------
# expand_diff_range
# ---------------------------------------------------------------------------


def test_expand_diff_range_returns_files_changed_between_commits(
    repo: pathlib.Path,
) -> None:
    """``HEAD~1..HEAD`` returns files modified by the most recent commit."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"src/a.ts": "first\n", "src/b.py": "first\n"}, "first")
    _commit_files(repo, {"src/a.ts": "second\n"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", repo=repo)

    assert files == ["src/a.ts"]


def test_expand_diff_range_filters_by_single_pattern(repo: pathlib.Path) -> None:
    """A single ``*.ts`` pattern excludes ``.py`` and ``.tsx`` files."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"keep.ts": "x", "skip.py": "x", "skip.tsx": "x"}, "first")
    _commit_files(repo, {"keep.ts": "y", "skip.py": "y", "skip.tsx": "y"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", patterns=["*.ts"], repo=repo)

    assert files == ["keep.ts"]


def test_expand_diff_range_combines_multiple_patterns(repo: pathlib.Path) -> None:
    """Multiple patterns are unioned by ``git diff -- <pat1> <pat2>``."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"a.ts": "x", "b.tsx": "x", "c.py": "x"}, "first")
    _commit_files(repo, {"a.ts": "y", "b.tsx": "y", "c.py": "y"}, "second")

    files = module.expand_diff_range(
        "HEAD~1..HEAD", patterns=["*.ts", "*.tsx"], repo=repo
    )

    assert sorted(files) == ["a.ts", "b.tsx"]


def test_expand_diff_range_returns_empty_when_no_files_match(
    repo: pathlib.Path,
) -> None:
    """A pattern that matches nothing in the diff yields an empty list."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"only.py": "x"}, "first")
    _commit_files(repo, {"only.py": "y"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", patterns=["*.ts"], repo=repo)

    assert files == []


def test_expand_diff_range_with_no_patterns_returns_all_files(
    repo: pathlib.Path,
) -> None:
    """``patterns=None`` runs ``git diff --name-only <range>`` without filter."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"a.ts": "x", "b.py": "x", "c.tsx": "x"}, "first")
    _commit_files(repo, {"a.ts": "y", "b.py": "y", "c.tsx": "y"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", repo=repo)

    assert sorted(files) == ["a.ts", "b.py", "c.tsx"]


def test_expand_diff_range_default_head_returns_uncommitted_changes(
    repo: pathlib.Path,
) -> None:
    """Range ``HEAD`` (no commits ahead) reports staged + unstaged changes."""
    module = load_audit_orchestrator_module()
    (repo / "edited.ts").write_text("new content\n", encoding="utf-8")
    _git(repo, "add", "edited.ts")

    files = module.expand_diff_range("HEAD", patterns=["*.ts"], repo=repo)

    assert files == ["edited.ts"]


# ---------------------------------------------------------------------------
# branch_scope
# ---------------------------------------------------------------------------


def test_branch_scope_returns_files_added_by_branch(repo: pathlib.Path) -> None:
    """Files committed after origin/main snapshot are reported."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"old.ts": "x", "old.py": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/audit-scope", "--quiet")
    _commit_files(repo, {"new.ts": "y", "new.tsx": "y"}, "branch work")

    files = module.branch_scope("main", repo=repo)

    assert sorted(files) == ["new.ts", "new.tsx"]


def test_branch_scope_filters_by_patterns(repo: pathlib.Path) -> None:
    """Patterns restrict the result to matching extensions."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/mixed", "--quiet")
    _commit_files(
        repo, {"keep.ts": "y", "keep.tsx": "y", "skip.py": "y"}, "branch work"
    )

    files = module.branch_scope("main", patterns=["*.ts", "*.tsx"], repo=repo)

    assert sorted(files) == ["keep.ts", "keep.tsx"]


def test_branch_scope_is_empty_when_no_commits_ahead(
    repo: pathlib.Path,
) -> None:
    """A branch with zero commits past origin/main yields an empty scope."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/no-work", "--quiet")

    files = module.branch_scope("main", repo=repo)

    assert files == []


def test_branch_scope_uses_origin_prefix_for_arbitrary_base(
    repo: pathlib.Path,
) -> None:
    """Any base ref name is composed as ``origin/<base_ref>``."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "base")
    _snapshot_origin(repo, "develop")
    _git(repo, "switch", "-c", "feature/branched-from-develop", "--quiet")
    _commit_files(repo, {"feature.ts": "y"}, "branch work")

    files = module.branch_scope("develop", repo=repo)

    assert files == ["feature.ts"]


def test_branch_scope_excludes_files_committed_on_base_after_branch_off(
    repo: pathlib.Path,
) -> None:
    """Files added to base after the branch-off are not part of the scope."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/parallel", "--quiet")
    _commit_files(repo, {"branch_only.ts": "y"}, "branch work")
    _git(repo, "switch", "main", "--quiet")
    _commit_files(repo, {"base_advanced.ts": "z"}, "base advanced")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "feature/parallel", "--quiet")

    files = module.branch_scope("main", repo=repo)

    assert files == ["branch_only.ts"]


# ---------------------------------------------------------------------------
# modified_since
# ---------------------------------------------------------------------------


def test_modified_since_returns_files_added_after_prior_sha(
    repo: pathlib.Path,
) -> None:
    """Files added in commits past ``prior_sha`` are reported."""
    module = load_audit_orchestrator_module()
    prior_sha = _commit_files(repo, {"old.ts": "x"}, "old work")
    _commit_files(repo, {"new.ts": "y", "another.tsx": "y"}, "new work")

    files = module.modified_since(prior_sha, repo=repo)

    assert sorted(files) == ["another.tsx", "new.ts"]


def test_modified_since_filters_by_patterns(repo: pathlib.Path) -> None:
    """Patterns restrict the result to matching extensions."""
    module = load_audit_orchestrator_module()
    prior_sha = _commit_files(repo, {"seed.ts": "x"}, "seed")
    _commit_files(repo, {"keep.ts": "y", "keep.tsx": "y", "skip.py": "y"}, "mixed work")

    files = module.modified_since(prior_sha, patterns=["*.ts", "*.tsx"], repo=repo)

    assert sorted(files) == ["keep.ts", "keep.tsx"]


def test_modified_since_is_empty_when_no_commits_past_sha(
    repo: pathlib.Path,
) -> None:
    """A repo at the same SHA as ``prior_sha`` yields an empty result."""
    module = load_audit_orchestrator_module()
    prior_sha = _commit_files(repo, {"seed.ts": "x"}, "seed")

    files = module.modified_since(prior_sha, repo=repo)

    assert files == []


def test_modified_since_includes_files_modified_by_later_commits(
    repo: pathlib.Path,
) -> None:
    """A file edited in a commit past ``prior_sha`` appears in the result."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"persistent.ts": "v1"}, "v1")
    prior_sha = _git(repo, "rev-parse", "HEAD").strip()
    _commit_files(repo, {"persistent.ts": "v2"}, "v2")

    files = module.modified_since(prior_sha, repo=repo)

    assert files == ["persistent.ts"]


def test_modified_since_uses_two_dot_diff_against_head(
    repo: pathlib.Path,
) -> None:
    """``prior_sha..HEAD`` reports tree-diff, distinct from three-dot.

    A file present at ``prior_sha`` but absent from HEAD must appear so
    the auditor knows the file no longer exists in the working tree.
    """
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "seed")
    _git(repo, "switch", "-c", "diverge", "--quiet")
    _commit_files(repo, {"diverge_only.ts": "y"}, "diverge commit")
    prior_sha = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "switch", "main", "--quiet")
    _commit_files(repo, {"main_only.ts": "z"}, "main commit")

    files = module.modified_since(prior_sha, repo=repo)

    assert sorted(files) == ["diverge_only.ts", "main_only.ts"]


# ---------------------------------------------------------------------------
# is_sha_reachable
# ---------------------------------------------------------------------------


NONEXISTENT_SHA = "0" * 40  # 40 hex zeros — syntactically a SHA, never used
SHA_ABBREV_LENGTH = 7  # git's default abbreviated SHA length


def test_is_sha_reachable_returns_true_for_known_commit(
    repo: pathlib.Path,
) -> None:
    """A SHA from an existing commit on the current branch is reachable."""
    module = load_audit_orchestrator_module()
    sha = _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable(sha, repo=repo) is True


def test_is_sha_reachable_accepts_abbreviated_sha(repo: pathlib.Path) -> None:
    """Git accepts unique SHA prefixes; the helper does not require full length."""
    module = load_audit_orchestrator_module()
    sha = _commit_files(repo, {"seed.ts": "x"}, "seed")
    abbreviated = sha[:SHA_ABBREV_LENGTH]

    assert module.is_sha_reachable(abbreviated, repo=repo) is True


def test_is_sha_reachable_returns_false_for_unknown_sha(
    repo: pathlib.Path,
) -> None:
    """A syntactically valid SHA that no commit produced is unreachable.

    Models the failure mode where a prior run SHA was force-pushed away
    or never fetched into the local clone.
    """
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable(NONEXISTENT_SHA, repo=repo) is False


def test_is_sha_reachable_returns_false_for_malformed_input(
    repo: pathlib.Path,
) -> None:
    """A non-SHA string (e.g., a typo'd value) is treated as unreachable."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable("not-a-sha", repo=repo) is False


def test_is_sha_reachable_returns_false_for_tree_object(
    repo: pathlib.Path,
) -> None:
    """A SHA that resolves to a non-commit object (a tree) is unreachable."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"seed.ts": "x"}, "seed")
    tree_sha = _git(repo, "rev-parse", "HEAD^{tree}").strip()

    assert module.is_sha_reachable(tree_sha, repo=repo) is False


# ---------------------------------------------------------------------------
# uncommitted_scope
# ---------------------------------------------------------------------------


def test_uncommitted_scope_includes_untracked_files(repo: pathlib.Path) -> None:
    """A new file that has not been ``git add``-ed is still in scope."""
    module = load_audit_orchestrator_module()
    (repo / "fresh.ts").write_text("brand new", encoding="utf-8")

    files = module.uncommitted_scope(patterns=["*.ts"], repo=repo)

    assert files == ["fresh.ts"]


def test_uncommitted_scope_includes_modified_staged_and_untracked(
    repo: pathlib.Path,
) -> None:
    """All three working-tree categories appear in the same scope."""
    module = load_audit_orchestrator_module()
    _commit_files(repo, {"committed.ts": "v1\n"}, "seed")
    (repo / "committed.ts").write_text("v2\n", encoding="utf-8")
    (repo / "staged.ts").write_text("staged content\n", encoding="utf-8")
    _git(repo, "add", "staged.ts")
    (repo / "untracked.ts").write_text("untracked content\n", encoding="utf-8")

    files = module.uncommitted_scope(repo=repo)

    assert sorted(files) == ["committed.ts", "staged.ts", "untracked.ts"]


def test_uncommitted_scope_respects_gitignore(repo: pathlib.Path) -> None:
    """Files matched by ``.gitignore`` are excluded from the scope."""
    module = load_audit_orchestrator_module()
    (repo / ".gitignore").write_text("ignored.ts\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-m", "ignore", "--quiet")
    (repo / "ignored.ts").write_text("should not appear", encoding="utf-8")
    (repo / "kept.ts").write_text("should appear", encoding="utf-8")

    files = module.uncommitted_scope(patterns=["*.ts"], repo=repo)

    assert files == ["kept.ts"]


def test_uncommitted_scope_is_empty_when_working_tree_clean(
    repo: pathlib.Path,
) -> None:
    """A clean working tree (no diff, no untracked files) yields ``[]``."""
    module = load_audit_orchestrator_module()

    files = module.uncommitted_scope(repo=repo)

    assert files == []


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------


def _run_cli(
    *args: str, stdin: str = "", cwd: pathlib.Path | None = None
) -> tuple[int, str, str]:
    """Invoke the script's CLI as a subprocess and return (rc, stdout, stderr)."""
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell
        [sys.executable, str(AUDIT_ORCHESTRATOR_MODULE_PATH), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_base_ref_prints_default(repo: pathlib.Path) -> None:
    """``base-ref`` prints the default ref when ``origin/HEAD`` is absent."""
    rc, out, _ = _run_cli("base-ref", "--repo", str(repo))

    assert rc == 0
    assert out.strip() == DEFAULT_BASE_REF


def test_cli_current_branch_prints_named_branch(repo: pathlib.Path) -> None:
    """``current-branch`` prints the bare branch name."""
    _git(repo, "switch", "-c", "feature/cli-current", "--quiet")

    rc, out, _ = _run_cli("current-branch", "--repo", str(repo))

    assert rc == 0
    assert out.strip() == "feature/cli-current"


def test_cli_current_branch_exits_2_on_detached_head(repo: pathlib.Path) -> None:
    """``current-branch`` exits with code 2 on detached HEAD."""
    head_sha = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "checkout", "--detach", head_sha, "--quiet")

    rc, _, _ = _run_cli("current-branch", "--repo", str(repo))

    assert rc == 2


def test_cli_branch_slug_prints_slug(tmp_path: pathlib.Path) -> None:
    """``branch-slug`` derives the slug for the named branch."""
    rc, out, _ = _run_cli("branch-slug", "--branch", "feature/foo")

    assert rc == 0
    assert out.strip() == "feature__foo"


def test_cli_branch_slug_accepts_no_state_dir() -> None:
    """``branch-slug`` can derive a slug without an explicit state directory."""
    rc, out, _ = _run_cli("branch-slug", "--branch", "feature/foo")

    assert rc == 0
    assert out.strip() == "feature__foo"


def test_cli_remote_tracking_ref_prints_origin_ref() -> None:
    """``remote-tracking-ref`` composes the remote-tracking base ref."""
    rc, out, _ = _run_cli("remote-tracking-ref", "--base", "main")

    assert rc == 0
    assert out.strip() == "origin/main"


def test_cli_scope_hash_hashes_listed_files(repo: pathlib.Path) -> None:
    """``scope-hash`` reads paths from stdin, hashes their contents, prints hex."""
    (repo / "a.py").write_text("x", encoding="utf-8")
    (repo / "b.py").write_text("y", encoding="utf-8")

    rc, out, _ = _run_cli("scope-hash", "--repo", str(repo), stdin="a.py\nb.py\n")

    assert rc == 0
    hash_value = out.strip()
    assert len(hash_value) == 12
    assert all(c in "0123456789abcdef" for c in hash_value)


def test_cli_config_digest_hashes_stdin_payload() -> None:
    """``config-digest`` prints a stable SHA-256 digest for config payloads."""
    payload_a = "validation=just check\nlanguage=python\n"
    payload_b = "validation=just validation\nlanguage=python\n"

    rc_a1, out_a1, _ = _run_cli("config-digest", stdin=payload_a)
    rc_a2, out_a2, _ = _run_cli("config-digest", stdin=payload_a)
    rc_b, out_b, _ = _run_cli("config-digest", stdin=payload_b)

    assert rc_a1 == 0
    assert rc_a2 == 0
    assert rc_b == 0
    digest = out_a1.strip()
    assert digest == out_a2.strip()
    assert digest != out_b.strip()
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_cli_branch_scope_prints_changed_files(repo: pathlib.Path) -> None:
    """``branch-scope`` prints files changed against ``origin/<base>``."""
    _commit_files(repo, {"seed.ts": "x"}, "seed")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/cli-scope", "--quiet")
    _commit_files(repo, {"added.ts": "y"}, "add")

    rc, out, _ = _run_cli("branch-scope", "--base", "main", "--repo", str(repo))

    assert rc == 0
    assert out.splitlines() == ["added.ts"]


def test_cli_modified_since_prints_changed_files(repo: pathlib.Path) -> None:
    """``modified-since`` prints files changed since the given SHA."""
    sha = _commit_files(repo, {"v1.ts": "v1"}, "v1")
    _commit_files(repo, {"v2.ts": "v2"}, "v2")

    rc, out, _ = _run_cli("modified-since", "--since", sha, "--repo", str(repo))

    assert rc == 0
    assert out.splitlines() == ["v2.ts"]


def test_cli_commit_oid_prints_full_commit_oid(repo: pathlib.Path) -> None:
    """``commit-oid`` prints the full object ID for a commit ref."""
    sha = _commit_files(repo, {"seed.ts": "x"}, "seed")

    rc, out, _ = _run_cli("commit-oid", "--ref", "HEAD", "--repo", str(repo))

    assert rc == 0
    assert out.strip() == sha


def test_cli_sha_reachable_exit_codes(repo: pathlib.Path) -> None:
    """``sha-reachable`` exits 0 for known SHAs, 1 for unknown."""
    sha = _commit_files(repo, {"seed.ts": "x"}, "seed")

    rc_known, _, _ = _run_cli("sha-reachable", "--sha", sha, "--repo", str(repo))
    rc_unknown, _, _ = _run_cli(
        "sha-reachable", "--sha", NONEXISTENT_SHA, "--repo", str(repo)
    )

    assert rc_known == 0
    assert rc_unknown == 1


# ---------------------------------------------------------------------------
# Module surface
# ---------------------------------------------------------------------------


def test_helpers_under_audit_are_exposed_by_module() -> None:
    """The full helper symbol set must be importable from audit_orchestrator."""
    module = load_audit_orchestrator_module()

    for name in [
        "compute_scope_hash",
        "expand_diff_range",
        "branch_scope",
        "modified_since",
        "uncommitted_scope",
        "is_sha_reachable",
        "detect_base_ref",
        "detect_current_branch",
        "branch_slug",
        "DetachedHeadError",
        "build_parser",
        "main",
        "compute_verdict_diff",
    ]:
        assert hasattr(module, name), f"missing symbol: {name}"


# Verdict-diff tests — journal run-set projection of open, resolved, and
# reopened findings. Identity is (file, line, rule, message).
#
# Findings are constructed via the source-owned verdict.Finding dataclass and
# serialized through finding_to_json_dict; the wire-shape dict shape lives in
# verdict.py (one source for the schema), not in copied test literals.
# Cross-process determinism of the resolved/reopened ordering is covered by
# test_audit_orchestrator_cli.scenario.l1.py — it cannot be observed inside
# one Python process because hash randomization is fixed per-process.

_verdict_module = load_verdict_module()
_Finding = _verdict_module.Finding
_finding_to_json_dict = _verdict_module.finding_to_json_dict

VERDICT_FINDING_A_DICT = _finding_to_json_dict(
    _Finding(
        id="f-001",
        file="src/a.ts",
        line=1,
        rule="no-shared-bag",
        severity=_verdict_module.Severity.REJECT,
        message="shared bag in a",
    )
)
VERDICT_FINDING_B_DICT = _finding_to_json_dict(
    _Finding(
        id="f-002",
        file="src/b.ts",
        line=2,
        rule="no-shared-bag",
        severity=_verdict_module.Severity.REJECT,
        message="shared bag in b",
    )
)


def _verdict(open_findings: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "skill": "audit",
        "target": "scope",
        "overall": "REJECTED" if open_findings else "APPROVED",
        "rows": [{"name": "row-1", "status": "FAIL", "findings": open_findings}],
        "children": [],
        "metadata": {},
    }


def test_verdict_diff_first_run_returns_empty_arrays() -> None:
    module = load_audit_orchestrator_module()
    current = _verdict([VERDICT_FINDING_A_DICT, VERDICT_FINDING_B_DICT])
    enriched = module.compute_verdict_diff(prior=None, current=current)
    assert enriched["resolved"] == []
    assert enriched["reopened"] == []


def test_verdict_diff_resolves_findings_no_longer_open() -> None:
    module = load_audit_orchestrator_module()
    prior = _verdict([VERDICT_FINDING_A_DICT, VERDICT_FINDING_B_DICT])
    current = _verdict([VERDICT_FINDING_A_DICT])
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["resolved"] == [VERDICT_FINDING_B_DICT]
    assert enriched["reopened"] == []


def test_verdict_diff_carries_resolved_across_runs() -> None:
    module = load_audit_orchestrator_module()
    prior = {
        **_verdict([VERDICT_FINDING_A_DICT]),
        "resolved": [VERDICT_FINDING_B_DICT],
    }
    current = _verdict([VERDICT_FINDING_A_DICT])
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["resolved"] == [VERDICT_FINDING_B_DICT]


def test_verdict_diff_reopens_finding_in_prior_resolved() -> None:
    module = load_audit_orchestrator_module()
    prior = {
        **_verdict([VERDICT_FINDING_A_DICT]),
        "resolved": [VERDICT_FINDING_B_DICT],
    }
    current = _verdict([VERDICT_FINDING_A_DICT, VERDICT_FINDING_B_DICT])
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["reopened"] == [VERDICT_FINDING_B_DICT]
    assert enriched["resolved"] == []


def test_verdict_diff_walks_into_child_verdicts() -> None:
    module = load_audit_orchestrator_module()
    prior_with_child = {
        "schema_version": 1,
        "skill": "audit",
        "target": "scope",
        "overall": "REJECTED",
        "rows": [],
        "children": [_verdict([VERDICT_FINDING_A_DICT])],
        "metadata": {},
    }
    current_no_child_finding = {
        "schema_version": 1,
        "skill": "audit",
        "target": "scope",
        "overall": "APPROVED",
        "rows": [],
        "children": [_verdict([])],
        "metadata": {},
    }
    enriched = module.compute_verdict_diff(
        prior=prior_with_child, current=current_no_child_finding
    )
    assert enriched["resolved"] == [VERDICT_FINDING_A_DICT]


def test_verdict_diff_severity_change_is_same_finding() -> None:
    module = load_audit_orchestrator_module()
    prior_warning = {**VERDICT_FINDING_A_DICT, "severity": "WARNING"}
    prior = _verdict([prior_warning])
    current = _verdict([VERDICT_FINDING_A_DICT])  # same identity, REJECT severity
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["resolved"] == []
    assert enriched["reopened"] == []


def test_verdict_diff_id_change_is_same_finding() -> None:
    module = load_audit_orchestrator_module()
    prior_with_generated_id = {**VERDICT_FINDING_A_DICT, "id": "generated-previous"}
    current_with_new_id = {**VERDICT_FINDING_A_DICT, "id": "generated-current"}
    prior = _verdict([prior_with_generated_id])
    current = _verdict([current_with_new_id])
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["resolved"] == []
    assert enriched["reopened"] == []
