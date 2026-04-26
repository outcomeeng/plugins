<template>
Write this content to `<SESSION_FILE>` using the Write tool:

```text
---
priority: medium
tags: [node-slug-1, node-slug-2, tech-stack]
agent_session_id: [prefilled by spx session handoff]
created_at: [prefilled by spx session handoff]
---
<metadata>
  timestamp: [UTC timestamp]
  project: [Project name from cwd]
  git_branch: [Current branch]
  git_status: [clean | dirty]
  working_directory: [Full path]
</metadata>

<nodes>
Spec-tree nodes worked on. The receiving agent should invoke
`/contextualizing` on each before starting work.

- `spx/{path-to-node}`
  - Status: [tests passing | partially implemented | spec only | architected | etc.]
  - Done: [What was accomplished on this node]
  - Remaining: [What's left — omit if captured in PLAN.md]
  - Escape hatches: [PLAN.md written | ISSUES.md written | none]

</nodes>

<skills>

## Critical — invoke before starting work
- `/understanding` — load spec tree methodology
- `/contextualizing {node-path}` — load target context for each node above

## Missed — caused problems when skipped
- [skill name] — [what went wrong and why it matters]

## Next action
- [skill to invoke] — [what to do and why]
- TDD flow position: step [N] ([step name]) on `spx/{node-path}`

</skills>

<persisted>
What was captured durably during session closure.

- Committed: [files committed during this session, including the final handoff commit]
- Uncommitted: [files still dirty after the handoff commit — foreign changes only]
- Insights: [what was written to CLAUDE.md, memory, or skills]
- Escape hatches: [PLAN.md / ISSUES.md written and in which nodes]

</persisted>

<coordination>
Cross-cutting context that doesn't belong to any single node.
Only include information that CANNOT be derived from the spec tree or git history.

- [Why the session ended]
- [Dependencies between nodes being worked on]
- [Environment or setup notes]
- [Open questions or pending decisions]

</coordination>

<incorporated_sessions>
- [session-id] — archived after this handoff
- [session-id] — archived after this handoff
</incorporated_sessions>
```

</template>

<field_guidance>

- **`priority`**: `high` if tests are failing or a blocker exists; `medium` for normal continuation; `low` for exploratory or low-urgency work.
- **`tags`**: Node slugs (strip the integer prefix — `21-test-harness.enabler` → `test-harness`) plus the language or technology stack. **Never use meta-terms that apply to every session**: `plan`, `handoff`, `session`, `continuation`, `pickup`, `release`, `commit`. If a word describes the session mechanism rather than its subject, it is forbidden as a tag.
- **`agent_session_id`**: Prefilled by `spx session handoff` from the runtime environment (`$CLAUDE_SESSION_ID` for Claude Code, `$CODEX_THREAD_ID` for Codex). Preserve the value as written; do not overwrite it. If blank (hook not active when `spx` ran), `timestamp` + `working_directory` + `git_branch` in `<metadata>` uniquely identify the session.
- **`created_at`**: ISO 8601 UTC timestamp written by `spx session handoff`. Preserve the value as written.
- **`<nodes>`**: One entry per anchored node. Omit `Remaining` if a PLAN.md was written — the next agent will read that.
- **`<skills> ## Missed`**: Only include if skipping that skill caused a real problem. Omit the section entirely if nothing was missed.
- **`<coordination>`**: Thin. Only cross-cutting context that cannot be reconstructed from the spec tree or git history. If in doubt, leave it out.
- **`<incorporated_sessions>`**: Include ONLY when the in-scope set resolved by `<resolve_session_scope>` is non-empty (at least one session is being archived as part of this closure). Omit the section entirely on a fresh handoff with no pickup. Every listed session must also be archived by workflow 04. Do NOT list a mid-session artifact that is being rewritten in place — this file IS that artifact.

</field_guidance>
