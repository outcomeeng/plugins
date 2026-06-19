<overview>

Plugin hook patterns for injecting session identity and runtime context into agent Bash tool calls. Read before authoring a hook script or `hooks/hooks.json`.

A shipped hook observes or injects context on a non-blocking event only; it can never deny, block, or stall an agent. Every hook command is a self-contained inline guard whose reachable floor is a clean exit on every branch, carries an explicit short timeout, exposes an environment kill switch, and treats any script or external command it runs as an optional dependency. A hook that fails degrades to a no-op, never an error — a missing script at a substituted path, an absent CLI, or a drifted plugin root leaves the session untouched.

</overview>

<session_identity>

**The hook stdin `session_id` field is the canonical hook-script identity source. The `SessionStart` hook + `$CLAUDE_ENV_FILE` pattern is the Claude Code way to make that identity available to later Bash tool calls in a session.**

Claude Code and Codex command hooks receive a JSON payload on stdin that includes `session_id`, `transcript_path`, `cwd`, `hook_event_name`, and `model`; `SessionStart` also receives `source`. Claude Code injects `$CLAUDE_ENV_FILE` into `SessionStart` hooks. Writing `export VAR=value` lines to that file persists the variable for every subsequent Bash tool call in the session. Codex does not use `$CLAUDE_ENV_FILE`; hook scripts still read the documented `session_id` from stdin, while later shell commands may also see `$CODEX_THREAD_ID` in the runtime environment.

A hook script that writes the identity (`scripts/session-start.py` — Python, stdlib only, no `jq`):

```python
#!/usr/bin/env python3
import json
import os
import sys

payload = json.loads(sys.stdin.read() or "{}")
session_id = payload.get("session_id") or ""

env_file = os.environ.get("CLAUDE_ENV_FILE")
if env_file and session_id:
    with open(env_file, "a", encoding="utf-8") as handle:
        handle.write(f"export CLAUDE_SESSION_ID={session_id}\n")
```

The hook *command* never invokes that script bare. It wraps the invocation in an inline guard: an environment kill switch, an explicit `timeout`, and a floor that emits a valid empty result on every branch, so a missing script or a drifted plugin root degrades to a no-op rather than denying the session. Hook declaration (`hooks/hooks.json`):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "if [ \"${MY_PLUGIN_SESSION_HOOK:-1}\" = \"0\" ]; then exit 0; fi; python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py\" 2>/dev/null || echo '{}'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

The guard, piece by piece: `MY_PLUGIN_SESSION_HOOK=0` disables the hook without editing config or leaving the session; the trailing `|| echo '{}'` floors the command to a clean exit on every branch; the `timeout` bounds the command so it never inherits the runtime's multi-minute default. The floor is any branch that exits 0 without an error — `|| true` and a bare `exit 0` are equally valid; `|| echo '{}'` additionally emits a well-formed empty result, the defensive form for a runtime that parses the hook's stdout (`SessionStart` does not). Register only on a non-blocking event — `SessionStart` is observational. An event the runtime consults before an action (for example `PreToolUse`, `Stop`, `PreCompact`) turns any hook failure into a wall the agent cannot pass, so it is never a safe host for a command hook.

A hook that needs richer session state delegates to a CLI rather than reimplementing it in a shipped script. Treat that CLI as an optional dependency: resolve it from an environment override then `PATH`, probe it with `command -v` before use, floor its invocation to a clean exit (`|| true`), and never name a version-pinned cache path. The delegating command stays a self-contained inline guard, and the CLI itself performs the `$CLAUDE_ENV_FILE` write the script does above — the hook command never inspects what the CLI wrote:

```json
{
  "type": "command",
  "command": "if [ \"${MY_PLUGIN_SESSION_HOOK:-1}\" = \"0\" ]; then exit 0; fi; BIN=\"${MY_PLUGIN_BIN:-my-cli}\"; command -v \"$BIN\" >/dev/null 2>&1 || exit 0; \"$BIN\" session-start || true",
  "timeout": 10
}
```

After this hook fires, `$CLAUDE_SESSION_ID` is available in all Bash tool calls for the session — no file-system heuristics or index files needed.

**Comparison by runtime for later shell commands:**

| Runtime     | Env var              | Source                                     |
| ----------- | -------------------- | ------------------------------------------ |
| Claude Code | `$CLAUDE_SESSION_ID` | `SessionStart` hook via `$CLAUDE_ENV_FILE` |
| Codex       | `$CODEX_THREAD_ID`   | Injected by runtime                        |

**`SessionStart` fires on**: startup, resume, `/clear`, and `/compact`. Hook scripts must be idempotent.

</session_identity>

<hooks_directory>

Hooks live at the plugin root, not inside `.claude-plugin/`:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json     ← hook declarations
└── scripts/
    └── session-start.py  ← hook script (python3, stdlib only), invoked through the guarded command
```

Use `${CLAUDE_PLUGIN_ROOT}` in hook commands to reference the plugin's installation path. Use `${CLAUDE_PLUGIN_DATA}` for data that survives plugin updates. Never reference a version-pinned plugin cache path: it drifts the instant the plugin updates, and a hook command that resolves a stale path fails where the guarded floor cannot save it.

</hooks_directory>

<anti_patterns>

The bare invocation is the canonical unsafe form:

```json
{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py" }
```

It fails every property of the guarded command above:

- **No floor.** When the script path drifts (a pinned cache, a moved plugin root, a missing `scripts/` directory), `python3` errors instead of exiting clean. On a blocking-capable event that error denies the action; even on a non-blocking event it surfaces noise.
- **No timeout.** The command inherits the runtime's multi-minute default, so a hung script stalls session start.
- **No kill switch.** An operator hitting a bad hook cannot disable it without editing and reinstalling the plugin.
- **No optional-dependency probe.** An invoked CLI is assumed present rather than resolved-then-probed, so an absent binary errors.

A hook missing any one of these guards is unsafe regardless of how reliable its script looks today.

</anti_patterns>
