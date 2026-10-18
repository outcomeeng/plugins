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
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation.hook_contract import (
    CLAUDE_PLUGIN_ROOT_TOKEN,
    CODEX_RUNTIME_TREE,
    COMMAND_KEY,
    HOOKS_CONFIG_ENCODING,
    HOOKS_CONFIG_FILE,
    HOOKS_DIRECTORY,
    HOOKS_KEY,
    MATCHER_KEY,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_ADAPTER_INTERPRETER,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_COMMAND_CODEX,
    PRE_WRITE_EMPTY_RESULT,
    PRE_WRITE_KILL_SWITCH,
    PRE_WRITE_MATCHER_SEPARATOR,
    PRE_WRITE_PLUGIN,
    PRE_WRITE_TOOLS,
    SESSION_START_EVENT,
    SUBSTITUTED_PATH_TOKENS,
    TIMEOUT_KEY,
)
from outcomeeng.validation.hook_safety import BLOCKING_EVENTS, main

# The harness-owned handler every fixture starts from: a command-shape-clean
# command with an explicit timeout, so a fixture's only violation is the one
# its builder introduces.
DEFAULT_HANDLER_COMMAND: Final = f"echo '{PRE_WRITE_EMPTY_RESULT}'"
DEFAULT_HANDLER_TIMEOUT: Final = 5
DEFAULT_MATCHER: Final = ""

# Incidental values a case needs but no validator rule owns, supplied as handles
# so a test never writes them as call-site literals.
FOREIGN_PLUGIN: Final = "foreign-plugin"
UNRECOGNIZED_EVENT: Final = "UnrecognizedEvent"
KILL_SWITCH_RENAME_SUFFIX: Final = "_RENAMED"
SCRIPT_PATH: Final = "scripts/session-start.py"
EXTENSIONLESS_SCRIPT_PATH: Final = "scripts/session-start"
SECOND_SCRIPT_PATH: Final = "scripts/second.py"
PINNED_CACHE_PREFIX: Final = "/home/user/.claude/plugins/cache/marketplace/plugin"
PINNED_VERSION: Final = "1.2.3"
EMPTY_RESULT_FLOOR: Final = f"echo '{PRE_WRITE_EMPTY_RESULT}'"
SHORT_CIRCUIT_FLOOR: Final = "true"


def pre_write_matcher() -> str:
    """Return the matcher naming exactly the source-owned Write and Edit tools."""
    return PRE_WRITE_MATCHER_SEPARATOR.join(sorted(PRE_WRITE_TOOLS))


def pre_write_command(runtime: str) -> str:
    """Return the source-owned pre-write command of one runtime tree."""
    if runtime == CODEX_RUNTIME_TREE:
        return PRE_WRITE_COMMAND_CODEX
    return PRE_WRITE_COMMAND_CLAUDE


def _invocation(token: str, path: str) -> str:
    return f"{PRE_WRITE_ADAPTER_INTERPRETER} {token}/{path}"


def guarded_script_command() -> str:
    """Return one guarded substituted-path invocation in the Claude token form."""
    return (
        f"{_invocation(CLAUDE_PLUGIN_ROOT_TOKEN, SCRIPT_PATH)} || {EMPTY_RESULT_FLOOR}"
    )


@dataclass(frozen=True)
class HookCase:
    """One named whole ``hooks.json`` payload, built for the runtime it lands in.

    The name states the clause the case varies. The case carries the plugin
    directory it is written under; it carries no expected result.
    """

    name: str
    plugin: str
    build: Callable[[str], Mapping[str, object]]


def _case(name: str, plugin: str, event: str, **parts: object) -> HookCase:
    """Build a case whose payload registers handlers on one event."""

    def build(runtime: str) -> Mapping[str, object]:
        return hook_config(event, **_resolve(runtime, parts))  # type: ignore[arg-type]

    return HookCase(name=name, plugin=plugin, build=build)


def _resolve(runtime: str, parts: Mapping[str, object]) -> dict[str, object]:
    resolved: dict[str, object] = {}
    for key, value in parts.items():
        resolved[key] = value(runtime) if callable(value) else value
    return resolved


def _floor_removed(runtime: str) -> str:
    return pre_write_command(runtime).replace(f" || {EMPTY_RESULT_FLOOR}; fi", "; fi")


def _kill_switch_renamed(runtime: str) -> str:
    return pre_write_command(runtime).replace(
        PRE_WRITE_KILL_SWITCH, PRE_WRITE_KILL_SWITCH + KILL_SWITCH_RENAME_SUFFIX
    )


def _pre_write_case(
    name: str, plugin: str = PRE_WRITE_PLUGIN, **parts: object
) -> HookCase:
    base: dict[str, object] = {
        "command": pre_write_command,
        "matcher": pre_write_matcher(),
    }
    base.update(parts)
    return _case(name, plugin, PRE_TOOL_USE_EVENT, **base)


def conforming_cases() -> tuple[HookCase, ...]:
    """Return the cases every rule passes: the exact exception and a SessionStart hook."""
    return (
        _pre_write_case("the exact pre-write exception"),
        _case("a SessionStart hook", FOREIGN_PLUGIN, SESSION_START_EVENT),
    )


def allowlist_violation_cases() -> tuple[HookCase, ...]:
    """Return the cases the event allowlist rejects: each blocking event and an unrecognized one."""
    cases = [
        _case(f"blocking event {event}", FOREIGN_PLUGIN, event)
        for event in sorted(BLOCKING_EVENTS)
    ]
    cases.append(_case("unrecognized event", FOREIGN_PLUGIN, UNRECOGNIZED_EVENT))
    return tuple(cases)


def missing_timeout_cases() -> tuple[HookCase, ...]:
    """Return the case whose handler declares no explicit timeout."""
    return (
        _case(
            "handler declares no timeout",
            FOREIGN_PLUGIN,
            SESSION_START_EVENT,
            timeout=None,
        ),
    )


def bare_script_cases() -> tuple[HookCase, ...]:
    """Return substituted-path invocations carrying no inline short-circuit fallback."""
    cases: list[HookCase] = []
    for token in SUBSTITUTED_PATH_TOKENS:
        commands = {
            f"bare script under {token}": _invocation(token, SCRIPT_PATH),
            f"extensionless script under {token}": _invocation(
                token, EXTENSIONLESS_SCRIPT_PATH
            ),
            f"quoted token {token}": (
                f'{PRE_WRITE_ADAPTER_INTERPRETER} "{token}"/{SCRIPT_PATH}'
            ),
            f"fallback before the script under {token}": (
                f"{EMPTY_RESULT_FLOOR} && {_invocation(token, SCRIPT_PATH)}"
            ),
            f"unguarded second script under {token}": (
                f"{_invocation(token, SCRIPT_PATH)} || {EMPTY_RESULT_FLOOR} ; "
                f"{_invocation(token, SECOND_SCRIPT_PATH)}"
            ),
        }
        cases.extend(
            _case(name, FOREIGN_PLUGIN, SESSION_START_EVENT, command=command)
            for name, command in commands.items()
        )
    return tuple(cases)


def guarded_script_cases() -> tuple[HookCase, ...]:
    """Return substituted-path invocations carrying a trailing fallback."""
    cases: list[HookCase] = []
    for token in SUBSTITUTED_PATH_TOKENS:
        guarded = f"{_invocation(token, SCRIPT_PATH)} || {EMPTY_RESULT_FLOOR}"
        commands = {
            f"guarded script under {token}": guarded,
            f"short-circuit script under {token}": (
                f"{_invocation(token, SCRIPT_PATH)} || {SHORT_CIRCUIT_FLOOR}"
            ),
            f"quoted guarded token {token}": (
                f'{PRE_WRITE_ADAPTER_INTERPRETER} "{token}"/{SCRIPT_PATH}'
                f" || {EMPTY_RESULT_FLOOR}"
            ),
            f"leading and trailing fallback under {token}": (
                f"{EMPTY_RESULT_FLOOR} && {guarded}"
            ),
        }
        cases.extend(
            _case(name, FOREIGN_PLUGIN, SESSION_START_EVENT, command=command)
            for name, command in commands.items()
        )
    return tuple(cases)


def pinned_cache_cases() -> tuple[HookCase, ...]:
    """Return the guarded command naming a version-pinned plugin cache path."""
    command = (
        f"{PRE_WRITE_ADAPTER_INTERPRETER} "
        f"{PINNED_CACHE_PREFIX}/{PINNED_VERSION}/{SCRIPT_PATH} || {EMPTY_RESULT_FLOOR}"
    )
    return (
        _case(
            "command names a version-pinned cache path",
            FOREIGN_PLUGIN,
            SESSION_START_EVENT,
            command=command,
        ),
    )


def pre_write_violation_cases() -> tuple[HookCase, ...]:
    """Return the cases the pre-write exception rejects, each varying one value.

    Plugin, matcher, command, a second entry, a second handler, and the exact
    block on every other blocking event.
    """
    cases = [_pre_write_case("plugin other than the pre-write plugin", FOREIGN_PLUGIN)]
    cases.extend(
        _pre_write_case(f"matcher naming only {tool}", matcher=tool)
        for tool in sorted(PRE_WRITE_TOOLS)
    )
    cases.extend(
        _pre_write_case(
            f"matcher repeating {tool}",
            matcher=PRE_WRITE_MATCHER_SEPARATOR.join((tool, tool)),
        )
        for tool in sorted(PRE_WRITE_TOOLS)
    )
    cases.extend(
        _pre_write_case(
            f"matcher naming both tools and repeating {tool}",
            matcher=PRE_WRITE_MATCHER_SEPARATOR.join((*sorted(PRE_WRITE_TOOLS), tool)),
        )
        for tool in sorted(PRE_WRITE_TOOLS)
    )
    cases.extend(
        (
            _pre_write_case("empty matcher", matcher=""),
            _pre_write_case("no matcher key", matcher=None),
            _pre_write_case(
                "command with its kill switch renamed", command=_kill_switch_renamed
            ),
            _pre_write_case("command with its floor removed", command=_floor_removed),
            _pre_write_case("second PreToolUse entry", entries=2),
            _pre_write_case("second handler in the exception block", handlers=2),
        )
    )
    cases.extend(
        _case(
            f"exception block on blocking event {event}",
            PRE_WRITE_PLUGIN,
            event,
            command=pre_write_command,
            matcher=pre_write_matcher(),
        )
        for event in sorted(BLOCKING_EVENTS - {PRE_TOOL_USE_EVENT})
    )
    return tuple(cases)


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

    def write_case(self, runtime: str, case: HookCase) -> Path:
        """Write one case's whole payload under its plugin in one runtime tree; return its path."""
        return self.write_hooks(runtime, case.plugin, case.build(runtime))

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
    "DEFAULT_HANDLER_COMMAND",
    "DEFAULT_HANDLER_TIMEOUT",
    "DEFAULT_MATCHER",
    "EMPTY_RESULT_FLOOR",
    "EXTENSIONLESS_SCRIPT_PATH",
    "FOREIGN_PLUGIN",
    "KILL_SWITCH_RENAME_SUFFIX",
    "HookCase",
    "HookTree",
    "PINNED_CACHE_PREFIX",
    "PINNED_VERSION",
    "SCRIPT_PATH",
    "SECOND_SCRIPT_PATH",
    "SHORT_CIRCUIT_FLOOR",
    "ScanReport",
    "UNRECOGNIZED_EVENT",
    "allowlist_violation_cases",
    "bare_script_cases",
    "conforming_cases",
    "guarded_script_cases",
    "guarded_script_command",
    "hook_config",
    "hook_tree",
    "missing_timeout_cases",
    "pinned_cache_cases",
    "pre_write_command",
    "pre_write_matcher",
    "pre_write_violation_cases",
]
