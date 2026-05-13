"""Scenario tests for the git and scope helpers in ``audit_orchestrator``.

The ``/auditing`` skill's Phase 0 delegates to these helpers so the
deterministic computations stay out of skill prose:

- ``detect_base_ref`` — derives the bare base-branch name from
  ``refs/remotes/origin/HEAD`` (defaults to ``main`` when no remote is
  configured).
- ``expand_diff_range`` — runs ``git diff --name-only <range> -- <patterns>``
  and returns the resulting file list.
- ``branch_scope`` — returns the files this branch changed relative to
  ``origin/<base_ref>``, composing the three-dot diff range so commits
  that landed on the base branch after this feature branch was cut are
  excluded from the scope.

``compute_scope_hash`` is covered by ``test_auditing.property.l1.py``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
from types import ModuleType

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

    Without prefix stripping the composed ref would be
    ``origin/refs/remotes/origin/main...HEAD`` and git would halt the
    orchestrator before any audit ran.
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
# Module surface
# ---------------------------------------------------------------------------


def test_helpers_under_audit_are_exposed_by_module() -> None:
    """The git/scope helpers must be importable from ``audit_orchestrator``."""
    module = _load_audit_orchestrator()

    assert hasattr(module, "compute_scope_hash")
    assert hasattr(module, "expand_diff_range")
    assert hasattr(module, "branch_scope")
    assert hasattr(module, "uncommitted_scope")
    assert hasattr(module, "detect_base_ref")


# ---------------------------------------------------------------------------
# uncommitted_scope
# ---------------------------------------------------------------------------


def test_uncommitted_scope_includes_untracked_files(repo: pathlib.Path) -> None:
    """A new file that has not been ``git add``-ed is still in scope.

    ``git diff --name-only HEAD`` lists modified-and-staged files only — it
    never reports untracked files. Without ``uncommitted_scope`` the
    orchestrator's no-explicit-scope path would return an empty list for
    a developer who created a new file and ran the audit before staging
    it, halting with ``no scope detected``. The helper closes that gap
    by unioning ``git diff HEAD`` with
    ``git ls-files --others --exclude-standard``.
    """
    module = _load_audit_orchestrator()
    (repo / "fresh.ts").write_text("brand new", encoding="utf-8")

    files = module.uncommitted_scope(patterns=["*.ts"], repo=repo)

    assert files == ["fresh.ts"]


def test_uncommitted_scope_includes_modified_staged_and_untracked(
    repo: pathlib.Path,
) -> None:
    """All three working-tree categories appear in the same scope.

    Modified files (in ``git diff HEAD`` but not staged), staged files
    (in ``git diff HEAD``), and untracked files (in ``git ls-files
    --others``) all belong to "what the developer has changed since the
    last commit" and must therefore all appear in the no-explicit-scope
    audit.
    """
    module = _load_audit_orchestrator()
    _commit_files(repo, {"committed.ts": "v1\n"}, "seed")
    # Modify a committed file (not staged).
    (repo / "committed.ts").write_text("v2\n", encoding="utf-8")
    # Stage a new file.
    (repo / "staged.ts").write_text("staged content\n", encoding="utf-8")
    _git(repo, "add", "staged.ts")
    # Leave a third file untracked.
    (repo / "untracked.ts").write_text("untracked content\n", encoding="utf-8")

    files = module.uncommitted_scope(repo=repo)

    assert sorted(files) == ["committed.ts", "staged.ts", "untracked.ts"]


def test_uncommitted_scope_respects_gitignore(repo: pathlib.Path) -> None:
    """Files matched by ``.gitignore`` are excluded from the scope.

    ``git ls-files --others --exclude-standard`` is the
    ``standard``-exclusion variant — it honors ``.gitignore``,
    ``.git/info/exclude``, and the user's global excludesfile. A
    generated artefact (build output, virtualenv) sitting next to the
    source must not pollute the scope.
    """
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
    """A clean working tree (no diff, no untracked files) yields ``[]``.

    Mirrors the orchestrator's no-scope-detected halt condition: nothing
    to audit, empty list returned.
    """
    module = _load_audit_orchestrator()

    files = module.uncommitted_scope(repo=repo)

    assert files == []
