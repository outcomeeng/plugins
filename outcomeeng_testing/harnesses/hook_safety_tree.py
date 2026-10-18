"""Test infrastructure: the temporary hook tree the hook-safety validator scans.

The harness owns the whole lifecycle of a throwaway generated-tree fixture: the
temporary root, the runtime directory, the plugin directory, the
``hooks/hooks.json`` location, the JSON write with its encoding, the default
handler command and timeout, and the working directory of a default-root scan.
Every layout name and the encoding come from the validator's source owner
(``outcomeeng.validation.hook_contract``), so a fixture lands exactly where the
validator looks. It writes each whole ``hooks.json`` payload itself and hands the
test the path; it accepts no expected result, calls no assertion API, and
returns no verdict.

Exception case: none.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation.hook_contract import (
    CODEX_RUNTIME_TREE,
    COMMAND_KEY,
    HOOKS_CONFIG_ENCODING,
    HOOKS_CONFIG_FILE,
    HOOKS_DIRECTORY,
    HOOKS_KEY,
    MATCHER_KEY,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_COMMAND_CODEX,
    PRE_WRITE_EMPTY_RESULT,
    SESSION_START_EVENT,
    TIMEOUT_KEY,
)
from outcomeeng.validation.hook_safety import main
from outcomeeng_testing.generators.hook_safety import pre_write_matcher

# The harness-owned handler every fixture starts from: a command-shape-clean
# command with an explicit timeout, so a fixture's only violation is the one
# its builder introduces.
DEFAULT_HANDLER_COMMAND: Final = f"echo '{PRE_WRITE_EMPTY_RESULT}'"
DEFAULT_HANDLER_TIMEOUT: Final = 5
DEFAULT_MATCHER: Final = ""


@dataclass(frozen=True)
class ScanReport:
    """The observed exit code and error stream of one ``main`` scan."""

    exit_code: int
    stderr: str


def hook_config(
    event: str,
    *,
    command: str = DEFAULT_HANDLER_COMMAND,
    timeout: int | None = DEFAULT_HANDLER_TIMEOUT,
    matcher: str | None = DEFAULT_MATCHER,
    entries: int = 1,
    handlers: int = 1,
) -> Mapping[str, object]:
    """Build a whole ``hooks.json`` payload registering handlers on one event.

    A ``None`` timeout omits the key; a ``None`` matcher omits the key.
    """
    handler: dict[str, object] = {COMMAND_KEY: command}
    if timeout is not None:
        handler[TIMEOUT_KEY] = timeout
    block: dict[str, object] = {
        HOOKS_KEY: [dict(handler) for _ in range(handlers)],
    }
    if matcher is not None:
        block[MATCHER_KEY] = matcher
    return {HOOKS_KEY: {event: [dict(block) for _ in range(entries)]}}


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

    def write_hooks(
        self, runtime: str, plugin: str, config: Mapping[str, object]
    ) -> Path:
        """Write one plugin's hook config into one runtime tree; return its path."""
        path = self.hooks_path(runtime, plugin)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config), encoding=HOOKS_CONFIG_ENCODING)
        return path

    def write_event_hook(
        self,
        runtime: str,
        plugin: str,
        event: str,
        *,
        command: str = DEFAULT_HANDLER_COMMAND,
        timeout: int | None = DEFAULT_HANDLER_TIMEOUT,
        matcher: str | None = DEFAULT_MATCHER,
        handlers: int = 1,
    ) -> Path:
        """Write a payload registering the default handler on ``event``; return its path."""
        return self.write_hooks(
            runtime,
            plugin,
            hook_config(
                event,
                command=command,
                timeout=timeout,
                matcher=matcher,
                handlers=handlers,
            ),
        )

    def write_session_start_hook(
        self,
        runtime: str,
        plugin: str,
        *,
        command: str = DEFAULT_HANDLER_COMMAND,
        timeout: int | None = DEFAULT_HANDLER_TIMEOUT,
        matcher: str | None = DEFAULT_MATCHER,
    ) -> Path:
        """Write a payload registering a handler on the SessionStart event."""
        return self.write_event_hook(
            runtime,
            plugin,
            SESSION_START_EVENT,
            command=command,
            timeout=timeout,
            matcher=matcher,
        )

    def write_pre_write_hook(
        self,
        runtime: str,
        plugin: str,
        *,
        matcher: str | None = None,
        command: str | None = None,
        event: str = PRE_TOOL_USE_EVENT,
        entries: int = 1,
        handlers: int = 1,
    ) -> Path:
        """Write a payload shaped as the pre-write exception, with overridable parts.

        The defaults are the source-owned exception for ``runtime``: the exact
        Write and Edit matcher and the runtime's pre-write command. A ``None``
        override keeps the default; pass ``matcher=""`` for an empty matcher.
        """
        default_command = (
            PRE_WRITE_COMMAND_CODEX
            if runtime == CODEX_RUNTIME_TREE
            else PRE_WRITE_COMMAND_CLAUDE
        )
        return self.write_hooks(
            runtime,
            plugin,
            hook_config(
                event,
                command=default_command if command is None else command,
                matcher=pre_write_matcher() if matcher is None else matcher,
                entries=entries,
                handlers=handlers,
            ),
        )

    def write_matcherless_pre_write_hook(self, runtime: str, plugin: str) -> Path:
        """Write the pre-write exception with its matcher key omitted."""
        command = (
            PRE_WRITE_COMMAND_CODEX
            if runtime == CODEX_RUNTIME_TREE
            else PRE_WRITE_COMMAND_CLAUDE
        )
        return self.write_hooks(
            runtime,
            plugin,
            hook_config(PRE_TOOL_USE_EVENT, command=command, matcher=None),
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

    def subtree(self, name: str) -> HookTree:
        """Return an isolated tree rooted in a named directory beneath this one."""
        return HookTree(self.root / name)


@contextmanager
def hook_tree() -> Iterator[HookTree]:
    """Yield an empty temporary hook tree and release it on exit."""
    with TemporaryDirectory() as directory:
        yield HookTree(Path(directory))


__all__ = [
    "DEFAULT_HANDLER_COMMAND",
    "DEFAULT_HANDLER_TIMEOUT",
    "DEFAULT_MATCHER",
    "HookTree",
    "ScanReport",
    "hook_config",
    "hook_tree",
]
