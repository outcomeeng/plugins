<overview>

Plugin hook patterns for injecting session identity and runtime context into agent Bash tool calls. Read before authoring a hook script or `hooks/hooks.json`.

</overview>

<session_identity>

**The `SessionStart` hook + `$CLAUDE_ENV_FILE` pattern is the canonical way to make session identity available to all Bash tool calls in a session.**

Claude Code injects `$CLAUDE_ENV_FILE` into `SessionStart` hooks. Writing `export VAR=value` lines to that file persists the variable for every subsequent Bash tool call in the session. Codex does not use this mechanism — it injects `$CODEX_THREAD_ID` directly as an env var.

Hook script (`bin/session-start`):

```bash
#!/usr/bin/env bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')

if [[ -n "${CLAUDE_ENV_FILE:-}" ]]; then
  echo "export CLAUDE_SESSION_ID=$SESSION_ID" >> "$CLAUDE_ENV_FILE"
fi
```

Hook declaration (`hooks/hooks.json`):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/bin/session-start" }]
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
└── bin/
    └── session-start  ← hook script (chmod +x)
```

Use `${CLAUDE_PLUGIN_ROOT}` in hook commands to reference the plugin's installation path. Use `${CLAUDE_PLUGIN_DATA}` for data that survives plugin updates.

</hooks_directory>
