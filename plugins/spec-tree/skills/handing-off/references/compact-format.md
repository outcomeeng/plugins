# Compact Handoff Format

When a conversation compacts before explicit closure, `compactPrompt` (in `~/.claude/settings.json`) **appends** supplemental instructions to Claude Code's built-in compaction prompt — it does not replace it. The built-in prompt produces a 9-section summary (Primary Request, Key Technical Concepts, Files, Errors, Problem Solving, User Messages, Pending Tasks, Current Work, Next Step); the `compactPrompt` value adds spec-tree-specific sections after that. The PostCompact hook persists the full output to `.spx/compact-summary.md`; the `session-resume` SessionStart hook injects it into the next session's context via stdout.

This is a **prospective session file**: it captures everything the handing-off workflow would have written, but without user approval and without tool execution. The receiving agent treats it as a starting point and applies the persistence proposal through the normal `/picking-up` → `/handing-off` flow.

## Relationship to session-format.md

| Aspect            | Session file (session-format.md)         | Compact summary (this file)                  |
| ----------------- | ---------------------------------------- | -------------------------------------------- |
| Produced by       | Workflow 04 (with tools, after approval) | Built-in prompt + `compactPrompt` supplement |
| Stored in         | `.spx/sessions/todo/`                    | `.spx/compact-summary.md`                    |
| Consumed by       | `/picking-up`                            | `session-resume` hook (context injection)    |
| Approved by user  | Yes (workflow 03)                        | No — prospective only                        |
| Persistence items | Already written                          | Proposed — must be approved in next session  |

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

When `session-resume` injects this document at SessionStart, the receiving agent:

1. Reads the **Nodes** section and treats each path as a node to `/contextualizing` before any work.
2. Reads the **Starting Point** section and uses it as the first action.
3. Reads the **Persistence Proposal** and presents it to the user via `AskUserQuestion` (workflow 03 format) before writing anything.
4. Does NOT treat this as a committed session file — no `spx session pickup` needed; this is context injection, not queue management.

Approved items from the persistence proposal are written and committed as if they had come from a normal handing-off workflow 04.
