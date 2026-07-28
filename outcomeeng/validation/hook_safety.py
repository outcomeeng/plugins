"""Validate that no shipped plugin hook can trap an agent.

A hook traps an agent when it fires on a blocking-capable event (where exit 2, a
deny or block decision, or a timeout denies the action), omits an explicit
timeout, invokes a script at a substituted path with no inline short-circuit
fallback, or names a version-pinned plugin cache path that drifts. This validator
scans every ``hooks/hooks.json`` under the generated ``dist/claude`` and
``dist/codex`` trees and reports each violation. It checks the deterministic,
falsifiable half of the contract; the floor's emitting a valid empty result on
every branch is the audited inline-guard rule, not a regex check here.

The same hooks.json ships byte-identical to dist/claude and dist/codex, and both
runtimes share the hook schema and the ``${CLAUDE_PLUGIN_ROOT}`` variable (Codex
exposes it as a compatibility alias), so one set of rules governs both. Enforcement
is an allowlist: a hook may fire only on an event in ``SAFE_EVENTS`` — the events
observational on EVERY shipped runtime. Any other event is flagged — every event in
``BLOCKING_EVENTS`` and any unrecognized event alike — so a runtime that adds a new
blocking event, or an event blocking on one runtime but not another, fails closed
rather than slipping through a denylist.

Usage::

    python3 -m outcomeeng.validation.hook_safety [ROOT ...]

Exit codes:
    0 - No hook config under any root violates the contract
    1 - One or more hook configs violate the contract
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

from outcomeeng.validation.hook_contract import SESSION_START_EVENT

# Events observational on EVERY runtime the marketplace ships a hook to. The same
# hooks.json ships byte-identical to dist/claude and dist/codex, so an event is safe
# only when it is non-blocking on both Claude Code and Codex. The set is the
# cross-runtime intersection: Codex documents only SessionStart and SubagentStart as
# observational (it classifies PostToolUse and PostCompact as able to block
# continuation), so events Claude Code alone treats as non-blocking are excluded.
# Adding an event requires confirming it is observational on every shipped runtime.
SAFE_EVENTS: Final[frozenset[str]] = frozenset(
    {
        SESSION_START_EVENT,
        "SubagentStart",
    }
)

# Documented blocking-capable events on either runtime: exit 2, a deny/block decision,
# a timeout, or a ``continue: false`` denies or halts the agent's action. Enforcement
# flags anything outside SAFE_EVENTS — every event here plus any unrecognized event —
# so this set sharpens the message and pins the domain the compliance evidence
# exercises. PostToolUse, PostToolUseFailure, and PostCompact are blocking-capable on
# Codex even though Claude Code treats them as non-blocking.
BLOCKING_EVENTS: Final[frozenset[str]] = frozenset(
    {
        "PreToolUse",
        "UserPromptSubmit",
        "UserPromptExpansion",
        "PermissionRequest",
        "PostToolBatch",
        "PostToolUse",
        "PostToolUseFailure",
        "Stop",
        "SubagentStop",
        "TeammateIdle",
        "TaskCreated",
        "TaskCompleted",
        "ConfigChange",
        "PreCompact",
        "PostCompact",
        "WorktreeCreate",
        "Elicitation",
        "ElicitationResult",
    }
)

# A reference into the plugin tree by a substituted path, regardless of extension — a
# ``.py``/``.sh`` script, an extensionless wrapper, or any file whose absence under a
# drifted plugin root makes a bare invocation fail. The build emits two distributions
# with different path tokens: dist/claude keeps ``${CLAUDE_PLUGIN_ROOT}`` /
# ``${CLAUDE_SKILL_DIR}``, while dist/codex carries Codex's ``${PLUGIN_ROOT}`` and the
# rewritten ``${SKILL_DIR}`` (build rewrites ``${CLAUDE_SKILL_DIR}`` → ``${SKILL_DIR}``;
# ``${CLAUDE_PLUGIN_ROOT}`` is preserved via Codex's alias). All four are matched so a
# bare invocation is caught in whichever tree it lands.
_SUBSTITUTED_SCRIPT: Final[re.Pattern[str]] = re.compile(
    r"\$\{(?:CLAUDE_PLUGIN_ROOT|CLAUDE_SKILL_DIR|PLUGIN_ROOT|SKILL_DIR)\}[\"']?/[^\s|;&]*"
)
# A short-circuit fallback (``||``) following the substituted-path invocation. This is
# the deterministic, falsifiable half of the contract: a substituted-path command with
# no ``||`` fallback at all is bare and is flagged. Whether the fallback's floor is a
# terminal successful empty-result emission is a shell-semantics property no regex
# verifies — that is the audited inline-guard property of the hook safety contract,
# not this check.
_FALLBACK: Final[re.Pattern[str]] = re.compile(r"\|\|")
# A version-pinned plugin cache path (a semver segment under a cache directory).
_PINNED_CACHE: Final[re.Pattern[str]] = re.compile(r"/cache/\S*?\d+\.\d+\.\d+")


def _event_violation(event: str) -> str | None:
    """Return a violation message when ``event`` is not a permitted non-blocking event."""
    if event in SAFE_EVENTS:
        return None
    if event in BLOCKING_EVENTS:
        return f"{event}: hook on blocking-capable event — exit 2 or a timeout would deny the agent's action"
    return f"{event}: hook on an event outside the known non-blocking set — only observe/inject events are permitted"


def _command_violations(event: str, command: str) -> list[str]:
    """Return command-shape violations for a hook handler's ``command`` string."""
    found: list[str] = []
    # Every substituted-path invocation needs its own guard: a guarded first script
    # does not cover a later bare one. Check each match's own statement (up to the next
    # ``;``) for a ``||`` short-circuit.
    for match in _SUBSTITUTED_SCRIPT.finditer(command):
        statement = command[match.end() :].split(";", 1)[0]
        if _FALLBACK.search(statement) is None:
            found.append(
                f"{event}: hook command invokes a script at a substituted path with no inline short-circuit fallback"
            )
            break
    if _PINNED_CACHE.search(command):
        found.append(f"{event}: hook command names a version-pinned plugin cache path")
    return found


def hook_config_violations(config: Mapping[str, object]) -> list[str]:
    """Return every hook-safety violation in a parsed ``hooks.json`` config.

    An empty list means the config registers hooks only on non-blocking events,
    declares an explicit timeout on each handler, carries an inline short-circuit
    fallback after every substituted-path script invocation, and names no pinned
    cache path.
    """
    violations: list[str] = []
    hooks = config.get("hooks")
    if not isinstance(hooks, Mapping):
        return violations
    for raw_event, blocks in hooks.items():
        event = str(raw_event)
        if not isinstance(blocks, list):
            continue
        event_issue = _event_violation(event)
        saw_handler = False
        for block in blocks:
            if not isinstance(block, Mapping):
                continue
            handlers = block.get("hooks")
            if not isinstance(handlers, list):
                continue
            for handler in handlers:
                if not isinstance(handler, Mapping):
                    continue
                saw_handler = True
                if "timeout" not in handler:
                    violations.append(
                        f"{event}: hook handler declares no explicit timeout"
                    )
                command = handler.get("command")
                if isinstance(command, str):
                    violations.extend(_command_violations(event, command))
        # Report the event-level violation once per event, not once per handler.
        if event_issue is not None and saw_handler:
            violations.append(event_issue)
    return violations


def iter_tree_violations(root: Path) -> list[str]:
    """Scan every ``hooks/hooks.json`` under ``root`` and return located violations."""
    violations: list[str] = []
    for hooks_file in sorted(root.rglob("hooks.json")):
        if hooks_file.parent.name != "hooks":
            continue
        try:
            parsed: object = json.loads(hooks_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            violations.append(f"{hooks_file}: unreadable hook config ({exc})")
            continue
        if not isinstance(parsed, Mapping):
            continue
        relative = hooks_file.relative_to(root)
        violations.extend(
            f"{relative}: {issue}" for issue in hook_config_violations(parsed)
        )
    return violations


# The generated runtime trees a hook config can ship under, scanned by default.
DEFAULT_ROOTS: Final[tuple[Path, ...]] = (Path("dist/claude"), Path("dist/codex"))


def main(argv: Sequence[str] | None = None) -> int:
    """Scan the given roots (default: the dist trees) and report hook-safety violations."""
    args = list(sys.argv[1:] if argv is None else argv)
    roots = [Path(arg) for arg in args] if args else list(DEFAULT_ROOTS)
    violations: list[str] = []
    for root in roots:
        if root.exists():
            violations.extend(f"{root}/{issue}" for issue in iter_tree_violations(root))
    for violation in violations:
        print(violation, file=sys.stderr)
    if violations:
        print(f"hook-safety: {len(violations)} violation(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
