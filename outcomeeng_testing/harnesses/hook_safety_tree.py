"""Test infrastructure: the temporary hook tree the hook-safety validator scans.

The harness owns lifecycle only: the temporary root, the runtime and plugin
layout (every name and the encoding come from the validator's source owner,
``outcomeeng.validation.hook_contract``, so a fixture lands exactly where the
validator looks), copying a fixture directory by path into a runtime tree, and
the default-root scan with its working directory. It holds no case value, accepts
no expected result, calls no assertion API, and returns no verdict.

Every case is an inert whole-payload fixture directory under
``outcomeeng_testing/fixtures/hook_safety/<group>--<instance>/``; each holds the
tree the validator scans below a runtime root, ``<plugin>/hooks/hooks.json``. The
directory name states the one clause instance the fixture varies.

The one payload the harness assembles is the blocking-event re-key: it takes the
handler list from one fixture's ``hooks.json`` and places it under an event key the
caller supplies. The handlers come from the fixture file and the key from the
source-owned ``BLOCKING_EVENTS`` set the hook-safety node's blocking-events clause
parametrizes over.

Exception case: none.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation.hook_contract import (
    HOOKS_CONFIG_ENCODING,
    HOOKS_CONFIG_FILE,
    HOOKS_DIRECTORY,
    HOOKS_KEY,
    PRE_WRITE_PLUGIN,
)
from outcomeeng.validation.hook_safety import main

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
HOOK_SAFETY_FIXTURES: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "hook_safety"
)
GROUP_SEPARATOR: Final = "--"


class FixtureGroup(StrEnum):
    """The directory-name prefix that gathers the fixtures of one clause."""

    SESSION_START = "session-start"
    UNRECOGNIZED_EVENT = "unrecognized-event"
    MISSING_TIMEOUT = "missing-timeout"
    BARE_SCRIPT = "bare-script"
    GUARDED_SCRIPT = "guarded-script"
    PINNED_CACHE = "pinned-cache"
    PRE_WRITE_EXCEPTION = "pre-write-exception"
    PRE_WRITE_DEVIATION = "pre-write-deviation"


@dataclass(frozen=True)
class FixtureCase:
    """One fixture directory: a name stating the clause instance and its path."""

    name: str
    path: Path

    @property
    def plugins(self) -> tuple[str, ...]:
        """Return the plugin directory names the fixture ships."""
        return tuple(sorted(child.name for child in self.path.iterdir()))


def case_id(case: FixtureCase) -> str:
    """Return the parametrize id of one fixture case: its directory name."""
    return case.name


def fixture_cases(*groups: FixtureGroup) -> tuple[FixtureCase, ...]:
    """Return every fixture of the given groups, ordered by name.

    A group with no fixture raises, so a parametrization never vanishes silently.
    """
    cases: list[FixtureCase] = []
    for group in groups:
        found = sorted(
            child
            for child in HOOK_SAFETY_FIXTURES.iterdir()
            if child.is_dir() and child.name.startswith(f"{group}{GROUP_SEPARATOR}")
        )
        if not found:
            raise FileNotFoundError(f"no hook-safety fixture of group {group.value}")
        cases.extend(FixtureCase(name=child.name, path=child) for child in found)
    return tuple(cases)


@dataclass(frozen=True)
class ScanReport:
    """The observed exit code and error stream of one ``main`` scan."""

    exit_code: int
    stderr: str


@dataclass(frozen=True)
class HookTree:
    """A temporary directory tree holding plugin hook configs per runtime tree."""

    root: Path

    def runtime_root(self, runtime: str) -> Path:
        """Return the directory of one generated runtime tree."""
        return self.root / runtime

    def hooks_path(self, runtime: str, plugin: str) -> Path:
        """Return where one plugin's hook config lives in one runtime tree."""
        return self.runtime_root(runtime) / plugin / HOOKS_DIRECTORY / HOOKS_CONFIG_FILE

    def install(self, runtime: str, case: FixtureCase) -> None:
        """Copy one fixture directory by path into one runtime tree."""
        shutil.copytree(case.path, self.runtime_root(runtime), dirs_exist_ok=True)

    def install_shipped(self, runtime: str) -> None:
        """Copy the shipped spec-tree plugin's hook config of one runtime tree by path."""
        source = (
            REPO_ROOT / runtime / PRE_WRITE_PLUGIN / HOOKS_DIRECTORY / HOOKS_CONFIG_FILE
        )
        target = self.hooks_path(runtime, PRE_WRITE_PLUGIN)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def install_rekeyed(self, runtime: str, case: FixtureCase, event: str) -> None:
        """Place a fixture's handler list under ``event`` in one runtime tree.

        The handlers are read from the fixture's ``hooks.json``; ``event`` is the
        only value assembled here.
        """
        for source in sorted(
            case.path.glob(f"*/{HOOKS_DIRECTORY}/{HOOKS_CONFIG_FILE}")
        ):
            payload = json.loads(source.read_text(encoding=HOOKS_CONFIG_ENCODING))
            (blocks,) = payload[HOOKS_KEY].values()
            target = self.hooks_path(runtime, source.parents[1].name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps({HOOKS_KEY: {event: blocks}}),
                encoding=HOOKS_CONFIG_ENCODING,
            )

    def scan_default_roots(self, argv: Sequence[str] = ()) -> ScanReport:
        """Run ``main`` with this tree's root as the working directory; report the outcome.

        The harness enters the root before the scan and restores the prior
        working directory afterwards, so a default-root scan resolves its
        relative runtime trees beneath this tree.
        """
        previous = Path.cwd()
        stderr = io.StringIO()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stderr(stderr):
                exit_code = main(list(argv))
        finally:
            os.chdir(previous)
        return ScanReport(exit_code=exit_code, stderr=stderr.getvalue())


@contextmanager
def hook_tree() -> Iterator[HookTree]:
    """Yield an empty temporary hook tree and release it on exit."""
    with TemporaryDirectory() as directory:
        yield HookTree(Path(directory))


__all__ = [
    "HOOK_SAFETY_FIXTURES",
    "FixtureCase",
    "FixtureGroup",
    "HookTree",
    "ScanReport",
    "case_id",
    "fixture_cases",
    "hook_tree",
]
