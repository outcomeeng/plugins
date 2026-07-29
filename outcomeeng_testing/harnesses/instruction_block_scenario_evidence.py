"""Scenario fixture setup for the instruction-block CLI edge and shared-region reconcile.

This module builds the resources the scenarios need — templates and a git repository whose root
files carry a committed shared region at a fixed date. It asserts nothing: the linked scenario
test owns every predicate, so inverting any scenario's expected behavior changes that test and
nothing here.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


def scenario_template(
    tmp_path: pathlib.Path, *, extra_section: bool = False
) -> pathlib.Path:
    """Write the installed-version template the scenarios render from."""
    return harness.write_template(
        tmp_path, harness.NEW_VERSION, extra_section=extra_section
    )


def init_repo_with_committed_shared_region(
    tmp_path: pathlib.Path,
    *,
    claude_region: str,
    agents_region: str,
    timestamp: int,
) -> pathlib.Path:
    """Create a git repository whose two root files commit their shared region at ``timestamp``."""
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    harness.write_both_root_files_with_shared_region(
        MODULE,
        repo,
        languages=(harness.LANG_PRIMARY,),
        version=harness.NEW_VERSION,
        claude_region=claude_region,
        agents_region=agents_region,
    )
    harness.git_commit_at(
        repo, timestamp, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )
    return repo


def diverge_region_and_commit(
    repo: pathlib.Path, filename: str, body: str, timestamp: int
) -> None:
    """Replace ``filename``'s shared-region body and commit only that file at ``timestamp``."""
    path = repo / filename
    path.write_text(
        MODULE.set_shared_region(
            path.read_text(encoding="utf-8"), harness.SHARED_REGION_NAME, body
        ),
        encoding="utf-8",
    )
    harness.git_commit_at(repo, timestamp, filename)


def region_body(repo: pathlib.Path, filename: str) -> str:
    """Return ``filename``'s current shared-region body."""
    return MODULE.parse_shared_regions((repo / filename).read_text(encoding="utf-8"))[
        harness.SHARED_REGION_NAME
    ]
