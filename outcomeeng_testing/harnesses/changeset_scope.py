"""Test harness for the changeset-scope skill's git-derivation module.

Exposes:

- An importlib loader for ``changeset_scope.py``. The module ships under a
  runtime-substituted plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- ``build_stale_local_base_repo``. Constructs a git repository reproducing the
  multi-worktree staleness bug: the feature branch contains a commit that has
  been merged into ``origin/<base>`` while the local base branch ref lags behind
  it. Scoping against the local ref re-includes the merged commit; scoping
  against the remote-tracking ref excludes it.
- ``build_base_advanced_after_branch_repo``. Constructs a diverged repository
  where the base gains a commit after the feature branches, distinguishing a
  merge-base three-dot diff from a two-dot tip-to-tip diff.
- ``build_repo_without_origin``. A repository with a branch and a commit but no
  ``refs/remotes/origin/HEAD`` symbolic ref, for the base-ref fallback paths.
- ``build_repo_with_modified_spaced_note``. A repository whose only working-tree
  change is a committed-then-modified coordination note at a path containing a
  space, for the porcelain-quoting case.

The harness owns Git lifecycle, temporary resources, process isolation, and
runtime handles. Generated branch and path inputs come from the changeset-scope
generator, while executed test files call production behavior and own every
outcome assertion.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import islice
from tempfile import TemporaryDirectory
from types import ModuleType

from outcomeeng_testing.generators.changeset_scope import (
    ChangesetScopeCase,
    changeset_scope_cases,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHANGESET_SCOPE_SCRIPTS_DIR = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "changeset-scope-standards"
    / "scripts"
)
CHANGESET_SCOPE_MODULE_PATH = CHANGESET_SCOPE_SCRIPTS_DIR / "changeset_scope.py"
CHANGESET_SCOPE_CONTRACT_MODULE_PATH = (
    CHANGESET_SCOPE_SCRIPTS_DIR / "changeset_scope_contract.py"
)
MERGE_CLASSIFIER_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "merge"
    / "scripts"
    / "classify_changeset.py"
)
MERGE_CONTRACT_MODULE_PATH = MERGE_CLASSIFIER_MODULE_PATH.with_name("merge_contract.py")
COHERENCE_SCOPE_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "audit-changeset-coherence"
    / "scripts"
    / "resolve_scope.py"
)
CHANGESET_SCOPE_FIXTURES_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "changeset_scope"
)
SPACED_NOTE_FIXTURE_DIR = CHANGESET_SCOPE_FIXTURES_DIR / "spaced-note"
CHANGESET_SCOPE_CASE_COUNT = 3


def _fixture_file(scenario: pathlib.Path, role: str) -> pathlib.Path:
    role_root = scenario / role
    files = tuple(path for path in role_root.rglob("*") if path.is_file())
    if len(files) != 1:
        raise RuntimeError(
            f"Expected one fixture file under {role_root}, found {files}"
        )
    return files[0]


def _fixture_relative_path(scenario: pathlib.Path, role: str) -> str:
    return _fixture_file(scenario, role).relative_to(scenario / role).as_posix()


SPACED_NOTE_PATH = _fixture_relative_path(SPACED_NOTE_FIXTURE_DIR, "committed")


def generated_changeset_scope_cases() -> tuple[ChangesetScopeCase, ...]:
    """Return the harness-configured number of reproducible generated cases."""
    return tuple(islice(changeset_scope_cases(), CHANGESET_SCOPE_CASE_COUNT))


def _first_changeset_scope_case() -> ChangesetScopeCase:
    return next(changeset_scope_cases())


@dataclass(frozen=True)
class TemporaryChangesetScope:
    """Invocation-unique paths for changeset-scope tests."""

    repo: pathlib.Path
    empty_state_dir: pathlib.Path


@contextmanager
def temporary_changeset_scope() -> Iterator[TemporaryChangesetScope]:
    """Yield empty scenario paths and remove their temporary root on exit."""
    with TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        repo = root / "repo"
        repo.mkdir()
        yield TemporaryChangesetScope(
            repo=repo,
            empty_state_dir=root / "empty-state",
        )


def _load_source_module(name: str, path: pathlib.Path) -> ModuleType:
    """Load one shipped source module through its file boundary and cache it."""
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_changeset_scope_module() -> ModuleType:
    """Load the ``changeset_scope`` implementation through its shipped file."""
    return _load_source_module("changeset_scope", CHANGESET_SCOPE_MODULE_PATH)


def load_changeset_scope_contract_module() -> ModuleType:
    """Load the source-owned changeset contract independently of its implementation."""
    return _load_source_module(
        "changeset_scope_contract", CHANGESET_SCOPE_CONTRACT_MODULE_PATH
    )


def load_merge_classifier_module() -> ModuleType:
    """Load the merge changeset classifier through its shipped file boundary."""
    return _load_source_module("classify_changeset", MERGE_CLASSIFIER_MODULE_PATH)


def load_merge_contract_module() -> ModuleType:
    """Load the source-owned merge contract independently of its classifier."""
    return _load_source_module("merge_contract", MERGE_CONTRACT_MODULE_PATH)


def load_coherence_scope_module() -> ModuleType:
    """Load the coherence-audit scope resolver through its shipped file boundary."""
    return _load_source_module("resolve_scope", COHERENCE_SCOPE_MODULE_PATH)


CHANGESET_SCOPE = load_changeset_scope_module()
CHANGESET_SCOPE_CONTRACT = load_changeset_scope_contract_module()
MERGE_CLASSIFIER = load_merge_classifier_module()
MERGE_CONTRACT = load_merge_contract_module()
COHERENCE_SCOPE = load_coherence_scope_module()


def _git(repo: pathlib.Path, *args: str, cwd: pathlib.Path | None = None) -> str:
    """Run a git command with isolated config, returning stripped stdout.

    Global and system config are suppressed and a fixed identity is injected so
    the call does not inherit operator settings or commit signing.
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
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell, args from the harness
        ["git", *args],
        cwd=cwd if cwd is not None else repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _commit_file(repo: pathlib.Path, name: str, content: str, message: str) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)


def _fixture_text(scenario: pathlib.Path, role: str) -> str:
    return _fixture_file(scenario, role).read_text(encoding="utf-8")


def _initialize_changeset_repo(
    repo: pathlib.Path,
    scenario: ChangesetScopeCase | None = None,
) -> ChangesetScopeCase:
    """Create the shared initial commit for a changeset-scope scenario."""
    scenario = scenario or _first_changeset_scope_case()
    _git(
        repo,
        "init",
        "-q",
        "-b",
        scenario.base_branch,
        str(repo),
        cwd=pathlib.Path.cwd(),
    )
    _git(repo, "config", "commit.gpgsign", "false")
    _commit_file(
        repo,
        scenario.initial_file,
        scenario.initial_file,
        scenario.initial_file,
    )
    return scenario


def _publish_origin_base(
    repo: pathlib.Path,
    scenario: ChangesetScopeCase,
    commit_oid: str,
) -> None:
    """Point the synthetic origin base and origin/HEAD refs at a commit."""
    _git(
        repo,
        "update-ref",
        f"refs/remotes/origin/{scenario.base_branch}",
        commit_oid,
    )
    _git(
        repo,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        f"refs/remotes/origin/{scenario.base_branch}",
    )


@dataclass(frozen=True)
class StaleBaseRepo:
    """A repo where the feature branch holds a commit already merged to origin.

    ``base_ref`` is the bare base-branch name. ``merged_file`` was committed on
    the base and is present on ``origin/<base_ref>`` (current) but absent from
    the lagging local base ref. ``feature_file`` is the feature branch's own
    change. A changeset scoped against ``origin/<base_ref>`` contains
    ``feature_file`` only; one scoped against the stale local ref also contains
    ``merged_file``.
    """

    repo: pathlib.Path
    base_ref: str
    feature_branch: str
    merged_file: str
    feature_file: str
    working_file: str


@dataclass(frozen=True)
class BaseAdvancedRepo:
    """A repo whose base gains a commit after the feature branches."""

    repo: pathlib.Path
    base_ref: str
    feature_branch: str
    base_file: str
    feature_file: str


def build_stale_local_base_repo(
    repo: pathlib.Path,
    scenario: ChangesetScopeCase | None = None,
) -> StaleBaseRepo:
    """Build the staleness scenario and return its handle.

    Sequence: initial commit A on ``main``; merged commit M on ``main``; point
    ``refs/remotes/origin/{main,HEAD}`` at A+M; branch the feature off A+M so it
    contains M; add feature commit F; reset the local ``main`` ref back to A so
    it lags ``origin/main`` by the merged commit.
    """
    scenario = _initialize_changeset_repo(repo, scenario)
    initial_sha = _git(repo, "rev-parse", "HEAD")

    _commit_file(
        repo,
        scenario.merged_file,
        scenario.merged_file,
        scenario.merged_file,
    )
    advanced_sha = _git(repo, "rev-parse", "HEAD")

    # origin/main (and origin/HEAD) point at the advanced base A+M.
    _publish_origin_base(repo, scenario, advanced_sha)

    # Feature branches off A+M (so it contains the merged commit) and adds F.
    _git(repo, "switch", "-q", "-c", scenario.feature_branch)
    _commit_file(
        repo,
        scenario.feature_file,
        scenario.feature_file,
        scenario.feature_file,
    )

    # The local base ref lags origin by the merged commit.
    _git(repo, "update-ref", f"refs/heads/{scenario.base_branch}", initial_sha)

    return StaleBaseRepo(
        repo=repo,
        base_ref=scenario.base_branch,
        feature_branch=scenario.feature_branch,
        merged_file=scenario.merged_file,
        feature_file=scenario.feature_file,
        working_file=scenario.working_file,
    )


def build_base_advanced_after_branch_repo(
    repo: pathlib.Path,
    scenario: ChangesetScopeCase | None = None,
) -> BaseAdvancedRepo:
    """Build a topology that distinguishes three-dot from two-dot diff scope.

    Sequence: initial commit A on the base; branch the feature from A and add F;
    return to the base and add M; point ``origin/<base>`` at A+M; switch back to
    the feature at A+F. A three-dot diff starts from merge base A and contains F
    only, while a two-dot diff between A+M and A+F also contains M.
    """
    scenario = _initialize_changeset_repo(repo, scenario)

    _git(repo, "switch", "-q", "-c", scenario.feature_branch)
    _commit_file(
        repo,
        scenario.feature_file,
        scenario.feature_file,
        scenario.feature_file,
    )

    _git(repo, "switch", "-q", scenario.base_branch)
    _commit_file(
        repo,
        scenario.merged_file,
        scenario.merged_file,
        scenario.merged_file,
    )
    _publish_origin_base(repo, scenario, _git(repo, "rev-parse", "HEAD"))
    _git(repo, "switch", "-q", scenario.feature_branch)

    return BaseAdvancedRepo(
        repo=repo,
        base_ref=scenario.base_branch,
        feature_branch=scenario.feature_branch,
        base_file=scenario.merged_file,
        feature_file=scenario.feature_file,
    )


def build_repo_without_origin(
    repo: pathlib.Path,
    scenario: ChangesetScopeCase | None = None,
) -> str:
    """Build a repo with a branch and a commit but no origin/HEAD symbolic ref.

    Returns the generated branch name while leaving ``origin/HEAD`` absent so
    callers can exercise the production error path.
    """
    scenario = _initialize_changeset_repo(repo, scenario)
    return scenario.base_branch


@dataclass(frozen=True)
class SpacedNoteRepo:
    """A repo whose only working-tree change is a modified spaced-path note.

    ``note_path`` is a coordination note (``PLAN.md``) under a directory whose
    name contains a space. It is committed first (so git lists the individual
    file rather than collapsing an untracked directory) and then modified, so it
    appears as a working-tree change. ``git status --porcelain`` without ``-z``
    C-quotes the spaced path; consumers must use ``-z`` to recover the unquoted
    name that matches ``git diff --name-only`` output.
    """

    repo: pathlib.Path
    note_path: str


def build_repo_with_modified_spaced_note(repo: pathlib.Path) -> SpacedNoteRepo:
    """Build a repo with a committed-then-modified coordination note at a spaced path.

    Sequence: initialise the repo with a base commit (no origin needed — the
    working-tree query does not read it); create the spaced directory; commit
    the note so git tracks the individual file; modify it so it surfaces as a
    working-tree change. Returns the handle carrying the note's unquoted path.
    """
    build_repo_without_origin(repo)
    (repo / "spx dir").mkdir()
    _commit_file(
        repo,
        SPACED_NOTE_PATH,
        _fixture_text(SPACED_NOTE_FIXTURE_DIR, "committed"),
        "add spaced note",
    )
    (repo / SPACED_NOTE_PATH).write_text(
        _fixture_text(SPACED_NOTE_FIXTURE_DIR, "working"),
        encoding="utf-8",
    )
    return SpacedNoteRepo(repo=repo, note_path=SPACED_NOTE_PATH)


@contextmanager
def stale_local_base_repo(
    scenario: ChangesetScopeCase | None = None,
) -> Iterator[StaleBaseRepo]:
    """Yield a generated stale-base repository and clean it up on exit."""
    with temporary_changeset_scope() as paths:
        yield build_stale_local_base_repo(paths.repo, scenario)


@contextmanager
def base_advanced_after_branch_repo(
    scenario: ChangesetScopeCase | None = None,
) -> Iterator[BaseAdvancedRepo]:
    """Yield a generated diverged repository and clean it up on exit."""
    with temporary_changeset_scope() as paths:
        yield build_base_advanced_after_branch_repo(paths.repo, scenario)


@contextmanager
def repo_without_origin(
    scenario: ChangesetScopeCase | None = None,
) -> Iterator[pathlib.Path]:
    """Yield a generated repository with no remote default ref."""
    with temporary_changeset_scope() as paths:
        build_repo_without_origin(paths.repo, scenario)
        yield paths.repo


@contextmanager
def modified_spaced_note_repo() -> Iterator[SpacedNoteRepo]:
    """Yield a repository containing one modified spaced-path coordination note."""
    with temporary_changeset_scope() as paths:
        yield build_repo_with_modified_spaced_note(paths.repo)


@contextmanager
def canonical_merge_changeset(
    scenario: ChangesetScopeCase | None = None,
) -> Iterator[StaleBaseRepo]:
    """Yield a stale-base repo with an additional working-tree change."""
    with stale_local_base_repo(scenario) as stale:
        working_path = stale.repo / stale.working_file
        working_path.parent.mkdir(parents=True, exist_ok=True)
        working_path.write_text(stale.working_file, encoding="utf-8")
        yield stale


@dataclass(frozen=True)
class BranchCollisionState:
    """Generated branch inputs and state directories for slug assertions."""

    feature_branch: str
    state_dir: pathlib.Path
    empty_state_dir: pathlib.Path


@contextmanager
def branch_collision_state(
    scenario: ChangesetScopeCase | None = None,
) -> Iterator[BranchCollisionState]:
    """Yield generated branches with a conflicting state file already present."""
    with temporary_changeset_scope() as paths:
        scenario = scenario or _first_changeset_scope_case()
        base_slug = scenario.feature_branch.replace(
            CHANGESET_SCOPE_CONTRACT.BRANCH_REF_PATH_SEPARATOR,
            CHANGESET_SCOPE_CONTRACT.BRANCH_SLUG_PATH_SUBSTITUTE,
        )
        write_branch_state_file(paths.repo, base_slug, scenario.base_branch)
        yield BranchCollisionState(
            feature_branch=scenario.feature_branch,
            state_dir=paths.repo,
            empty_state_dir=paths.empty_state_dir,
        )


def git_commit_oid(repo: pathlib.Path, ref: str) -> str:
    """Resolve a ref through real Git for an independent commit-OID oracle."""
    contract = load_changeset_scope_contract_module()
    return _git(
        repo,
        "rev-parse",
        "--verify",
        "--quiet",
        f"{ref}{contract.COMMIT_PEEL_SUFFIX}",
    )


def checkout_branch(repo: pathlib.Path, branch: str) -> None:
    """Switch ``repo`` to an existing branch.

    Lets a scenario resolve a branch that is not the checked-out one, which
    distinguishes a range composed against the named ref from one composed
    against ``HEAD``.
    """
    _git(repo, "switch", "-q", branch)


def git_three_dot_scope(repo: pathlib.Path, ref: str) -> tuple[str, ...]:
    """Return Git's merge-base scope for a caller-supplied ref."""
    contract = load_changeset_scope_contract_module()
    output = _git(repo, "diff", "--name-only", f"{ref}...{contract.HEAD_REF}")
    return tuple(output.splitlines())


def run_merge_classifier(repo: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """Run the shipped merge classifier and return its observable process result."""
    return subprocess.run(
        (sys.executable, str(MERGE_CLASSIFIER_MODULE_PATH)),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def run_coherence_scope(
    repo: pathlib.Path, scope: str
) -> subprocess.CompletedProcess[str]:
    """Run the shipped coherence scope resolver and return its process result."""
    return subprocess.run(
        (sys.executable, str(COHERENCE_SCOPE_MODULE_PATH), scope),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def contains_python_traceback(stderr: str) -> bool:
    """Report whether Python emitted its standard uncaught-exception header."""
    return "Traceback (most recent call last):" in stderr


def detach_head(repo: pathlib.Path) -> None:
    """Put ``repo`` on a detached HEAD so ``detect_current_branch`` raises.

    Resolves the current commit and checks it out by SHA, detaching HEAD
    from the branch ref.
    """
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)


def write_branch_state_file(
    state_dir: pathlib.Path, slug: str, branch: str
) -> pathlib.Path:
    """Write a state file at ``state_dir/<slug>.md`` recording ``branch``.

    The file carries the YAML frontmatter ``branch_slug`` reads for
    state-collision disambiguation: a ``branch:`` key fenced by
    ``changeset_scope.FRONTMATTER_DELIMITER``. Returns the written path.
    """
    delimiter = load_changeset_scope_module().FRONTMATTER_DELIMITER
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / f"{slug}.md"
    path.write_text(f"{delimiter}\nbranch: {branch}\n{delimiter}\n", encoding="utf-8")
    return path
