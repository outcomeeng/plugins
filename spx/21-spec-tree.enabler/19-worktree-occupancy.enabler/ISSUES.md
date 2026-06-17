# Issues: Worktree Occupancy

## SessionStart-only claiming leaves live sessions unaware of stale occupancy (RESOLVED)

`SessionStart` claiming alone is insufficient for worktree occupancy because a runtime may enter a session whose installed hook trust, plugin version, or startup execution did not establish a live claim. When `spx worktree status --format json` reports the running worktree as `stale` or `unclaimed`, the agent is operating inside the pool without model-visible claim awareness.

The repair is implemented in the `PreToolUse` hook path: before evaluating the normal load gate, the hook reads `spx worktree status --format json`, invokes `spx worktree claim --session-id <session-id>` when the status is `stale` or `unclaimed`, and emits model-visible context when it repairs or cannot repair the claim. The hook keeps `payload.session_id` as the primary identity source and falls back to runtime identity environment variables only when the payload omits the documented field.

## `spx worktree claim` cannot resolve the Codex controlling process

The live command `spx worktree claim --session-id 019ed48b-0465-79b2-ba88-8bf2838cd71a` in `/Users/shz/Code/outcomeeng/plugins/plugins-a` exits non-zero with `Error: worktree controlling process could not be resolved`, leaving `spx worktree status --format json` at `{"worktree":"plugins-a","status":"stale"}`.

The marketplace hook now exposes this failure through `PreToolUse` model-visible context, so the agent can observe the stale claim. The remaining fix belongs in the `spx` CLI worktree-claim implementation: a Codex session must be claimable from the hook subprocess, or the CLI must accept an explicit controlling-process identity supplied by the runtime hook contract.
