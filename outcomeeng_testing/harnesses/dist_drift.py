"""Temp git repo harness for dist/ drift-reporter scenario tests.

The dist-diff drift reporter (``outcomeeng.distribution.dist_diff``) inspects the
git working tree: it lists ``dist/`` paths that differ from the index and checks
whether ``src/plugins/`` carries uncommitted edits. Exercising that behavior
needs a real repo whose ``dist/`` and ``src/plugins/`` baselines are committed,
so a test can introduce drift and an optional source edit and observe the report.

``dist_drift_repo()`` provisions that repo and tears it down on every exit path.
Exception case: none. This is a real local git repository (L1: git plus tmp
dirs), not a test double. The harness owns resource setup, teardown, and
cleanup; it does not replace the behavior under test.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.orchestration import DIST_ROOT_NAME, SOURCE_PLUGINS_DIR


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@dataclass
class DistDriftRepo:
    """A committed repo plus helpers to introduce dist/ drift and src/ edits.

    ``dist_path`` and ``src_path`` are repo-relative paths to committed baseline
    files under ``dist/`` and ``src/plugins/`` respectively. The helpers rewrite
    those files so the working tree diverges from the index, reproducing the two
    states the reporter discriminates.
    """

    root: Path
    dist_path: Path
    src_path: Path

    def drift_dist(self) -> None:
        """Rewrite the committed dist file so it differs from the index."""
        (self.root / self.dist_path).write_text("drifted\n", encoding="utf-8")

    def edit_src(self) -> None:
        """Rewrite the committed src/plugins file so it shows as uncommitted."""
        (self.root / self.src_path).write_text("edited\n", encoding="utf-8")


@contextmanager
def dist_drift_repo() -> Iterator[DistDriftRepo]:
    """Yield a repo with committed ``dist/`` and ``src/plugins/`` baselines.

    The repo is initialized on ``main`` with one commit holding a baseline file
    under each of ``dist/`` and ``src/plugins/`` and a clean working tree, so the
    reporter sees no drift until a helper introduces it. The whole tree is removed
    on context exit, including on failure.
    """
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _git(repo, "init", "-b", "main")
        _git(repo, "config", "user.email", "test@example.invalid")
        _git(repo, "config", "user.name", "Spec Tree Test")
        # Disable commit signing locally so the seed commit succeeds regardless
        # of a contributor's global commit.gpgsign (no signing key in this repo).
        _git(repo, "config", "commit.gpgsign", "false")
        dist_path = Path(DIST_ROOT_NAME) / "claude" / "example" / "SKILL.md"
        src_path = SOURCE_PLUGINS_DIR / "example" / "skills" / "example" / "SKILL.md"
        for rel in (dist_path, src_path):
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("baseline\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "baseline")
        yield DistDriftRepo(root=repo, dist_path=dist_path, src_path=src_path)


__all__ = ["DistDriftRepo", "dist_drift_repo"]
