"""Scenario tests for audit_orchestrator helpers required by the
``spx/21-spec-tree.enabler/17-auditing.adr.md`` Compliance MUST clause.

Covers four helpers the ``/auditing`` skill and the ``auditor`` agent
delegate to so deterministic computations stay out of skill prose and
agent prompts (the ADR's NEVER clause forbids inline shell pipelines for
hashing, branch detection, slug derivation, and lock acquisition):

- ``detect_base_ref`` — derives the bare base-branch name from
  ``refs/remotes/origin/HEAD`` (defaults to ``main`` when no remote is
  configured).
- ``detect_current_branch`` — returns the current branch and refuses to
  produce a label for a detached HEAD.
- ``branch_slug`` — derives the on-disk state-file slug for a branch and
  appends a SHA-256 suffix when a collision against a different branch's
  state file is detected.
- ``RunLock`` — file-based exclusive lock with a TTL that distinguishes
  fresh locks (refuse) from stale locks left by a crashed run
  (overwrite).
- ``expand_diff_range`` — runs ``git diff --name-only <range> -- <patterns>``
  and returns the resulting file list so the ``/auditing`` skill prose
  does not embed inline shell.
- ``branch_scope`` — returns the files this branch changed relative to
  ``origin/<base_ref>``, composing the diff range the interim agent's
  Phase 0 step 6 used inline.
- ``modified_since`` — returns files changed in repo between an arbitrary
  prior SHA and HEAD, used by the interim agent's Phase R step 5 re-run
  scope to identify which files to re-comprehend.
- ``is_sha_reachable`` — boolean check that a SHA stored in prior state
  is still resolvable to a commit in the local clone, used to detect
  the interim agent's "Last_run_sha unreachable" failure mode.
- ``AuditState`` / ``Finding`` / ``ResolvedFinding`` / ``load_state`` /
  ``save_state`` / ``assign_finding_id`` — typed in-memory shape for
  the state file ``.spx/audits/<lang>/<branch-slug>.md`` plus the
  monotonic finding-ID counter the interim agent's Phase F/R protocol
  depends on. PRIORITY 1 scope: round-trip persistence and ID
  assignment that never reuses a resolved finding's ID.
- ``find_resolved_by_identity`` / ``reopen_finding`` / ``resolve_finding``
  plus round-trip preservation of ``|`` and newlines in finding text —
  PRIORITY 2 regression-detection helpers. Reopening a resolved finding
  whose root cause has returned at the same file:line keeps the
  original ID (interim agent's "never create a new ID for a regression"
  invariant).
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

# parents[4] = repo root (this file lives 4 levels deep: spx/21-spec-tree.enabler/
# 65-auditing.enabler/tests/<file>).
# Tree surgery that changes the enabler's depth must update this index.
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[4]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
)
AUDIT_ORCHESTRATOR = SCRIPTS_DIR / "audit_orchestrator.py"

DEFAULT_BASE_REF = "main"
COLLISION_SUFFIX_LENGTH = 8
LOCK_TTL_SECONDS = 600
FRESH_LOCK_AGE = 60
STALE_LOCK_AGE = 1200
LOCK_AGE_HALF_TTL = 300


def _load_audit_orchestrator() -> ModuleType:
    """Load plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py.

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


@pytest.fixture
def repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """tmp_path-rooted git repo on branch ``main`` with one commit."""
    _init_repo(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# detect_base_ref
# ---------------------------------------------------------------------------


def test_detect_base_ref_strips_origin_head_prefix(repo: pathlib.Path) -> None:
    """When ``refs/remotes/origin/HEAD`` exists, return the bare branch name.

    The interim agent's failure mode "Last_run_sha unreachable" depended on
    composing ``origin/<base>..HEAD``; without prefix stripping the resulting
    ref would be ``origin/refs/remotes/origin/main..HEAD`` and git would halt
    the orchestrator before any audit ran.
    """
    module = _load_audit_orchestrator()
    # Simulate `origin` with HEAD pointing at refs/heads/main without needing a
    # network remote: git symbolic-ref accepts a target arg that bypasses the
    # usual `git remote set-head` requirement.
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
    """Repos without an ``origin`` remote default to ``main``.

    Solo-developer and freshly-bootstrapped checkouts have no remote configured;
    the orchestrator must still produce a usable base ref instead of halting.
    """
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
    """Detached HEAD must raise so the orchestrator refuses to create state.

    The interim agent's Phase 0 step 2 explicitly halts on detached HEAD —
    state-file naming requires a stable branch label.
    """
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
    """Two branches whose base slugs collide must produce distinct slugs.

    ``feature/foo`` slugs to ``feature__foo`` and a literal branch named
    ``feature__foo`` slugs identically; the helper detects the existing state
    file's frontmatter ``branch`` differs from the new branch and appends an
    8-character SHA-256 suffix derived from the new branch name.
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
    """Two calls with the same colliding branch produce the same suffix.

    Determinism matters because the suffix is the on-disk identity of the
    state file across re-runs; a non-deterministic suffix would orphan prior
    state on the next invocation.
    """
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
    """Monotonic time source whose value the test controls.

    The ``time`` attribute is read by ``RunLock`` via its injected ``now``
    callable; tests advance time by reassigning the attribute rather than
    sleeping so lock-TTL behavior is exercised without real waits.
    """

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

    The interim agent's failure mode "Race against parallel runs" requires
    that the lock be removed on every exit path including failure; otherwise
    a crashed run leaves a fresh-looking lock that blocks the next run for a
    full TTL window.
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
    """A second acquisition during the TTL window raises RunLockError."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()

    outer = module.RunLock(lock_path, now=clock)
    outer.__enter__()
    try:
        clock.time += FRESH_LOCK_AGE
        with pytest.raises(module.RunLockError):
            with module.RunLock(lock_path, now=clock):
                pass
    finally:
        outer.__exit__(None, None, None)


def test_run_lock_overwrites_when_existing_lock_is_stale(
    tmp_path: pathlib.Path,
) -> None:
    """A lock older than ``max_age_seconds`` is overwritten (crashed run)."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / "main.md.lock"
    clock = _FakeClock()

    # Write a stale lock directly so the test owns the timestamp; the helper
    # uses the file's mtime to compute age.
    lock_path.write_text(str(clock.time))
    stale_time = clock.time - STALE_LOCK_AGE
    os.utime(lock_path, (stale_time, stale_time))

    with module.RunLock(lock_path, now=clock):
        # Acquisition succeeded — the helper recognized the stale lock and
        # overwrote it.
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

    # With the default 600s TTL this would refuse; with 120s it overwrites.
    with module.RunLock(lock_path, max_age_seconds=custom_ttl, now=clock):
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


def _commit_files(repo: pathlib.Path, files: dict[str, str], message: str) -> str:
    """Write ``files`` (path → content) into ``repo``, commit, return SHA."""
    for relpath, content in files.items():
        target = repo / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        _git(repo, "add", relpath)
    _git(repo, "commit", "-m", message, "--quiet")
    return _git(repo, "rev-parse", "HEAD").strip()


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
    """A pattern that matches nothing in the diff yields an empty list.

    Important: empty is the expected representation of "no matching files",
    not an error. The ``/auditing`` skill's Phase 0 step 1 documents this as
    the no-scope-detected case it halts on with a deliberate message.
    """
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
    """Range ``HEAD`` (no commits ahead) reports staged + unstaged changes.

    This is the SKILL.md Phase 0 default scope: when the caller passes no
    explicit range, the orchestrator falls back to ``HEAD`` to capture
    work-in-progress edits.
    """
    module = _load_audit_orchestrator()
    (repo / "edited.ts").write_text("new content\n", encoding="utf-8")
    _git(repo, "add", "edited.ts")

    files = module.expand_diff_range("HEAD", patterns=["*.ts"], repo=repo)

    assert files == ["edited.ts"]


# ---------------------------------------------------------------------------
# branch_scope
# ---------------------------------------------------------------------------


def _snapshot_origin(repo: pathlib.Path, base_ref: str) -> str:
    """Write ``.git/refs/remotes/origin/<base_ref>`` pointing at current HEAD.

    Simulates ``origin`` having ``<base_ref>`` at the local HEAD without
    requiring a network remote. ``branch_scope`` resolves ``origin/<base>``
    via the on-disk ref, which is precisely what this file represents.
    """
    head_sha = _git(repo, "rev-parse", "HEAD").strip()
    target = repo / ".git" / "refs" / "remotes" / "origin" / base_ref
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{head_sha}\n", encoding="utf-8")
    return head_sha


def test_branch_scope_returns_files_added_by_branch(repo: pathlib.Path) -> None:
    """Files committed after origin/main snapshot are reported.

    Simulates the orchestrator's "what changed on this feature branch?"
    query by snapshotting origin/main at one SHA and then committing more
    work; only the new files appear in the scope.
    """
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
    """A branch with zero commits past origin/main yields an empty scope.

    Mirrors the orchestrator's no-scope-detected case: nothing to audit,
    so an empty list is the correct representation (not an error).
    """
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/no-work", "--quiet")

    files = module.branch_scope("main", repo=repo)

    assert files == []


def test_branch_scope_uses_origin_prefix_for_arbitrary_base(
    repo: pathlib.Path,
) -> None:
    """Any base ref name is composed as ``origin/<base_ref>``.

    Marketplace projects vary their base branch (``main``, ``develop``,
    ``trunk``). The helper must compose the diff range against
    ``origin/<base_ref>`` literally without assuming ``main``.
    """
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
    """Files added to base after the branch-off are not part of the scope.

    If the base branch moves forward after the feature branch is cut, the
    scope must still report only the feature-branch additions. Composing
    the range as ``origin/<base>...HEAD`` (three-dot form: diff between
    the merge-base of HEAD and origin/<base> and HEAD itself) gives this
    semantics; the two-dot form ``origin/<base>..HEAD`` is a tree-diff
    that would include the new base commits as deletions.
    """
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "base")
    _snapshot_origin(repo, "main")
    _git(repo, "switch", "-c", "feature/parallel", "--quiet")
    _commit_files(repo, {"branch_only.ts": "y"}, "branch work")
    # Advance main on disk too — branch_scope must still report only
    # branch_only.ts (the feature commit), not the new base commit.
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
    """Files added in commits past ``prior_sha`` are reported.

    Mirrors the interim agent's Phase R step 5 re-run scope query: given a
    SHA from a previous run, which files in the working tree must be
    re-comprehended this run?
    """
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
    """A repo at the same SHA as ``prior_sha`` yields an empty result.

    Re-running an audit with no commits since the prior run is the
    common case; an empty list is the correct representation of
    "nothing to re-comprehend", not an error.
    """
    module = _load_audit_orchestrator()
    prior_sha = _commit_files(repo, {"seed.ts": "x"}, "seed")

    files = module.modified_since(prior_sha, repo=repo)

    assert files == []


def test_modified_since_includes_files_modified_by_later_commits(
    repo: pathlib.Path,
) -> None:
    """A file edited in a commit past ``prior_sha`` appears in the result.

    The re-run scope must include modified files, not just newly added
    ones, so the auditor re-comprehends edits to functions it previously
    flagged.
    """
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

    Re-run scope is intentionally tree-diff (two-dot): a file present
    at ``prior_sha`` but absent from HEAD must appear in the result so
    the auditor knows the file no longer exists in the working tree.
    Three-dot semantics would compute diff from ``merge-base..HEAD``
    instead — which excludes commits exclusive to ``prior_sha``'s
    history and would miss the deletion.

    Fixture geometry: ``prior_sha`` lives on a branch (``diverge``)
    that holds a file (``diverge_only.ts``) HEAD has never seen; HEAD
    is on ``main`` with its own commit (``main_only.ts``) and the two
    branches are not merged. Two-dot reports both files (deletion +
    addition); three-dot reports only ``main_only.ts``.
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


def test_is_sha_reachable_accepts_abbreviated_sha(
    repo: pathlib.Path,
) -> None:
    """Git accepts unique SHA prefixes; the helper does not require full length.

    The interim agent's state file stored full SHAs but the helper must
    not gratuitously reject abbreviated forms — git's own resolution
    accepts any unambiguous prefix.
    """
    module = _load_audit_orchestrator()
    sha = _commit_files(repo, {"seed.ts": "x"}, "seed")
    abbreviated = sha[:SHA_ABBREV_LENGTH]

    assert module.is_sha_reachable(abbreviated, repo=repo) is True


def test_is_sha_reachable_returns_false_for_unknown_sha(
    repo: pathlib.Path,
) -> None:
    """A syntactically valid SHA that no commit produced is unreachable.

    This is the interim agent's "Last_run_sha unreachable" failure mode:
    a state file pinned to a SHA that was force-pushed away or never
    fetched into the local clone.
    """
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable(NONEXISTENT_SHA, repo=repo) is False


def test_is_sha_reachable_returns_false_for_malformed_input(
    repo: pathlib.Path,
) -> None:
    """A non-SHA string (e.g., a typo'd value) is treated as unreachable.

    The helper guards a re-run scope query; any input git cannot resolve
    to a commit is functionally equivalent to "unreachable" — the caller
    falls back to re-scanning the full branch scope either way.
    """
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "seed")

    assert module.is_sha_reachable("not-a-sha", repo=repo) is False


def test_is_sha_reachable_returns_false_for_tree_object(
    repo: pathlib.Path,
) -> None:
    """A SHA that resolves to a non-commit object (a tree) is unreachable.

    The helper specifically checks for commit reachability so the caller
    can safely compose ``<sha>..HEAD`` ranges; a tree SHA would compose
    but resolve to a syntactically valid range that produces garbage
    output.
    """
    module = _load_audit_orchestrator()
    _commit_files(repo, {"seed.ts": "x"}, "seed")
    tree_sha = _git(repo, "rev-parse", "HEAD^{tree}").strip()

    assert module.is_sha_reachable(tree_sha, repo=repo) is False


# ---------------------------------------------------------------------------
# AuditState / Finding / ResolvedFinding / load_state / save_state /
# assign_finding_id
# ---------------------------------------------------------------------------


SAMPLE_BRANCH = "feature/audit-helpers"
SAMPLE_FIRST_RUN_SHA = "abc1234"
SAMPLE_FIRST_RUN_AT = "2026-05-11T15:30:43Z"
SAMPLE_LAST_RUN_SHA = "def5678"
SAMPLE_LAST_RUN_AT = "2026-05-11T15:35:12Z"
# Verdict spellings are source-owned by audit_orchestrator.Verdict; bind once
# at module-load time so the rest of the test module references the canonical
# instances rather than re-typing the literal strings.
_VERDICT_MODULE = _load_audit_orchestrator()
APPROVED_VERDICT = _VERDICT_MODULE.Verdict.APPROVED
REJECTED_VERDICT = _VERDICT_MODULE.Verdict.REJECTED


def _sample_state(module: ModuleType) -> Any:
    """Return a fresh AuditState with one open and one resolved finding.

    Lives at module scope (not a fixture) so individual tests can mutate
    the returned instance without leaking between tests. Return type is
    ``Any`` (not ``audit_orchestrator.AuditState``) because callers reach
    for fields the dataclass exposes; importing the dataclass for static
    typing creates a circular RED-phase dependency since the symbol does
    not exist until the implementation step lands. After GREEN, this
    annotation can be tightened to ``audit_orchestrator.AuditState`` via
    a TYPE_CHECKING import.
    """
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
    """A nonexistent state-file path resolves to ``None``, not an exception.

    The interim agent's Phase 0 step 5 distinguishes "first run on this
    branch" (state file absent) from "re-run" (state file present); the
    helper must signal the first-run case without raising so the caller
    can branch into Phase F instead of halting.
    """
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
    """An on-disk file that fails to parse raises StateFileCorruptError so the
    caller can distinguish 'corrupt' from 'absent' (None) and 'valid' (populated
    AuditState). With atomic save_state the corruption path is unreachable
    in-process; the error remains as a signal for out-of-band tampering."""
    module = _load_audit_orchestrator()
    state_path = tmp_path / "corrupt.md"
    # Frontmatter has a starting delimiter but no closing delimiter; the parser
    # raises ValueError, which load_state wraps as StateFileCorruptError.
    state_path.write_text("---\nbranch: main\n", encoding="utf-8")

    with pytest.raises(module.StateFileCorruptError) as exc_info:
        module.load_state(state_path)

    assert str(state_path) in str(exc_info.value)


def test_save_state_is_atomic_via_temp_then_replace(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """save_state writes to <path>.tmp and then calls os.replace. A failure
    during the rename leaves the prior file's content unchanged — never
    partially overwritten — and the temp file remains on disk holding the
    intended new content."""
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

    # Atomicity contract: the destination is untouched by a failed rename.
    assert state_path.read_text(encoding="utf-8") == prior_content
    # The temp file holds the intended new content, ready to be promoted on
    # the next successful write.
    tmp_file = state_path.with_name(state_path.name + ".tmp")
    assert tmp_file.exists()
    assert SAMPLE_BRANCH in tmp_file.read_text(encoding="utf-8")


def test_state_round_trip_preserves_frontmatter_and_findings(
    tmp_path: pathlib.Path,
) -> None:
    """save_state followed by load_state reproduces the original AuditState.

    The state file is the source of truth for re-run continuity; any
    field that doesn't survive the round-trip would silently corrupt
    the next run's scope or ID assignment.
    """
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    original = _sample_state(module)

    module.save_state(original, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded == original


def test_state_round_trip_preserves_empty_finding_tables(
    tmp_path: pathlib.Path,
) -> None:
    """A state with zero findings round-trips with empty tables intact.

    First-run states with all-pass audits have empty Open and Resolved
    tables; the parser must accept them rather than treating an empty
    table as a parse error.
    """
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
    """Each call returns the next ID in sequence and bumps next_finding_id.

    Sequential assignment is the property the auditor agent's Phase F
    relies on when batch-assigning IDs to a fresh verdict's findings.
    """
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

    The interim agent's monotonic-ID invariant: if f-002 was assigned
    in run 1 and resolved in run 2, run 3 must NOT reuse f-002 for a
    new finding even though its row no longer appears in Open. State
    persists ``next_finding_id`` so the counter survives across runs.

    Geometry deliberately decouples ``next_finding_id`` from any
    max-of-finding-ids quantity so a ``max(open_id) + 1`` mutation
    fails. State has open IDs ``[f-001, f-004]``, resolved IDs
    ``[f-002, f-003]``, and ``next_finding_id=7``. Three competing
    mutations produce three different IDs:

    - counter-driven (correct): ``f-007``
    - max(open) + 1: ``f-005``
    - max(open ∪ resolved) + 1: ``f-005``
    - first gap in [open]: ``f-002``
    - max(resolved) + 1: ``f-004`` (collides with open)

    Asserting ``f-007`` rules out every alternative.
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
    """next_finding_id survives serialization so the counter persists.

    Without this the interim agent's monotonic invariant would only hold
    within a single process; a fresh process loading prior state would
    reset to f-001 and reuse resolved IDs.
    """
    module = _load_audit_orchestrator()
    state_path = tmp_path / "main.md"
    state = _sample_state(module)
    expected_next = state.next_finding_id

    module.save_state(state, state_path)
    reloaded = module.load_state(state_path)

    assert reloaded is not None
    assert reloaded.next_finding_id == expected_next


# ---------------------------------------------------------------------------
# Cell escaping + regression helpers (PRIORITY 2)
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
    """Build a Finding with overridable fields for cell-escaping tests."""
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
    """Build a ResolvedFinding for regression-detection tests."""
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
    """Build an AuditState parameterized by its finding lists."""
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
    """A finding whose root_cause contains ``|`` survives save → load.

    Without cell escaping, the literal ``|`` would split the table row
    into more cells than the schema has columns; load_state would
    either parse the wrong field boundaries or raise.
    """
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
    """A finding whose required_fix contains ``\\n`` survives save → load.

    Without cell escaping, the literal newline would break the table
    row into two visual rows; load_state would parse the second half
    as a separate row (with the wrong column count) or skip it.
    """
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


def test_state_round_trip_preserves_pipe_and_newline_in_same_field(
    tmp_path: pathlib.Path,
) -> None:
    """A field containing both ``|`` and ``\\n`` round-trips intact.

    Tests that the escape order is composable — the forward escape and
    its inverse compose to identity when both special characters
    appear together. A mutation that escapes-then-unescapes in the
    wrong order would corrupt this input.
    """
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
    """No matching (file_line, root_cause) pair returns None.

    The re-run protocol calls this to check whether the current
    finding represents a regression; absence is the normal case and
    must not raise.
    """
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
    """A matching (file_line, root_cause) pair returns the ResolvedFinding.

    The re-run protocol uses the returned identity to reopen the
    finding (preserving its original ID) rather than allocating a new
    one — the core monotonic-ID invariant for regressions.
    """
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
    """Reopening a resolved finding moves it back without a new ID.

    The interim agent's invariant: "A regression — the same root cause
    returning at the same file:line — reopens the original finding by
    moving its row from Resolved to Open and clearing resolved_at.
    Never create a new ID for a regression."
    """
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
    """Resolving an open finding moves it to resolved with the same ID.

    Resolution does not allocate a new ID, so ``next_finding_id`` must
    NOT advance — symmetric with reopen. A mutation that bumps the
    counter on resolve would waste IDs and the round-trip persistence
    of ``next_finding_id`` would carry the spurious bump across runs.
    """
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
# Sanity: tests fail in RED phase before helpers exist
# ---------------------------------------------------------------------------


def test_helpers_under_audit_are_exposed_by_module() -> None:
    """The full helper symbol set must be importable from audit_orchestrator.

    A failure here means the implementation step did not land the helpers,
    not that a behavior test failed; this guard makes the import expectation
    explicit so RED-phase failure is unambiguous.
    """
    module = _load_audit_orchestrator()

    assert hasattr(module, "detect_base_ref")
    assert hasattr(module, "detect_current_branch")
    assert hasattr(module, "branch_slug")
    assert hasattr(module, "RunLock")
    assert hasattr(module, "expand_diff_range")
    assert hasattr(module, "branch_scope")
    assert hasattr(module, "modified_since")
    assert hasattr(module, "is_sha_reachable")
    assert hasattr(module, "AuditState")
    assert hasattr(module, "Finding")
    assert hasattr(module, "ResolvedFinding")
    assert hasattr(module, "load_state")
    assert hasattr(module, "save_state")
    assert hasattr(module, "assign_finding_id")
    assert hasattr(module, "find_resolved_by_identity")
    assert hasattr(module, "reopen_finding")
    assert hasattr(module, "resolve_finding")
    assert hasattr(module, "DetachedHeadError")
    assert hasattr(module, "RunLockError")
    assert hasattr(module, "StateFileCorruptError")
    assert hasattr(module, "Verdict")
