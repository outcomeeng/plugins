<overview>

Claude plugin hooks are not a Codex skill contract. Do not author `hooks`, `$CLAUDE_ENV_FILE`, `${CLAUDE_PLUGIN_ROOT}`, or `${CLAUDE_PLUGIN_DATA}` behavior for Codex from this reference.

</overview>

<codex_session_identity>

Codex provides `$CODEX_THREAD_ID` to shell commands when session identity is available. Read it directly from the runtime environment; do not install a hook to synthesize a second identity variable.

</codex_session_identity>
