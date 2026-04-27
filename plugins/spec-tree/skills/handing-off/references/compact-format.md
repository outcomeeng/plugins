# Compact Handoff Format

When a conversation compacts before explicit closure, `compactPrompt` (in `~/.claude/settings.json`) **appends** supplemental instructions to Claude Code's built-in compaction prompt — it does not replace it. The built-in prompt produces a 9-section summary (Primary Request, Key Technical Concepts, Files, Errors, Problem Solving, User Messages, Pending Tasks, Current Work, Next Step); the `compactPrompt` value adds spec-tree-specific sections after that. The PostCompact hook persists the full output to `.spx/sessions/tmp/compact-<session_id>.md`; the `session-resume` SessionStart hook atomically claims the file (renaming it to `.processing-<new_session_id>`) and injects its content into the next session's context via stdout.

The receiving session executes the handing-off persist and commit phase (workflows 03–04): it presents the Persistence Proposal to the user, writes approved items, creates a session file via `spx session handoff`, and runs `compact-done` to remove the claimed compact file. Subsequent sessions resume from that session file via `/picking-up`.

## Relationship to session-format.md

| Aspect            | Session file (session-format.md)         | Compact summary (this file)                             |
| ----------------- | ---------------------------------------- | ------------------------------------------------------- |
| Produced by       | Workflow 04 (with tools, after approval) | Built-in prompt + `compactPrompt` supplement            |
| Stored in         | `.spx/sessions/todo/`                    | `.spx/sessions/tmp/compact-<session_id>.md`             |
| Consumed by       | `/picking-up`                            | `session-resume` → receiving agent creates session file |
| Approved by user  | Yes (workflow 03)                        | No — prospective only                                   |
| Persistence items | Already written                          | Proposed — must be approved in next session             |

## Document structure

The authoritative structure is `compaction-prompt.md`. The built-in 9-section summary precedes these spec-tree-specific sections; Issues and Path Forward are omitted here because the built-in sections 4–5 (Errors, Problem Solving) and 7–9 (Pending Tasks, Current Work, Next Step) cover them.

| Section                    | Contents                                                                                 |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| `### Nodes`                | One bullet per node: path, what was done, TDD step, declared/specified/passing state     |
| `### Lessons`              | Routing only — `[Type] fact → destination`; what was learned is in built-in sections 4–5 |
| `### Skills`               | Critical skills to invoke; missed skills that caused problems                            |
| `### Starting Point`       | Node path, TDD step, first skill invocation                                              |
| `### Persistence Proposal` | Items requiring user approval before writing — omitted if nothing to propose             |
| `### Session Scope`        | In-scope session IDs; mid-session artifacts                                              |

## compactPrompt value

The prompt text is in `compaction-prompt.md` (same directory). Set it with:

```bash
jq --rawfile prompt plugins/spec-tree/skills/handing-off/references/compaction-prompt.md \
   '.compactPrompt = $prompt' ~/.claude/settings.json \
   > /tmp/claude-settings.tmp && mv /tmp/claude-settings.tmp ~/.claude/settings.json
```

## Receiving agent behavior

When `session-resume` injects the compact content at SessionStart, the receiving agent **must execute these steps as the first action, before responding to any user message**:

1. Reads ### Nodes and treats each path as a node to `/contextualizing` before any work.
2. Reads ### Starting Point as the first action.
3. Reads ### Persistence Proposal and presents it to the user via `AskUserQuestion` before writing anything.
4. Writes approved items and commits them.
5. Runs `spx session handoff` to create a session file in `.spx/sessions/todo/`. **Always create the session file, even when the Persistence Proposal is empty** — the session file is the canonical continuation required by subsequent agents.
6. Runs `compact-done` (path provided in the `session-resume` preamble) to remove the claimed compact file and `.spx/sessions/tmp/compact-active`.

No `spx session pickup` is needed — the compact context arrives via injection, not the queue. Subsequent sessions find the session file created in step 5 and resume via `/picking-up`.
