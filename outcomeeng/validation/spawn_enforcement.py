"""Report spawn calls that leave a child outside the forwarded-signal contract.

Two rules the gate node declares bound how a child is started: it runs in its
own session, so a forwarded signal reaches the whole process group rather than
one PID; and it starts with the forwarded signals unblocked, so the
orchestrator's protected spawn window never hands a validator a blocked mask.
Both are reported here, as a pure function of the paths given, so each
detection is exercised against a violating source rather than asserted over the
one module that already conforms.

Every name the readers match is taken from the declaration that owns it — the
spawn call from `subprocess`, the unblock call and its action from `signal`,
and the forwarded set from the orchestrator — so no spelling is restated here.
"""

from __future__ import annotations

import ast
import signal
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Final

from outcomeeng.validation._engine import FORWARDED_SIGNALS

SPAWN_MODULE: Final = subprocess.__name__
"""The module whose spawn call both rules constrain."""
SPAWN_CALL: Final = subprocess.Popen.__name__
"""The call that starts a child, and so the site each rule reads."""
SESSION_KEYWORD: Final = "start_new_session"
"""The `Popen` keyword that puts the child in its own session."""
PREEXEC_KEYWORD: Final = "preexec_fn"
"""The `Popen` keyword naming the function the child runs before exec."""
UNBLOCK_CALL: Final = signal.pthread_sigmask.__name__
"""The call a child-side function makes to change its own signal mask."""
UNBLOCK_ACTION: Final = signal.SIG_UNBLOCK.name
"""The mask action that unblocks, rather than blocks or replaces."""
FORWARDED_SIGNAL_NAMES: Final = frozenset(sig.name for sig in FORWARDED_SIGNALS)
"""The signals a spawned child must start with unblocked, by name."""

SESSIONLESS_SITE_KIND: Final = "sessionless-spawn"
"""The kind a site carries when the spawn leaves the child in the caller's session."""
UNMASKED_SITE_KIND: Final = "blocked-child-mask"
"""The kind a site carries when the spawn leaves the forwarded signals blocked."""


def sessionless_spawn_sites(paths: Iterable[Path]) -> tuple[str, ...]:
    """Return every spawn among `paths` that leaves the child in the caller's session.

    A spawn conforms only by passing the session keyword the literal `True`.
    Omitting the keyword and passing it anything else are the same defect —
    the child shares the caller's process group, so a forwarded signal reaches
    one PID and the grandchildren outlive it — so both are reported.
    """
    sites: list[str] = []
    for path in sorted(paths):
        module = _parsed(path)
        for call in _spawn_calls(module):
            keywords = _keywords(call)
            value = keywords.get(SESSION_KEYWORD)
            if not _is_literal_true(value):
                sites.append(f"{path}::{SESSIONLESS_SITE_KIND}:{call.lineno}")
    return tuple(sites)


def unmasked_child_spawn_sites(paths: Iterable[Path]) -> tuple[str, ...]:
    """Return every spawn among `paths` that leaves the forwarded signals blocked.

    Two shapes reach the same child state. A spawn that names no child-side
    function cannot unblock anything, and one whose named function does not
    unblock every forwarded signal leaves the rest blocked, so a validator
    inherits a mask that swallows the signal the orchestrator forwards. The
    reader follows the name to the function in the same module and, through a
    module-level binding when the call passes one, to the set it unblocks.
    """
    sites: list[str] = []
    for path in sorted(paths):
        module = _parsed(path)
        for call in _spawn_calls(module):
            named = _keywords(call).get(PREEXEC_KEYWORD)
            if not isinstance(named, ast.Name):
                sites.append(f"{path}::{UNMASKED_SITE_KIND}:{call.lineno}")
                continue
            if not _unblocks_forwarded_signals(module, named.id):
                sites.append(f"{path}::{UNMASKED_SITE_KIND}:{call.lineno}")
    return tuple(sites)


def _parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _spawn_calls(module: ast.Module) -> tuple[ast.Call, ...]:
    """Return every `subprocess.Popen` call in the module, in source order."""
    return tuple(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == SPAWN_CALL
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == SPAWN_MODULE
    )


def _keywords(call: ast.Call) -> dict[str, ast.expr]:
    return {
        keyword.arg: keyword.value
        for keyword in call.keywords
        if keyword.arg is not None
    }


def _is_literal_true(value: ast.expr | None) -> bool:
    return isinstance(value, ast.Constant) and value.value is True


def _unblocks_forwarded_signals(module: ast.Module, function_name: str) -> bool:
    """Whether the named function unblocks every forwarded signal.

    The function is found in the module the spawn lives in, because that is the
    only source the spawn's own name can resolve against. Its unblock call's
    signal set is read where the call passes it, following one module-level
    binding when the set is named rather than written inline.
    """
    definition = next(
        (
            node
            for node in ast.walk(module)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name == function_name
        ),
        None,
    )
    if definition is None:
        return False
    for call in ast.walk(definition):
        if not isinstance(call, ast.Call):
            continue
        if not (
            isinstance(call.func, ast.Attribute) and call.func.attr == UNBLOCK_CALL
        ):
            continue
        if len(call.args) != 2 or not _is_unblock_action(call.args[0]):
            continue
        if FORWARDED_SIGNAL_NAMES <= _signal_names(module, call.args[1]):
            return True
    return False


def _is_unblock_action(value: ast.expr) -> bool:
    return isinstance(value, ast.Attribute) and value.attr == UNBLOCK_ACTION


def _signal_names(module: ast.Module, value: ast.expr) -> frozenset[str]:
    """Return the signal names an unblock call's set expression reaches."""
    resolved = (
        _resolved_binding(module, value) if isinstance(value, ast.Name) else value
    )
    return frozenset(
        node.attr for node in ast.walk(resolved) if isinstance(node, ast.Attribute)
    )


def _resolved_binding(module: ast.Module, name: ast.Name) -> ast.expr:
    """Return the module-level value bound to `name`, or the name itself."""
    for node in module.body:
        if isinstance(node, ast.Assign):
            targets: tuple[ast.expr, ...] = tuple(node.targets)
            value: ast.expr | None = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
            value = node.value
        else:
            continue
        if value is None:
            continue
        if any(
            isinstance(target, ast.Name) and target.id == name.id for target in targets
        ):
            return value
    return name
