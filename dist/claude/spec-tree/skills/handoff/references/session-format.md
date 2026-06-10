<template>
The session file content has two parts: a header of caller-supplied fields and the markdown body below. How the header is expressed depends on the path.

**Path C (new session file)** pipes to `spx session handoff`. stdin is a single JSON header object on the first line, then the body bytes verbatim — no YAML frontmatter, and a leading `#` or `---` in the body is literal. The command writes `<SESSION_FILE>`, renders the stored YAML frontmatter from the header, and prefills `created_at`, `agent_session_id`, and `git_ref`. The JSON header carries only the caller-supplied fields:

```text
{"priority": "medium", "goal": "[Why this continuation exists]", "next_step": "[The first concrete action for pickup]", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}
```

**Path B (rewrite in place)** writes the stored-file format directly to the existing artifact, preserving its existing `created_at`, `agent_session_id`, and `git_ref` values. The stored format is YAML frontmatter followed by the body:

```text
---
created_at: [preserve on rewrite]
agent_session_id: [preserve on rewrite]
priority: medium
git_ref: [preserve on rewrite]
goal: [Why this continuation exists]
next_step: [The first concrete action for pickup]
specs:
  - spx/{path-to-node}/{node-file}.md
files:
  - src/{path-to-file}
---
```

**Body (both paths)** — for Path C this is the content piped after the JSON header; for Path B it follows the YAML frontmatter above:

```text
<metadata>
  timestamp: [UTC timestamp]
  product: [Product name from cwd]
  git_ref: [value from frontmatter git_ref]
  git_status: [clean | dirty]
</metadata>

<nodes>
Spec-tree nodes worked on. The receiving Claude context should invoke
`/contextualizing` on each before starting work.

- `spx/{path-to-node}`
  - Status: [tests passing | partially implemented | spec only | architected | etc.]
  - Done: [What was accomplished on this node]
  - Remaining: [What's left — omit if captured in PLAN.md]
  - Coordination notes: [PLAN.md written | ISSUES.md written | none]

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
- Coordination notes: [PLAN.md / ISSUES.md written and in which nodes]

</persisted>

<state_at_handoff>
OPTIONAL. Observable external-infrastructure state the next pickup needs and
cannot re-derive from the spec tree, PLAN.md/ISSUES.md, or git history. Include
only what the next agent would otherwise re-discover through a live-system query
(a CI, container, or cluster CLI, for example). Omit this section entirely when
every fact the next agent needs already lives in the repository.

- [Live identifiers and their last-observed state — PR / run / image / job ids with status or conclusion]
- [In-flight workflows or deployments that bear on the first action]
- [Inventory or baseline counts the next agent compares against]
- [What to re-confirm with one read-only command before acting]

Guide the next pickup from this state in prose. Do not encode the first action as
fixed if-then branches — the next agent decides freely from the observed state.

</state_at_handoff>

<constraints>
OPTIONAL. Normative rules that hold for this continuation regardless of what the
next agent observes. Scope them to this session's work — a rule that always holds
belongs in methodology or CLAUDE.md, not repeated in a per-session file. Omit this
section when there are none.

- NEVER [action] — [reason]

</constraints>

<coordination>
Cross-cutting context that is neither observable external state (that goes in
<state_at_handoff>) nor a normative rule (that goes in <constraints>): why this
handoff exists, dependencies between the nodes worked on, environment notes, open
questions. Include only what cannot be reconstructed from the spec tree or git
history.

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
- **`goal`**: Required, non-empty continuation objective. Use one sentence that identifies the user-visible outcome, not a generic handoff phrase.
- **`next_step`**: Required, non-empty first action for pickup. Name the skill, command, review step, or file inspection that should happen first.
- **Path C JSON header**: Carries only the caller-supplied fields — `priority`, `goal`, `next_step`, optional `specs`, optional `files`. Do not put `created_at`, `agent_session_id`, or `git_ref` in the header; `spx session handoff` prefills those when it renders the stored frontmatter.
- **`git_ref`**: Prefilled by `spx session handoff` from git context — the branch name for a main checkout on a branch, or a commit SHA for a detached or linked-worktree handoff. Preserve the value as written; do not overwrite it during Path B rewrites. Caller-supplied values are ignored for Path C.
- **`agent_session_id`**: Prefilled by `spx session handoff` from the runtime environment (`$CLAUDE_SESSION_ID` for Claude Code, `$CODEX_THREAD_ID` for Codex). Preserve the value as written; do not overwrite it. If absent, `created_at` + `git_ref` identify the session context.
- **`created_at`**: ISO 8601 UTC timestamp written by `spx session handoff`. Preserve the value as written.
- **`specs`**: Optional auto-injection list for spec or decision files pickup should read. Use repository-relative paths.
- **`files`**: Optional auto-injection list for source, test, or workflow files pickup should read. Use repository-relative paths.
- **`<nodes>`**: One entry per anchored node. Omit `Remaining` if a PLAN.md was written — the next Claude context will read that.
- **`<skills> ## Missed`**: Only include if skipping that skill caused a real problem. Omit the section entirely if nothing was missed.
- **`<state_at_handoff>`**: OPTIONAL. Only observable external-infrastructure state the next agent cannot re-derive from the repository — live PR/run/image/job ids and their status, deployed inventories, in-flight workflows. Omit the section entirely when the repository already carries everything the next agent needs. Guide the next pickup from the state in prose; do not encode fixed if-then branches.
- **`<constraints>`**: OPTIONAL. Session-specific normative rules (NEVER X) that hold for this continuation. Omit when there are none. A rule that always holds belongs in methodology or CLAUDE.md, not a per-session file.
- **`<coordination>`**: Thin. Cross-cutting context that is neither observable external state (`<state_at_handoff>`) nor a normative rule (`<constraints>`): why the handoff exists, dependencies between nodes, environment notes, open questions. Only what cannot be reconstructed from the spec tree or git history. If in doubt, leave it out.
- **`<incorporated_sessions>`**: Include ONLY when the in-scope set resolved by `<resolve_session_scope>` is non-empty (at least one session is being archived as part of this closure). Omit the section entirely on a fresh handoff with no pickup. Every listed session must also be archived by workflow 04. Do NOT list a mid-session artifact that is being rewritten in place — this file IS that artifact.

</field_guidance>
