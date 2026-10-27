"""Harness: invoke the product-tree SessionStart hook as the runtime would.

The shipped hook is the inline-guard command in
``src/plugins/product-tree/hooks/hooks.json``; it delegates to the ``spx`` CLI hook
runner. This harness reads that command verbatim (so a test exercises the shipped
artifact, not a copy) and runs it through ``/bin/sh`` with a controlled
environment. ``CLAUDE_PROJECT_DIR`` and the working directory are set to the
caller's temp directory, so the ``spx`` hook runner resolves its session storage
(the worktree-occupancy claim) under that temp tree rather than the real
repository — every run is hermetic. ``spx`` is resolved from the inherited
``PATH``; a caller drives the disabled-or-absent guard branches by overriding the
kill-switch env var or the ``PATH``.

Exception case: none.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from hypothesis import seed, settings

from outcomeeng.validation.foundation_manifest import (
    MANIFEST_RELATIVE_PATH,
    parse_foundation_manifest,
)
from outcomeeng.validation.hook_contract import (
    MATCHER_FIELD,
    PLUGIN_ROOT_ENV,
    SESSION_START_COMPACT_MATCHER,
    SESSION_START_EVENT,
)
from outcomeeng.validation.hook_safety import COMMAND_FIELD, HOOKS_FIELD
from outcomeeng_testing.harnesses.product_tree import (
    marketplace_root_for_product_tree_root_test,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

# A shell variable name the harness may safely interpolate into a sourced script.
_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_PLUGIN_ROOT = ("src", "plugins", "product-tree")
_HOOKS_JSON = (*_PLUGIN_ROOT, "hooks", "hooks.json")
_COMPACT_ENTRY_FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "agent_environment"
    / "compact_entry"
)
_COMPACT_ENTRY_FIXTURE_SUFFIX = ".hooks.json"
HOOK_EVIDENCE_SEED = 20260728
HOOK_EVIDENCE_EXAMPLES = 40
HOOK_EVIDENCE_REPLAY_PATH = (
    "just test "
    "spx/21-product-tree.enabler/13-agent-environment.enabler/21-identity.enabler/tests"
)

# The hook's environment kill switch (hooks.json): set to "1" to short-circuit the
# hook to a valid empty result before it probes for or invokes spx.
KILL_SWITCH_ENV = "PRODUCT_TREE_SESSION_HOOK_DISABLED"
KILL_SWITCH_DISABLED = "1"

# The spx hook runner records this PID as the worktree claim's controlling
# process; spx worktree status reads it back and checks liveness, so a claim is
# `running` only while this process is alive. A test sets it to its own PID.
WORKTREE_CONTROLLING_PID_ENV = "SPX_WORKTREE_CONTROLLING_PID"
# The hook integration asserts that spx exports a worktree claim; the exact
# export spelling follows the pinned spx floor installed by each gate.
WORKTREE_CLAIMED_ENV = "CLAUDE_WORKTREE_CLAIMED"
WORKTREE_CLAIM_PATH_ENV = "SPX_WORKTREE_CLAIM_PATH"
UNSET_ENV_VALUE = "<unset>"

# Env vars dropped from the child so the hook command sees only what the call
# provides — its own session identity, project dir, and env file, not the runner's.
_SESSION_START_ENV_EXCLUDES = {
    KILL_SWITCH_ENV,
    PLUGIN_ROOT_ENV,
    "CLAUDE_PROJECT_DIR",
    "CLAUDE_ENV_FILE",
    "CLAUDE_SESSION_ID",
    "CODEX_THREAD_ID",
}

# The hook declares its own short timeout; the harness bounds the subprocess well
# above it so a hung command surfaces as a harness failure rather than a wedge.
_SUBPROCESS_TIMEOUT_S = 60


def hook_generated_evidence(
    evidence_run: Callable[[], None],
) -> Callable[[], None]:
    """Apply reproducible Hypothesis policy to agent-hook evidence."""
    configured = seed(HOOK_EVIDENCE_SEED)(
        settings(
            max_examples=HOOK_EVIDENCE_EXAMPLES,
            deadline=None,
            print_blob=True,
        )(evidence_run)
    )

    def run_evidence() -> None:
        run_replayable_property(
            configured,
            seed_value=HOOK_EVIDENCE_SEED,
            replay_path=HOOK_EVIDENCE_REPLAY_PATH,
        )

    return run_evidence


@contextmanager
def session_start_workspace() -> Iterator[tuple[Path, Path]]:
    """Yield an isolated project directory and its hook env-file path."""
    with TemporaryDirectory() as directory:
        project_dir = Path(directory)
        yield project_dir, project_dir / "claude.env"


@dataclass(frozen=True)
class HookEntry:
    """One ``SessionStart`` entry as declared: its matcher and handler commands."""

    matcher: str
    commands: tuple[str, ...]


def marketplace_root(test_file: str | None = None) -> Path:
    """Return the repository root that carries the authored plugin tree."""
    return (
        marketplace_root_for_product_tree_root_test(test_file)
        if test_file is not None
        else Path(__file__).resolve().parents[2]
    )


def shipped_plugin_root(test_file: str | None = None) -> Path:
    """Return the authored product-tree plugin root a hook command resolves against."""
    return marketplace_root(test_file).joinpath(*_PLUGIN_ROOT)


def compact_recovery_resource(plugin_root: Path) -> Path:
    """Return the reminder resource path the plugin's manifest names under ``plugin_root``."""
    manifest_text = plugin_root.joinpath(*Path(MANIFEST_RELATIVE_PATH).parts).read_text(
        encoding="utf-8"
    )
    manifest = parse_foundation_manifest(manifest_text)
    return plugin_root.joinpath(*Path(manifest.compact_recovery).parts)


def _hooks_config(
    test_file: str | None = None, hooks_file: Path | None = None
) -> dict[str, Any]:
    path = (
        hooks_file
        if hooks_file is not None
        else marketplace_root(test_file).joinpath(*_HOOKS_JSON)
    )
    config: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return config


def session_start_events(test_file: str | None = None) -> list[str]:
    """Return the hook event names the product-tree plugin declares, in order."""
    return list(_hooks_config(test_file)[HOOKS_FIELD])


def session_start_entries(
    test_file: str | None = None, hooks_file: Path | None = None
) -> list[HookEntry]:
    """Return every ``SessionStart`` entry in declaration order."""
    entries = _hooks_config(test_file, hooks_file)[HOOKS_FIELD][SESSION_START_EVENT]
    return [
        HookEntry(
            matcher=entry.get(MATCHER_FIELD, ""),
            commands=tuple(hook[COMMAND_FIELD] for hook in entry[HOOKS_FIELD]),
        )
        for entry in entries
    ]


def _single_command(entries: list[HookEntry], description: str) -> str:
    commands = [command for entry in entries for command in entry.commands]
    if len(commands) != 1:
        msg = f"expected exactly one {description} command, found {len(commands)}"
        raise ValueError(msg)
    return commands[0]


def delegating_entry_command(test_file: str | None = None) -> str:
    """Return the command of the ``SessionStart`` entry that is not the compact entry."""
    return _single_command(
        [
            entry
            for entry in session_start_entries(test_file)
            if entry.matcher != SESSION_START_COMPACT_MATCHER
        ],
        "delegating SessionStart",
    )


def compact_entry_command(
    test_file: str | None = None, hooks_file: Path | None = None
) -> str:
    """Return the command of the ``SessionStart`` entry matched on ``compact``."""
    return _single_command(
        [
            entry
            for entry in session_start_entries(test_file, hooks_file)
            if entry.matcher == SESSION_START_COMPACT_MATCHER
        ],
        "compact SessionStart",
    )


def compact_entry_violation_fixtures() -> list[Path]:
    """Return the inert ``hooks.json`` payloads whose compact entry violates the rule."""
    return sorted(_COMPACT_ENTRY_FIXTURES.glob(f"*{_COMPACT_ENTRY_FIXTURE_SUFFIX}"))


def run_session_start(
    payload: dict[str, object],
    *,
    env_file: Path | None = None,
    project_dir: Path | str | None = None,
    env_overrides: dict[str, str] | None = None,
    path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the shipped ``SessionStart`` hook command with ``payload`` on stdin.

    The ambient ``CLAUDE_PROJECT_DIR``, ``CLAUDE_ENV_FILE``, and session-identity
    env vars are dropped so the hook sees only what the call provides. ``env_file``
    is exported as ``CLAUDE_ENV_FILE``; ``project_dir`` is exported as
    ``CLAUDE_PROJECT_DIR`` and used as the working directory, so the ``spx`` hook
    runner resolves its session storage there. ``env_overrides`` overlays extra
    variables (such as the kill switch); ``path`` overrides ``PATH`` so a caller
    can withhold ``spx`` to drive the absent-dependency branch.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _SESSION_START_ENV_EXCLUDES
    }
    if env_file is not None:
        env["CLAUDE_ENV_FILE"] = str(env_file)
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if path is not None:
        env["PATH"] = path
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(  # noqa: S603 — command is the shipped hook artifact under test.
        ["/bin/sh", "-c", delegating_entry_command()],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_dir) if project_dir is not None else None,
        timeout=_SUBPROCESS_TIMEOUT_S,
    )


def run_compact_entry(
    *,
    plugin_root: Path,
    project_dir: Path,
    command: str | None = None,
    env_overrides: dict[str, str] | None = None,
    path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a compact-entry command as the host would after a compaction.

    ``command`` defaults to the shipped compact entry; a caller passes a fixture's
    command to exercise a violating entry. ``plugin_root`` is exported as the plugin
    root the command resolves its resource against, and ``project_dir`` is the
    working directory, so any state the command writes lands there. ``path``
    overrides ``PATH`` so a caller can withhold every external command.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _SESSION_START_ENV_EXCLUDES
    }
    env[PLUGIN_ROOT_ENV] = str(plugin_root)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if path is not None:
        env["PATH"] = path
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(  # noqa: S603 — command is the shipped hook artifact or a violating fixture under test.
        [
            "/bin/sh",
            "-c",
            command if command is not None else compact_entry_command(),
        ],
        input="",
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_dir),
        timeout=_SUBPROCESS_TIMEOUT_S,
    )


def init_session_worktree(path: Path) -> None:
    """Initialize a real git worktree at ``path`` the hook can claim (L3 setup)."""
    subprocess.run(  # noqa: S603, S607 — git is a standard dev tool on PATH.
        ["git", "-C", str(path), "init", "-q"],
        check=True,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT_S,
    )


def read_env_exports(env_file: Path, names: Sequence[str]) -> dict[str, str]:
    """Source the hook's env file in ``/bin/sh`` and return each name's value.

    Sourcing through the shell applies the file's own ``export`` quoting, so the
    test reads the value a later Bash tool call in the session would see — not a
    hand-parsed line. An unset variable resolves to ``"<unset>"`` so a missing
    write is a loud assertion failure rather than an empty string. Each name is
    interpolated into the sourced script as a parameter expansion, so a name that
    is not a bare shell identifier could inject shell — every name is validated
    against ``_ENV_NAME`` first and a non-conforming name is a ``ValueError``.
    """
    for name in names:
        if not _ENV_NAME.fullmatch(name):
            msg = f"env var name must be a shell identifier, got {name!r}"
            raise ValueError(msg)
    script = (
        "\n".join(f"unset {name}" for name in names) + "\n"
        ". "
        + shlex.quote(str(env_file))
        + "\n"
        + "\n".join(f'printf "%s\\n" "${{{name}-<unset>}}"' for name in names)
    )
    result = subprocess.run(  # noqa: S603 — fixed /bin/sh argv; names validated as shell identifiers above.
        ["/bin/sh", "-c", script],
        check=True,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT_S,
    )
    return dict(zip(names, result.stdout.splitlines(), strict=True))


def worktree_claim_path_from_env(env_file: Path, project_dir: Path) -> Path:
    """Return the worktree claim path exported or indicated by the hook runner."""
    env = read_env_exports(env_file, [WORKTREE_CLAIMED_ENV, WORKTREE_CLAIM_PATH_ENV])
    claim_path = env[WORKTREE_CLAIM_PATH_ENV]
    if claim_path != UNSET_ENV_VALUE:
        return Path(claim_path)
    if env[WORKTREE_CLAIMED_ENV] == "1":
        claims = sorted((project_dir.resolve() / ".spx" / "worktrees").glob("*.claim"))
        if claims:
            return claims[0].resolve()
    msg = "SessionStart hook did not export or indicate a worktree claim"
    raise AssertionError(msg)


def has_worktree_claim_export(env: str | dict[str, str]) -> bool:
    """Return whether hook env output carries a worktree-claim export."""
    if isinstance(env, str):
        return (
            f"export {WORKTREE_CLAIMED_ENV}=1" in env
            or f"export {WORKTREE_CLAIM_PATH_ENV}=" in env
        )
    return env.get(WORKTREE_CLAIMED_ENV) == "1" or env.get(
        WORKTREE_CLAIM_PATH_ENV
    ) not in (None, "", UNSET_ENV_VALUE)


def worktree_occupancy(project_dir: Path) -> list[dict[str, Any]]:
    """Return spx's own occupancy verdict for the project's worktree claims.

    Runs the real ``spx worktree status`` from inside ``project_dir``, so the
    test asserts the spx CLI recognizes the claim the hook recorded — the
    round-trip, not a claim file's presence on disk. ``status`` resolves both the
    worktree under inspection and its ``.spx/worktrees`` from the working
    directory, so no explicit ``--worktrees-dir`` (and thus no dependency on that
    flag's availability at the pinned floor) is needed.
    """
    result = subprocess.run(  # noqa: S603, S607 — spx is the methodology CLI on PATH.
        ["spx", "worktree", "status", "--format", "json"],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        timeout=_SUBPROCESS_TIMEOUT_S,
    )
    parsed: Any = json.loads(result.stdout)
    return parsed if isinstance(parsed, list) else [parsed]


__all__ = [
    "HookEntry",
    "KILL_SWITCH_DISABLED",
    "KILL_SWITCH_ENV",
    "HOOK_EVIDENCE_REPLAY_PATH",
    "SESSION_START_EVENT",
    "UNSET_ENV_VALUE",
    "WORKTREE_CLAIMED_ENV",
    "WORKTREE_CLAIM_PATH_ENV",
    "WORKTREE_CONTROLLING_PID_ENV",
    "compact_entry_command",
    "compact_entry_violation_fixtures",
    "compact_recovery_resource",
    "delegating_entry_command",
    "has_worktree_claim_export",
    "hook_generated_evidence",
    "init_session_worktree",
    "read_env_exports",
    "run_compact_entry",
    "run_session_start",
    "session_start_entries",
    "session_start_events",
    "session_start_workspace",
    "shipped_plugin_root",
    "worktree_claim_path_from_env",
    "worktree_occupancy",
]
