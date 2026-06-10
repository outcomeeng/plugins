<overview>

Plugin hook patterns for injecting session identity and runtime context into agent Bash tool calls. Read before authoring a hook script or `hooks/hooks.json`.

</overview>

<session_identity>

**The `SessionStart` hook + `$CLAUDE_ENV_FILE` pattern is the canonical way to make session identity available to all Bash tool calls in a session.**

Claude Code injects `$CLAUDE_ENV_FILE` into `SessionStart` hooks. Writing `export VAR=value` lines to that file persists the variable for every subsequent Bash tool call in the session. Codex does not use this mechanism — it injects `$CODEX_THREAD_ID` directly as an env var.

Hook script (`scripts/session-start.py` — Python, stdlib only, no `jq`):

```python
#!/usr/bin/env python3
import json
import os
import sys

payload = json.loads(sys.stdin.read())
session_id = payload.get("session_id") or ""

env_file = os.environ.get("CLAUDE_ENV_FILE")
if env_file and session_id:
    with open(env_file, "a", encoding="utf-8") as handle:
        handle.write(f"export CLAUDE_SESSION_ID={session_id}\n")
```

Hook declaration (`hooks/hooks.json`):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session-start.py" }]
      }
    ]
  }
}
```

After this hook fires, `$CLAUDE_SESSION_ID` is available in all Bash tool calls for the session — no file-system heuristics or index files needed.

**Comparison by runtime:**

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
    └── session-start.py  ← hook script (python3, stdlib only)
```

Use `${CLAUDE_PLUGIN_ROOT}` in hook commands to reference the plugin's installation path. Use `${CLAUDE_PLUGIN_DATA}` for data that survives plugin updates.

</hooks_directory>
