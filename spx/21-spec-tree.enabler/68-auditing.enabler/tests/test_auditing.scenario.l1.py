"""Scenario tests for the ``audit_orchestrator`` helpers and CLI.

Covers the helpers the ``/audit`` skill and the ``audit-orchestrator``
agent delegate to so deterministic computations stay out of skill prose
and agent prompts:

- ``detect_base_ref`` / ``detect_current_branch`` — base-ref derivation
  and a stable label refusing detached HEAD.
- ``expand_diff_range`` / ``branch_scope`` / ``modified_since`` /
  ``uncommitted_scope`` — git plumbing wrappers.
- ``is_sha_reachable`` — prior-run-SHA reachability guard.
- ``branch_slug`` — on-disk state-file slug with collision suffix.
- ``RunLock`` — TTL-bounded file lock for serialised audit runs.
- ``AuditState`` / ``Finding`` / ``ResolvedFinding`` / ``load_state`` /
  ``save_state`` / ``assign_finding_id`` — typed state shape and the
  monotonic finding-ID counter.
- ``find_resolved_by_identity`` / ``reopen_finding`` / ``resolve_finding``
  plus cell-escape round-trip — regression-detection helpers.
- ``state_transition`` plus the CLI subcommands — the composed
  carry-forward / reopen / resolve operation that the audit-orchestrator
  agent invokes once per audit run.

``compute_scope_hash`` is covered by ``test_auditing.property.l1.py``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest
from outcomeeng_testing.harnesses.verdict_toolchain import load_verdict_module

# parents[4] = repo root (this file lives 4 levels deep: spx/21-spec-tree.enabler/
# 68-auditing.enabler/tests/<file>).
# Tree surgery that changes the enabler's depth must update this index.
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[4]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "audit"
    / "scripts"
)
AUDIT_ORCHESTRATOR = SCRIPTS_DIR / "audit_orchestrator.py"

DEFAULT_BASE_REF = "main"
COLLISION_SUFFIX_LENGTH = 8
FRESH_LOCK_AGE = 60
STALE_LOCK_AGE = 1200
LOCK_AGE_HALF_TTL = 300

APPROVED_VERDICT = "APPROVED"
REJECTED_VERDICT = "REJECTED"

SAMPLE_BRANCH = "feature/audit-helpers"
SAMPLE_FIRST_RUN_SHA = "abc1234"
SAMPLE_FIRST_RUN_AT = "2026-05-11T15:30:43Z"
SAMPLE_LAST_RUN_SHA = "def5678"
SAMPLE_LAST_RUN_AT = "2026-05-11T15:35:12Z"


def _load_audit_orchestrator() -> ModuleType:
    """Load src/plugins/spec-tree/skills/audit/scripts/audit_orchestrator.py.

    The module ships inside the spec-tree plugin's scripts/ directory; importlib
    loads it by absolute path so this test does not depend on package layout.
    """
    spec = importlib.util.spec_from_file_location(
        "audit_orchestrator", AUDIT_ORCHESTRATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {AUDIT_ORCHESTRATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_orchestrator"] = module
    spec.loader.exec_module(module)
    return module


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
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()

    base = module.detect_base_ref(repo)

    assert base == DEFAULT_BASE_REF


# ---------------------------------------------------------------------------
# detect_current_branch
# ---------------------------------------------------------------------------


def test_detect_current_branch_returns_named_branch(repo: pathlib.Path) -> None:
    """On a named branch, return the bare branch name."""
    module = _load_audit_orchestrator()
    _git(repo, "switch", "-c", "feature/audit-helpers", "--quiet")

    branch = module.detect_current_branch(repo)

    assert branch == "feature/audit-helpers"


def test_detect_current_branch_raises_on_detached_head(repo: pathlib.Path) -> None:
    """Detached HEAD raises ``DetachedHeadError`` so state naming refuses HEAD."""
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()

    slug = module.branch_slug("feature/foo", tmp_path)

    assert slug == "feature__foo"


def test_branch_slug_returns_base_when_existing_state_matches_same_branch(
    tmp_path: pathlib.Path,
) -> None:
    """An existing state file for the same branch reuses the base slug."""
    module = _load_audit_orchestrator()
    (tmp_path / "feature__foo.md").write_text(
        "---\nbranch: feature/foo\n---\n\n# state\n"
    )

    slug = module.branch_slug("feature/foo", tmp_path)

    assert slug == "feature__foo"


def test_branch_slug_appends_sha_suffix_on_collision(tmp_path: pathlib.Path) -> None:
    """Two branches whose base slugs collide produce distinct slugs.

    ``feature/foo`` slugs to ``feature__foo`` and a literal branch named
    ``feature__foo`` slugs identically; the helper detects the existing
    state file's frontmatter ``branch`` differs from the new branch and
    appends an 8-character SHA-256 suffix.
    """
    module = _load_audit_orchestrator()
    (tmp_path / "feature__foo.md").write_text(
        "---\nbranch: feature/foo\n---\n\n# state\n"
    )

    slug = module.branch_slug("feature__foo", tmp_path)

    prefix, separator, suffix = slug.partition("--")
    assert prefix == "feature__foo"
    assert separator == "--"
    assert len(suffix) == COLLISION_SUFFIX_LENGTH
    assert all(c in "0123456789abcdef" for c in suffix)


def test_branch_slug_collision_suffix_is_deterministic(
    tmp_path: pathlib.Path,
) -> None:
    """Two calls with the same colliding branch produce the same suffix."""
    module = _load_audit_orchestrator()
    (tmp_path / "feature__foo.md").write_text(
        "---\nbranch: feature/foo\n---\n\n# state\n"
    )

    first = module.branch_slug("feature__foo", tmp_path)
    second = module.branch_slug("feature__foo", tmp_path)

    assert first == second


# ---------------------------------------------------------------------------
# RunLock
# ---------------------------------------------------------------------------


class _FakeClock:
    """Monotonic time source whose value the test controls."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.time = start

    def __call__(self) -> float:
        return self.time


def test_run_lock_acquires_when_path_absent(tmp_path: pathlib.Path) -> None:
    """A fresh lock acquisition writes the lock file."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "audits" / "python" / "main.md.lock"
    clock = _FakeClock()

    with module.RunLock(lock_path, now=clock):
        assert lock_path.exists()


def test_run_lock_releases_on_normal_exit(tmp_path: pathlib.Path) -> None:
    """The lock file is removed when the context exits normally."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()

    with module.RunLock(lock_path, now=clock):
        pass

    assert not lock_path.exists()


def test_run_lock_releases_on_exception(tmp_path: pathlib.Path) -> None:
    """The lock file is removed even when the context exits via exception.

    A crashed run that left a fresh-looking lock would block the next
    audit for a full TTL window.
    """
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()

    class _Boom(RuntimeError):
        pass

    with pytest.raises(_Boom), module.RunLock(lock_path, now=clock):
        raise _Boom("simulated audit failure")

    assert not lock_path.exists()


def test_run_lock_refuses_when_existing_lock_is_fresh(
    tmp_path: pathlib.Path,
) -> None:
    """A second acquisition during the TTL window raises ``RunLockError``."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()

    outer = module.RunLock(lock_path, now=clock)
    outer.__enter__()
    try:
        clock.time += FRESH_LOCK_AGE
        with pytest.raises(module.RunLockError), module.RunLock(lock_path, now=clock):
            pass
    finally:
        outer.__exit__(None, None, None)


def test_run_lock_overwrites_when_existing_lock_is_stale(
    tmp_path: pathlib.Path,
) -> None:
    """A lock older than ``max_age_seconds`` is overwritten."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()

    lock_path.write_text(str(clock.time))
    stale_time = clock.time - STALE_LOCK_AGE
    os.utime(lock_path, (stale_time, stale_time))

    with module.RunLock(lock_path, now=clock):
        assert lock_path.exists()


def test_run_lock_respects_custom_ttl(tmp_path: pathlib.Path) -> None:
    """A custom ``max_age_seconds`` overrides the default TTL."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()
    custom_ttl = 120

    lock_path.write_text(str(clock.time))
    aged_at = clock.time - LOCK_AGE_HALF_TTL
    os.utime(lock_path, (aged_at, aged_at))

    with module.RunLock(lock_path, max_age_seconds=custom_ttl, now=clock):
        assert lock_path.exists()


def test_run_lock_handles_disappearance_between_excl_create_and_stat(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``RunLock`` retries when the lock vanishes between ``O_EXCL`` and ``stat``.

    A concurrent holder's ``__exit__`` may unlink the lock between the
    failed atomic create and the follow-up ``stat`` call. The race
    must surface as the same outcome as observing no lock at all —
    retry the atomic create — not as an uncaught ``FileNotFoundError``.
    Simulate the race by monkeypatching ``pathlib.Path.stat`` to raise
    ``FileNotFoundError`` exactly once; the helper must catch it,
    re-enter the loop, and succeed.
    """
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()
    # Pre-create the lock so the next acquisition takes the
    # ``FileExistsError`` branch.
    lock_path.write_text(str(clock.time))
    real_stat = pathlib.Path.stat
    calls: list[int] = []

    def flaky_stat(self: pathlib.Path, *args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        if len(calls) == 1 and self == lock_path:
            # Simulate disappearance between O_EXCL fail and stat:
            # the lock file is no longer here.
            lock_path.unlink()
            raise FileNotFoundError(f"vanished: {self}")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "stat", flaky_stat)

    with module.RunLock(lock_path, now=clock):
        assert lock_path.exists()


def test_run_lock_creates_parent_directories(tmp_path: pathlib.Path) -> None:
    """``.spx/audits/<lang>/`` may not exist yet; the helper creates it."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "deep" / "nested" / "path" / "main.md.lock"
    clock = _FakeClock()

    with module.RunLock(lock_path, now=clock):
        assert lock_path.exists()


# ---------------------------------------------------------------------------
# expand_diff_range
# ---------------------------------------------------------------------------


def test_expand_diff_range_returns_files_changed_between_commits(
    repo: pathlib.Path,
) -> None:
    """``HEAD~1..HEAD`` returns files modified by the most recent commit."""
    module = _load_audit_orchestrator()
    _commit_files(repo, {"src/a.ts": "first\n", "src/b.py": "first\n"}, "first")
    _commit_files(repo, {"src/a.ts": "second\n"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", repo=repo)

    assert files == ["src/a.ts"]


def test_expand_diff_range_filters_by_single_pattern(repo: pathlib.Path) -> None:
    """A single ``*.ts`` pattern excludes ``.py`` and ``.tsx`` files."""
    module = _load_audit_orchestrator()
    _commit_files(repo, {"keep.ts": "x", "skip.py": "x", "skip.tsx": "x"}, "first")
    _commit_files(repo, {"keep.ts": "y", "skip.py": "y", "skip.tsx": "y"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", patterns=["*.ts"], repo=repo)

    assert files == ["keep.ts"]


def test_expand_diff_range_combines_multiple_patterns(repo: pathlib.Path) -> None:
    """Multiple patterns are unioned by ``git diff -- <pat1> <pat2>``."""
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()
    _commit_files(repo, {"only.py": "x"}, "first")
    _commit_files(repo, {"only.py": "y"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", patterns=["*.ts"], repo=repo)

    assert files == []


def test_expand_diff_range_with_no_patterns_returns_all_files(
    repo: pathlib.Path,
) -> None:
    """``patterns=None`` runs ``git diff --name-only <range>`` without filter."""
    module = _load_audit_orchestrator()
    _commit_files(repo, {"a.ts": "x", "b.py": "x", "c.tsx": "x"}, "first")
    _commit_files(repo, {"a.ts": "y", "b.py": "y", "c.tsx": "y"}, "second")

    files = module.expand_diff_range("HEAD~1..HEAD", repo=repo)

    assert sorted(files) == ["a.ts", "b.py", "c.tsx"]


def test_expand_diff_range_default_head_returns_uncommitted_changes(
    repo: pathlib.Path,
) -> None:
    """Range ``HEAD`` (no commits ahead) reports staged + unstaged changes."""
    module = _load_audit_orchestrator()
    (repo / "edited.ts").write_text("new content\n", encoding="utf-8")
    _git(repo, "add", "edited.ts")

    files = module.expand_diff_range("HEAD", patterns=["*.ts"], repo=repo)

    assert files == ["edited.ts"]


# ---------------------------------------------------------------------------
# branch_scope
# ---------------------------------------------------------------------------


def test_branch_scope_returns_files_added_by_branch(repo: pathlib.Path) -> None:
    """Files committed after origin/main snapshot are reported."""
    module = _load_audit_orchestrator()
    _commit_files(repo, {"old.ts": "x", "old.py": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/audit-scope", "--quiet")
    _commit_files(repo, {"new.ts": "y", "new.tsx": "y"}, "branch work")

    files = module.branch_scope("main", repo=repo)

    assert sorted(files) == ["new.ts", "new.tsx"]


def test_branch_scope_filters_by_patterns(repo: pathlib.Path) -> None:
    """Patterns restrict the result to matching extensions."""
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/no-work", "--quiet")

    files = module.branch_scope("main", repo=repo)

    assert files == []


def test_branch_scope_uses_origin_prefix_for_arbitrary_base(
    repo: pathlib.Path,
) -> None:
    """Any base ref name is composed as ``origin/<base_ref>``."""
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()
    prior_sha = _commit_files(repo, {"old.ts": "x"}, "old work")
    _commit_files(repo, {"new.ts": "y", "another.tsx": "y"}, "new work")

    files = module.modified_since(prior_sha, repo=repo)

    assert sorted(files) == ["another.tsx", "new.ts"]


def test_modified_since_filters_by_patterns(repo: pathlib.Path) -> None:
    """Patterns restrict the result to matching extensions."""
    module = _load_audit_orchestrator()
    prior_sha = _commit_files(repo, {"seed.ts": "x"}, "seed")
    _commit_files(repo, {"keep.ts": "y", "keep.tsx": "y", "skip.py": "y"}, "mixed work")

    files = module.modified_since(prior_sha, patterns=["*.ts", "*.tsx"], repo=repo)

    assert sorted(files) == ["keep.ts", "keep.tsx"]


def test_modified_since_is_empty_when_no_commits_past_sha(
    repo: pathlib.Path,
) -> None:
    """A repo at the same SHA as ``prior_sha`` yields an empty result."""
    module = _load_audit_orchestrator()
    prior_sha = _commit_files(repo, {"seed.ts": "x"}, "seed")

    files = module.modified_since(prior_sha, repo=repo)

    assert files == []


def test_modified_since_includes_files_modified_by_later_commits(
    repo: pathlib.Path,
) -> None:
    """A file edited in a commit past ``prior_sha`` appears in the result."""
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()
    sha = _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable(sha, repo=repo) is True


def test_is_sha_reachable_accepts_abbreviated_sha(repo: pathlib.Path) -> None:
    """Git accepts unique SHA prefixes; the helper does not require full length."""
    module = _load_audit_orchestrator()
    sha = _commit_files(repo, {"seed.ts": "x"}, "seed")
    abbreviated = sha[:SHA_ABBREV_LENGTH]

    assert module.is_sha_reachable(abbreviated, repo=repo) is True


def test_is_sha_reachable_returns_false_for_unknown_sha(
    repo: pathlib.Path,
) -> None:
    """A syntactically valid SHA that no commit produced is unreachable.

    Models the failure mode where a state-file SHA was force-pushed away
    or never fetched into the local clone.
    """
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable(NONEXISTENT_SHA, repo=repo) is False


def test_is_sha_reachable_returns_false_for_malformed_input(
    repo: pathlib.Path,
) -> None:
    """A non-SHA string (e.g., a typo'd value) is treated as unreachable."""
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable("not-a-sha", repo=repo) is False


def test_is_sha_reachable_returns_false_for_tree_object(
    repo: pathlib.Path,
) -> None:
    """A SHA that resolves to a non-commit object (a tree) is unreachable."""
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "seed")
    tree_sha = _git(repo, "rev-parse", "HEAD^{tree}").strip()

    assert module.is_sha_reachable(tree_sha, repo=repo) is False


# ---------------------------------------------------------------------------
# AuditState / Finding / ResolvedFinding / load_state / save_state /
# assign_finding_id
# ---------------------------------------------------------------------------


def _sample_state(module: ModuleType) -> Any:
    """Return a fresh AuditState with one open and one resolved finding."""
    open_finding = module.Finding(
        id="f-001",
        file_line="src/orders.py:42",
        concern="comprehension",
        root_cause="processOrders tangles IO with logic",
        required_fix="Extract pure compute_order_totals helper",
        first_seen=SAMPLE_FIRST_RUN_SHA,
    )
    resolved_finding = module.ResolvedFinding(
        id="f-002",
        file_line="src/payments.py:7",
        concern="adr-compliance",
        root_cause="Direct sendgrid import — ADR mandates DI",
        first_seen=SAMPLE_FIRST_RUN_SHA,
        resolved_at=SAMPLE_LAST_RUN_SHA,
    )
    return module.AuditState(
        branch=SAMPLE_BRANCH,
        first_run_sha=SAMPLE_FIRST_RUN_SHA,
        first_run_at=SAMPLE_FIRST_RUN_AT,
        last_run_sha=SAMPLE_LAST_RUN_SHA,
        last_run_at=SAMPLE_LAST_RUN_AT,
        last_verdict=REJECTED_VERDICT,
        run_count=2,
        next_finding_id=3,
        open_findings=[open_finding],
        resolved_findings=[resolved_finding],
    )


def test_load_state_returns_none_when_path_absent(tmp_path: pathlib.Path) -> None:
    """A nonexistent state-file path resolves to ``None``, not an exception."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "audits" / "python" / "main.md"

    assert module.load_state(state_path) is None


def test_save_state_writes_state_file_with_frontmatter_and_tables(
    tmp_path: pathlib.Path,
) -> None:
    """save_state writes a file containing the branch, IDs, and table headers."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"

    module.save_state(_sample_state(module), state_path)

    content = state_path.read_text(encoding="utf-8")
    assert SAMPLE_BRANCH in content
    assert "f-001" in content
    assert "f-002" in content
    assert "## Open findings" in content
    assert "## Resolved findings" in content


def test_save_state_creates_parent_directories(tmp_path: pathlib.Path) -> None:
    """``.spx/audits/<lang>/`` may not exist yet; save_state creates it."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "deep" / "nested" / "audits" / "main.md"

    module.save_state(_sample_state(module), state_path)

    assert state_path.exists()


def test_load_state_raises_state_file_corrupt_error_on_malformed_frontmatter(
    tmp_path: pathlib.Path,
) -> None:
    """A file that fails to parse raises ``StateFileCorruptError``."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "corrupt.md"
    state_path.write_text("---\nbranch: main\n", encoding="utf-8")

    with pytest.raises(module.StateFileCorruptError) as exc_info:
        module.load_state(state_path)

    assert str(state_path) in str(exc_info.value)


def test_load_state_translates_truncated_row_to_state_file_corrupt_error(
    tmp_path: pathlib.Path,
) -> None:
    """A truncated table row raises ``StateFileCorruptError``, not ``IndexError``.

    Callers branch on ``StateFileCorruptError`` for the recovery path
    (e.g., discard-then-rerun). An uncaught ``IndexError`` from row
    indexing would bypass that branch — out-of-band editing or a
    partial write from a non-atomic predecessor must surface through
    the same channel as a malformed frontmatter.
    """
    module = _load_audit_orchestrator()
    state_path = tmp_path / "truncated.md"
    # Valid frontmatter; Open-findings table header + separator + a row
    # that is missing the trailing ``required_fix`` and ``first_seen``
    # cells. The row has 4 cells where the schema expects 6.
    state_path.write_text(
        "\n".join(
            [
                "---",
                "branch: feature/x",
                "schema_version: 1",
                "first_run_sha: aaa",
                "first_run_at: 2026-01-01T00:00:00Z",
                "last_run_sha: aaa",
                "last_run_at: 2026-01-01T00:00:00Z",
                "last_verdict: REJECTED",
                "run_count: 1",
                "next_finding_id: 2",
                "---",
                "",
                "## Open findings",
                "",
                "| ID | File:line | Concern | Root cause | Required fix | First seen |",
                "| --- | --- | --- | --- | --- | --- |",
                "| f-001 | src/a.py:1 | comp | trunc |",
                "",
                "## Resolved findings",
                "",
                "| ID | File:line | Concern | Root cause | First seen | Resolved at |",
                "| --- | --- | --- | --- | --- | --- |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(module.StateFileCorruptError) as exc_info:
        module.load_state(state_path)

    assert str(state_path) in str(exc_info.value)


def test_save_state_is_atomic_via_temp_then_replace(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure during the rename leaves the prior file's content unchanged."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    prior_content = "prior content"
    state_path.write_text(prior_content, encoding="utf-8")

    class ReplaceFailed(OSError):
        pass

    def failing_replace(src: object, dst: object) -> None:
        raise ReplaceFailed(f"simulated rename failure: {src} -> {dst}")

    monkeypatch.setattr(module.os, "replace", failing_replace)

    with pytest.raises(ReplaceFailed):
        module.save_state(_sample_state(module), state_path)

    assert state_path.read_text(encoding="utf-8") == prior_content
    tmp_file = state_path.with_name(state_path.name + ".tmp")
    assert tmp_file.exists()
    assert SAMPLE_BRANCH in tmp_file.read_text(encoding="utf-8")


def test_state_round_trip_preserves_frontmatter_and_findings(
    tmp_path: pathlib.Path,
) -> None:
    """save_state followed by load_state reproduces the original AuditState."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    original = _sample_state(module)

    module.save_state(original, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded == original


def test_state_round_trip_preserves_empty_finding_tables(
    tmp_path: pathlib.Path,
) -> None:
    """A state with zero findings round-trips with empty tables intact."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    empty_state = module.AuditState(
        branch=SAMPLE_BRANCH,
        first_run_sha=SAMPLE_FIRST_RUN_SHA,
        first_run_at=SAMPLE_FIRST_RUN_AT,
        last_run_sha=SAMPLE_FIRST_RUN_SHA,
        last_run_at=SAMPLE_FIRST_RUN_AT,
        last_verdict=APPROVED_VERDICT,
        run_count=1,
        next_finding_id=1,
        open_findings=[],
        resolved_findings=[],
    )

    module.save_state(empty_state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded == empty_state


def test_assign_finding_id_returns_f_001_for_empty_state() -> None:
    """The first finding on a branch gets id ``f-001``."""
    module = _load_audit_orchestrator()
    state = module.AuditState(
        branch=SAMPLE_BRANCH,
        first_run_sha=SAMPLE_FIRST_RUN_SHA,
        first_run_at=SAMPLE_FIRST_RUN_AT,
        last_run_sha=SAMPLE_FIRST_RUN_SHA,
        last_run_at=SAMPLE_FIRST_RUN_AT,
        last_verdict=APPROVED_VERDICT,
        run_count=1,
        next_finding_id=1,
    )

    assigned = module.assign_finding_id(state)

    assert assigned == "f-001"


def test_assign_finding_id_increments_counter_each_call() -> None:
    """Each call returns the next ID in sequence and bumps ``next_finding_id``."""
    module = _load_audit_orchestrator()
    state = module.AuditState(
        branch=SAMPLE_BRANCH,
        first_run_sha=SAMPLE_FIRST_RUN_SHA,
        first_run_at=SAMPLE_FIRST_RUN_AT,
        last_run_sha=SAMPLE_FIRST_RUN_SHA,
        last_run_at=SAMPLE_FIRST_RUN_AT,
        last_verdict=APPROVED_VERDICT,
        run_count=1,
        next_finding_id=1,
    )

    first = module.assign_finding_id(state)
    second = module.assign_finding_id(state)
    third = module.assign_finding_id(state)

    assert (first, second, third) == ("f-001", "f-002", "f-003")
    assert state.next_finding_id == 4


def test_assign_finding_id_never_reuses_a_resolved_id() -> None:
    """The counter strictly exceeds every assigned ID, including resolved ones.

    Geometry deliberately decouples ``next_finding_id`` from any
    max-of-finding-ids quantity so a ``max(open_id) + 1`` mutation fails.
    State has open IDs ``[f-001, f-004]``, resolved IDs ``[f-002, f-003]``,
    and ``next_finding_id=7``; counter-driven assignment yields ``f-007``,
    while every alternative mutation would yield a smaller ID.
    """
    module = _load_audit_orchestrator()
    state = module.AuditState(
        branch=SAMPLE_BRANCH,
        first_run_sha=SAMPLE_FIRST_RUN_SHA,
        first_run_at=SAMPLE_FIRST_RUN_AT,
        last_run_sha=SAMPLE_LAST_RUN_SHA,
        last_run_at=SAMPLE_LAST_RUN_AT,
        last_verdict=REJECTED_VERDICT,
        run_count=3,
        next_finding_id=7,
        open_findings=[
            module.Finding(
                id="f-001",
                file_line="src/a.py:1",
                concern="comprehension",
                root_cause="r1",
                required_fix="f1",
                first_seen=SAMPLE_FIRST_RUN_SHA,
            ),
            module.Finding(
                id="f-004",
                file_line="src/d.py:4",
                concern="comprehension",
                root_cause="r4",
                required_fix="f4",
                first_seen=SAMPLE_LAST_RUN_SHA,
            ),
        ],
        resolved_findings=[
            module.ResolvedFinding(
                id="f-002",
                file_line="src/b.py:2",
                concern="comprehension",
                root_cause="r2",
                first_seen=SAMPLE_FIRST_RUN_SHA,
                resolved_at=SAMPLE_LAST_RUN_SHA,
            ),
            module.ResolvedFinding(
                id="f-003",
                file_line="src/c.py:3",
                concern="comprehension",
                root_cause="r3",
                first_seen=SAMPLE_FIRST_RUN_SHA,
                resolved_at=SAMPLE_LAST_RUN_SHA,
            ),
        ],
    )

    assigned = module.assign_finding_id(state)

    assert assigned == "f-007"
    assert state.next_finding_id == 8


def test_state_round_trip_preserves_next_finding_id_across_rerun(
    tmp_path: pathlib.Path,
) -> None:
    """``next_finding_id`` survives serialization so the counter persists."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    state = _sample_state(module)
    expected_next = state.next_finding_id

    module.save_state(state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded is not None
    assert reloaded.next_finding_id == expected_next


# ---------------------------------------------------------------------------
# Cell escaping + regression helpers
# ---------------------------------------------------------------------------


ROOT_CAUSE_WITH_PIPE = "uses | as separator where , is expected"
REQUIRED_FIX_WITH_NEWLINE = "extract pure helper:\nsplit IO from logic"
ROOT_CAUSE_WITH_BOTH = "tangles | parsing with\nIO operations"
REGRESSION_FILE_LINE = "src/orders.py:42"
REGRESSION_ROOT_CAUSE = "processOrders tangles IO with logic"
REGRESSION_REQUIRED_FIX = "extract pure compute_order_totals"


def _finding_with(
    module: ModuleType,
    finding_id: str,
    *,
    root_cause: str = REGRESSION_ROOT_CAUSE,
    required_fix: str = REGRESSION_REQUIRED_FIX,
    file_line: str = REGRESSION_FILE_LINE,
) -> Any:
    return module.Finding(
        id=finding_id,
        file_line=file_line,
        concern="comprehension",
        root_cause=root_cause,
        required_fix=required_fix,
        first_seen=SAMPLE_FIRST_RUN_SHA,
    )


def _resolved_with(
    module: ModuleType,
    finding_id: str,
    *,
    root_cause: str = REGRESSION_ROOT_CAUSE,
    file_line: str = REGRESSION_FILE_LINE,
) -> Any:
    return module.ResolvedFinding(
        id=finding_id,
        file_line=file_line,
        concern="comprehension",
        root_cause=root_cause,
        first_seen=SAMPLE_FIRST_RUN_SHA,
        resolved_at=SAMPLE_LAST_RUN_SHA,
    )


def _state_with(
    module: ModuleType,
    *,
    open_findings: list[Any],
    resolved_findings: list[Any],
    next_finding_id: int,
) -> Any:
    return module.AuditState(
        branch=SAMPLE_BRANCH,
        first_run_sha=SAMPLE_FIRST_RUN_SHA,
        first_run_at=SAMPLE_FIRST_RUN_AT,
        last_run_sha=SAMPLE_LAST_RUN_SHA,
        last_run_at=SAMPLE_LAST_RUN_AT,
        last_verdict=REJECTED_VERDICT,
        run_count=2,
        next_finding_id=next_finding_id,
        open_findings=open_findings,
        resolved_findings=resolved_findings,
    )


def test_state_round_trip_preserves_pipe_character_in_finding_text(
    tmp_path: pathlib.Path,
) -> None:
    """A finding whose root_cause contains ``|`` survives save → load."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    state = _state_with(
        module,
        open_findings=[
            _finding_with(module, "f-001", root_cause=ROOT_CAUSE_WITH_PIPE),
        ],
        resolved_findings=[],
        next_finding_id=2,
    )

    module.save_state(state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded is not None
    assert reloaded.open_findings[0].root_cause == ROOT_CAUSE_WITH_PIPE


def test_state_round_trip_preserves_newline_in_finding_text(
    tmp_path: pathlib.Path,
) -> None:
    """A finding whose required_fix contains ``\\n`` survives save → load."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    state = _state_with(
        module,
        open_findings=[
            _finding_with(module, "f-001", required_fix=REQUIRED_FIX_WITH_NEWLINE),
        ],
        resolved_findings=[],
        next_finding_id=2,
    )

    module.save_state(state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded is not None
    assert reloaded.open_findings[0].required_fix == REQUIRED_FIX_WITH_NEWLINE


def test_state_round_trip_preserves_pipe_character_in_concern_field(
    tmp_path: pathlib.Path,
) -> None:
    """A finding whose concern contains ``|`` survives save → load.

    An auditing skill can emit a concern label combining multiple
    taxonomy tokens (e.g. ``"cohesion | coupling"``). Without
    cell escaping on the concern field the row would split into more
    cells than the schema has columns; load_state would either parse
    the wrong field boundaries or raise ``StateFileCorruptError``.
    """
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    concern_with_pipe = "cohesion | coupling"
    open_finding = module.Finding(
        id="f-001",
        file_line=REGRESSION_FILE_LINE,
        concern=concern_with_pipe,
        root_cause=REGRESSION_ROOT_CAUSE,
        required_fix=REGRESSION_REQUIRED_FIX,
        first_seen=SAMPLE_FIRST_RUN_SHA,
    )
    state = _state_with(
        module,
        open_findings=[open_finding],
        resolved_findings=[],
        next_finding_id=2,
    )

    module.save_state(state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded is not None
    assert reloaded.open_findings[0].concern == concern_with_pipe


def test_state_round_trip_preserves_pipe_character_in_resolved_concern_field(
    tmp_path: pathlib.Path,
) -> None:
    """Concern-cell escaping applies to the resolved table too.

    The serialiser writes ``concern`` for both Open and Resolved
    tables; both must escape the character class, and both parsers
    must reverse it.
    """
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    concern_with_pipe = "cohesion | coupling"
    resolved_finding = module.ResolvedFinding(
        id="f-001",
        file_line=REGRESSION_FILE_LINE,
        concern=concern_with_pipe,
        root_cause=REGRESSION_ROOT_CAUSE,
        first_seen=SAMPLE_FIRST_RUN_SHA,
        resolved_at=SAMPLE_LAST_RUN_SHA,
    )
    state = _state_with(
        module,
        open_findings=[],
        resolved_findings=[resolved_finding],
        next_finding_id=2,
    )

    module.save_state(state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded is not None
    assert reloaded.resolved_findings[0].concern == concern_with_pipe


def test_state_transition_reopen_refreshes_concern_from_incoming_finding(
    tmp_path: pathlib.Path,
) -> None:
    """A regression reopens with the incoming run's concern, not the resolved row's.

    Symmetric with the carry-forward branch in :func:`state_transition`,
    which refreshes ``concern`` from the incoming finding. The reopen
    branch must do the same so an auditing skill that evolves its
    concern taxonomy between runs sees the new label on the reopened
    row instead of the stale resolved-row label.
    """
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"

    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_FIRST_RUN_SHA,
        now=SAMPLE_FIRST_RUN_AT,
        verdict=REJECTED_VERDICT,
        new_findings=[
            {
                "file_line": "src/a.py:1",
                "concern": "old-concern",
                "root_cause": "tangles IO",
                "required_fix": "v1",
            }
        ],
    )
    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_LAST_RUN_SHA,
        now=SAMPLE_LAST_RUN_AT,
        verdict=APPROVED_VERDICT,
        new_findings=[],
    )
    third = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha="ghi9999",
        now="2026-05-12T09:00:00Z",
        verdict=REJECTED_VERDICT,
        new_findings=[
            {
                "file_line": "src/a.py:1",
                "concern": "new-concern",
                "root_cause": "tangles IO",
                "required_fix": "v2",
            }
        ],
    )

    assert [f["concern"] for f in third["reopened"]] == ["new-concern"]
    state = module.load_state(state_path)
    assert state is not None
    assert state.open_findings[0].concern == "new-concern"


def test_state_round_trip_preserves_pipe_and_newline_in_same_field(
    tmp_path: pathlib.Path,
) -> None:
    """A field containing both ``|`` and ``\\n`` round-trips intact."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    state = _state_with(
        module,
        open_findings=[
            _finding_with(module, "f-001", root_cause=ROOT_CAUSE_WITH_BOTH),
        ],
        resolved_findings=[],
        next_finding_id=2,
    )

    module.save_state(state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded is not None
    assert reloaded.open_findings[0].root_cause == ROOT_CAUSE_WITH_BOTH


def test_find_resolved_by_identity_returns_none_when_no_match() -> None:
    """No matching (file_line, root_cause) pair returns ``None``."""
    module = _load_audit_orchestrator()
    state = _state_with(
        module,
        open_findings=[],
        resolved_findings=[
            _resolved_with(module, "f-001", file_line="src/a.py:1"),
        ],
        next_finding_id=2,
    )

    result = module.find_resolved_by_identity(
        state, file_line="src/b.py:2", root_cause="different cause"
    )

    assert result is None


def test_find_resolved_by_identity_returns_matching_resolved_finding() -> None:
    """A matching (file_line, root_cause) pair returns the ResolvedFinding."""
    module = _load_audit_orchestrator()
    matching = _resolved_with(module, "f-001")
    state = _state_with(
        module,
        open_findings=[],
        resolved_findings=[
            _resolved_with(module, "f-002", file_line="other:1", root_cause="x"),
            matching,
        ],
        next_finding_id=3,
    )

    result = module.find_resolved_by_identity(
        state,
        file_line=REGRESSION_FILE_LINE,
        root_cause=REGRESSION_ROOT_CAUSE,
    )

    assert result == matching


def test_reopen_finding_preserves_id_and_does_not_advance_counter() -> None:
    """Reopening a resolved finding moves it back without a new ID."""
    module = _load_audit_orchestrator()
    resolved = _resolved_with(module, "f-001")
    state = _state_with(
        module,
        open_findings=[],
        resolved_findings=[resolved],
        next_finding_id=5,
    )
    counter_before = state.next_finding_id

    reopened = module.reopen_finding(
        state, resolved, required_fix=REGRESSION_REQUIRED_FIX
    )

    assert reopened.id == "f-001"
    assert state.next_finding_id == counter_before
    assert reopened in state.open_findings
    assert resolved not in state.resolved_findings


def test_resolve_finding_preserves_id_and_records_resolved_at() -> None:
    """Resolving an open finding moves it to resolved with the same ID."""
    module = _load_audit_orchestrator()
    finding = _finding_with(module, "f-001")
    state = _state_with(
        module,
        open_findings=[finding],
        resolved_findings=[],
        next_finding_id=2,
    )
    counter_before = state.next_finding_id

    resolved = module.resolve_finding(state, finding, resolved_at=SAMPLE_LAST_RUN_SHA)

    assert resolved.id == "f-001"
    assert resolved.resolved_at == SAMPLE_LAST_RUN_SHA
    assert state.next_finding_id == counter_before
    assert resolved in state.resolved_findings
    assert finding not in state.open_findings


# ---------------------------------------------------------------------------
# uncommitted_scope
# ---------------------------------------------------------------------------


def test_uncommitted_scope_includes_untracked_files(repo: pathlib.Path) -> None:
    """A new file that has not been ``git add``-ed is still in scope."""
    module = _load_audit_orchestrator()
    (repo / "fresh.ts").write_text("brand new", encoding="utf-8")

    files = module.uncommitted_scope(patterns=["*.ts"], repo=repo)

    assert files == ["fresh.ts"]


def test_uncommitted_scope_includes_modified_staged_and_untracked(
    repo: pathlib.Path,
) -> None:
    """All three working-tree categories appear in the same scope."""
    module = _load_audit_orchestrator()
    _commit_files(repo, {"committed.ts": "v1\n"}, "seed")
    (repo / "committed.ts").write_text("v2\n", encoding="utf-8")
    (repo / "staged.ts").write_text("staged content\n", encoding="utf-8")
    _git(repo, "add", "staged.ts")
    (repo / "untracked.ts").write_text("untracked content\n", encoding="utf-8")

    files = module.uncommitted_scope(repo=repo)

    assert sorted(files) == ["committed.ts", "staged.ts", "untracked.ts"]


def test_uncommitted_scope_respects_gitignore(repo: pathlib.Path) -> None:
    """Files matched by ``.gitignore`` are excluded from the scope."""
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()

    files = module.uncommitted_scope(repo=repo)

    assert files == []


# ---------------------------------------------------------------------------
# state_transition (library form)
# ---------------------------------------------------------------------------


def _finding_payload(
    file_line: str,
    root_cause: str,
    required_fix: str,
    concern: str = "comprehension",
) -> dict[str, str]:
    return {
        "file_line": file_line,
        "concern": concern,
        "root_cause": root_cause,
        "required_fix": required_fix,
    }


def test_state_transition_first_run_creates_state_and_assigns_ids(
    tmp_path: pathlib.Path,
) -> None:
    """First run on a branch creates the state file and allocates fresh IDs."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    findings = [
        _finding_payload("src/a.py:1", "tangles IO", "extract helper"),
        _finding_payload("src/b.py:2", "missing guard", "add validation"),
    ]

    result = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_FIRST_RUN_SHA,
        now=SAMPLE_FIRST_RUN_AT,
        verdict=REJECTED_VERDICT,
        new_findings=findings,
    )

    assert [f["id"] for f in result["open"]] == ["f-001", "f-002"]
    assert result["resolved"] == []
    assert result["reopened"] == []

    state = module.load_state(state_path)
    assert state is not None
    assert state.run_count == 1
    assert state.next_finding_id == 3
    assert state.first_run_sha == SAMPLE_FIRST_RUN_SHA


def test_state_transition_carries_open_ids_across_runs(
    tmp_path: pathlib.Path,
) -> None:
    """A finding present in both runs keeps its ID; required_fix refreshes."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    payload = _finding_payload("src/a.py:1", "tangles IO", "fix v1")

    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_FIRST_RUN_SHA,
        now=SAMPLE_FIRST_RUN_AT,
        verdict=REJECTED_VERDICT,
        new_findings=[payload],
    )
    second = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_LAST_RUN_SHA,
        now=SAMPLE_LAST_RUN_AT,
        verdict=REJECTED_VERDICT,
        new_findings=[_finding_payload("src/a.py:1", "tangles IO", "fix v2")],
    )

    assert [f["id"] for f in second["open"]] == ["f-001"]
    assert second["open"][0]["required_fix"] == "fix v2"
    assert second["resolved"] == []
    assert second["reopened"] == []

    state = module.load_state(state_path)
    assert state is not None
    assert state.run_count == 2
    assert state.next_finding_id == 2  # never advanced for carry-over


def test_state_transition_resolves_findings_absent_from_new_run(
    tmp_path: pathlib.Path,
) -> None:
    """An open finding missing from the new run resolves with ``resolved_at``."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_FIRST_RUN_SHA,
        now=SAMPLE_FIRST_RUN_AT,
        verdict=REJECTED_VERDICT,
        new_findings=[_finding_payload("src/a.py:1", "tangles IO", "fix")],
    )

    second = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_LAST_RUN_SHA,
        now=SAMPLE_LAST_RUN_AT,
        verdict=APPROVED_VERDICT,
        new_findings=[],
    )

    assert second["open"] == []
    assert [r["id"] for r in second["resolved"]] == ["f-001"]
    assert second["resolved"][0]["resolved_at"] == SAMPLE_LAST_RUN_SHA


def test_state_transition_reopens_regression_with_original_id(
    tmp_path: pathlib.Path,
) -> None:
    """A root cause returning at the same file:line reopens the original ID."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    payload = _finding_payload("src/a.py:1", "tangles IO", "fix")

    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_FIRST_RUN_SHA,
        now=SAMPLE_FIRST_RUN_AT,
        verdict=REJECTED_VERDICT,
        new_findings=[payload],
    )
    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SAMPLE_LAST_RUN_SHA,
        now=SAMPLE_LAST_RUN_AT,
        verdict=APPROVED_VERDICT,
        new_findings=[],
    )
    third = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha="ghi9999",
        now="2026-05-12T09:00:00Z",
        verdict=REJECTED_VERDICT,
        new_findings=[_finding_payload("src/a.py:1", "tangles IO", "fix again")],
    )

    assert [f["id"] for f in third["reopened"]] == ["f-001"]
    assert [f["id"] for f in third["open"]] == ["f-001"]
    state = module.load_state(state_path)
    assert state is not None
    # Counter must not advance for a regression reopen.
    assert state.next_finding_id == 2


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------


def _run_cli(
    *args: str, stdin: str = "", cwd: pathlib.Path | None = None
) -> tuple[int, str, str]:
    """Invoke the script's CLI as a subprocess and return (rc, stdout, stderr)."""
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell
        [sys.executable, str(AUDIT_ORCHESTRATOR), *args],
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
    """``branch-slug`` derives the on-disk slug for the named branch."""
    rc, out, _ = _run_cli(
        "branch-slug", "--branch", "feature/foo", "--state-dir", str(tmp_path)
    )

    assert rc == 0
    assert out.strip() == "feature__foo"


def test_cli_branch_slug_accepts_no_state_dir() -> None:
    """``branch-slug`` can derive a slug without a state-file collision check."""
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


def test_cli_acquire_and_release_lock_round_trip(tmp_path: pathlib.Path) -> None:
    """``acquire-lock`` then ``release-lock`` succeeds and leaves no file."""
    lock_path = tmp_path / "audits" / "python" / "main.md.lock"

    rc_acquire, _, _ = _run_cli("acquire-lock", "--path", str(lock_path))
    assert rc_acquire == 0
    assert lock_path.exists()

    rc_release, _, _ = _run_cli("release-lock", "--path", str(lock_path))
    assert rc_release == 0
    assert not lock_path.exists()


def test_cli_acquire_lock_refuses_when_fresh(tmp_path: pathlib.Path) -> None:
    """A fresh lock at the path causes ``acquire-lock`` to exit 1."""
    lock_path = tmp_path / "main.md.lock"
    lock_path.write_text("held")

    rc, _, _ = _run_cli(
        "acquire-lock", "--path", str(lock_path), "--max-age-seconds", "600"
    )

    assert rc == 1
    assert lock_path.exists()


def test_cli_state_transition_exits_3_on_missing_finding_keys(
    tmp_path: pathlib.Path,
) -> None:
    """A finding missing ``required_fix`` exits 3 with a clean stderr message.

    A KeyError traceback would surface as exit 1 conflated with
    lock-held; exit 3 is the agent's signal that the upstream
    auditing skill produced a malformed payload.
    """
    state_path = tmp_path / "main.md"
    payload = json.dumps(
        {
            "findings": [
                {
                    "file_line": "src/a.py:1",
                    "concern": "comprehension",
                    "root_cause": "tangles IO",
                    # required_fix omitted
                }
            ]
        }
    )

    rc, _, err = _run_cli(
        "state-transition",
        "--state-file",
        str(state_path),
        "--branch",
        SAMPLE_BRANCH,
        "--current-sha",
        SAMPLE_FIRST_RUN_SHA,
        "--now",
        SAMPLE_FIRST_RUN_AT,
        "--verdict",
        REJECTED_VERDICT,
        stdin=payload,
    )

    assert rc == 3
    assert "required_fix" in err
    assert not state_path.exists()


def test_cli_state_transition_exits_2_on_corrupt_state_file(
    tmp_path: pathlib.Path,
) -> None:
    """A corrupt state file exits 2 distinct from lock-held (1) and bad input (3).

    The agent's recovery prose names ``StateFileCorruptError`` as the
    signal to ask the caller whether to discard the file or keep it.
    Without a structured exit code the agent would conflate corruption
    with other failure modes.
    """
    state_path = tmp_path / "corrupt.md"
    # Frontmatter has a leading delimiter but no trailing one — the parser
    # raises ValueError, which load_state wraps as StateFileCorruptError.
    state_path.write_text("---\nbranch: main\n", encoding="utf-8")
    payload = json.dumps({"findings": []})

    rc, _, err = _run_cli(
        "state-transition",
        "--state-file",
        str(state_path),
        "--branch",
        SAMPLE_BRANCH,
        "--current-sha",
        SAMPLE_FIRST_RUN_SHA,
        "--now",
        SAMPLE_FIRST_RUN_AT,
        "--verdict",
        REJECTED_VERDICT,
        stdin=payload,
    )

    assert rc == 2
    assert "corrupt state file" in err


def test_save_state_cleans_up_tmp_on_write_text_failure(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``write_text`` failure removes the partial ``.tmp`` orphan.

    Distinct from the ``os.replace`` failure path, which intentionally
    preserves ``.tmp`` so the new content remains recoverable. The
    ``write_text`` failure leaves a truncated-or-empty file with no
    recovery value, and repeated failures would accumulate orphans
    alongside the state file without this cleanup.
    """
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"

    class WriteFailed(OSError):
        pass

    real_write_text = pathlib.Path.write_text

    def failing_write_text(
        self: pathlib.Path, data: str, *args: Any, **kwargs: Any
    ) -> int:
        if self.name.endswith(".tmp"):
            # Emulate a partial write before the failure.
            real_write_text(self, data[: len(data) // 2], *args, **kwargs)
            raise WriteFailed(f"simulated mid-write failure: {self}")
        return real_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "write_text", failing_write_text)

    with pytest.raises(WriteFailed):
        module.save_state(_sample_state(module), state_path)

    tmp_file = state_path.with_name(state_path.name + ".tmp")
    assert not tmp_file.exists()
    assert not state_path.exists()


def test_cli_state_transition_round_trips_findings(tmp_path: pathlib.Path) -> None:
    """``state-transition`` reads JSON findings on stdin, persists, emits classification."""
    state_path = tmp_path / "main.md"
    payload = json.dumps(
        {
            "findings": [
                {
                    "file_line": "src/a.py:1",
                    "concern": "comprehension",
                    "root_cause": "tangles IO",
                    "required_fix": "extract helper",
                }
            ]
        }
    )

    rc, out, _ = _run_cli(
        "state-transition",
        "--state-file",
        str(state_path),
        "--branch",
        SAMPLE_BRANCH,
        "--current-sha",
        SAMPLE_FIRST_RUN_SHA,
        "--now",
        SAMPLE_FIRST_RUN_AT,
        "--verdict",
        REJECTED_VERDICT,
        stdin=payload,
    )

    assert rc == 0
    response = json.loads(out)
    assert [f["id"] for f in response["open"]] == ["f-001"]
    assert response["resolved"] == []
    assert response["reopened"] == []
    assert state_path.exists()


# ---------------------------------------------------------------------------
# Module surface
# ---------------------------------------------------------------------------


def test_helpers_under_audit_are_exposed_by_module() -> None:
    """The full helper symbol set must be importable from audit_orchestrator."""
    module = _load_audit_orchestrator()

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
        "RunLock",
        "RunLockError",
        "DetachedHeadError",
        "StateFileCorruptError",
        "AuditState",
        "Finding",
        "ResolvedFinding",
        "load_state",
        "save_state",
        "assign_finding_id",
        "find_resolved_by_identity",
        "find_open_by_identity",
        "reopen_finding",
        "resolve_finding",
        "state_transition",
        "build_parser",
        "main",
        "compute_verdict_diff",
    ]:
        assert hasattr(module, name), f"missing symbol: {name}"


# Verdict-diff tests — the prior-verdict-thread state surface that
# pr-review-orchestrator drives over a PR comment thread. Identity is
# (file, line, rule, message); diff carries forward resolved across runs.
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
    module = _load_audit_orchestrator()
    current = _verdict([VERDICT_FINDING_A_DICT, VERDICT_FINDING_B_DICT])
    enriched = module.compute_verdict_diff(prior=None, current=current)
    assert enriched["resolved"] == []
    assert enriched["reopened"] == []


def test_verdict_diff_resolves_findings_no_longer_open() -> None:
    module = _load_audit_orchestrator()
    prior = _verdict([VERDICT_FINDING_A_DICT, VERDICT_FINDING_B_DICT])
    current = _verdict([VERDICT_FINDING_A_DICT])
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["resolved"] == [VERDICT_FINDING_B_DICT]
    assert enriched["reopened"] == []


def test_verdict_diff_carries_resolved_across_runs() -> None:
    module = _load_audit_orchestrator()
    prior = {
        **_verdict([VERDICT_FINDING_A_DICT]),
        "resolved": [VERDICT_FINDING_B_DICT],
    }
    current = _verdict([VERDICT_FINDING_A_DICT])
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["resolved"] == [VERDICT_FINDING_B_DICT]


def test_verdict_diff_reopens_finding_in_prior_resolved() -> None:
    module = _load_audit_orchestrator()
    prior = {
        **_verdict([VERDICT_FINDING_A_DICT]),
        "resolved": [VERDICT_FINDING_B_DICT],
    }
    current = _verdict([VERDICT_FINDING_A_DICT, VERDICT_FINDING_B_DICT])
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["reopened"] == [VERDICT_FINDING_B_DICT]
    assert enriched["resolved"] == []


def test_verdict_diff_walks_into_child_verdicts() -> None:
    module = _load_audit_orchestrator()
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
    module = _load_audit_orchestrator()
    prior_warning = {**VERDICT_FINDING_A_DICT, "severity": "WARNING"}
    prior = _verdict([prior_warning])
    current = _verdict([VERDICT_FINDING_A_DICT])  # same identity, REJECT severity
    enriched = module.compute_verdict_diff(prior=prior, current=current)
    assert enriched["resolved"] == []
    assert enriched["reopened"] == []
