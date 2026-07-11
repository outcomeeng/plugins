<template>
## Contents

- Path C JSON header and stdin form
- Path B stored-file format
- Body template shared by Path B and Path C
- Field guidance for frontmatter and body sections

The session file content has two parts: a header of caller-supplied fields and the markdown body below. How the header is expressed depends on the path.

**Path C (new session file)** pipes to `spx session handoff`. stdin is a single JSON header object on the first line, then the body bytes verbatim — no YAML frontmatter, and a leading `#` or `---` in the body is literal. The command writes `<SESSION_FILE>`, renders the stored YAML frontmatter from the header, prefills `created_at` and `agent_session_id`, and records the header's `git_ref` as the work branch after verifying it exists on `origin`. The JSON header carries the caller-supplied fields:

```text
{"priority": "medium", "goal": "[Output-shaped deliverable or target end-state]", "next_step": "[The first concrete action for pickup]", "git_ref": "[work branch the work is pushed to — the stable anchor /pickup checks out]", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}
```

Path C chooses its stdin form by harness: interactive Claude Code and Codex sessions use a quoted heredoc; programmatic runners that require one physical command line use `printf '%s\n'` with one argument per output line piped to `spx session handoff`. Both forms send the same bytes to stdin. Never assemble the body through temporary files, helper files, command substitution, or post-hoc text substitution.

**Path B (rewrite in place)** writes the stored-file format directly to the existing artifact, preserving its existing `created_at`, `agent_session_id`, and `git_ref` values. The stored format is YAML frontmatter followed by the body:

```text
---
created_at: [preserve on rewrite]
agent_session_id: [preserve on rewrite]
priority: medium
git_ref: [preserve on rewrite]
goal: [Output-shaped deliverable or target end-state]
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
  git_ref: [value from frontmatter git_ref — the work branch /pickup checks out]
  git_status: [clean | dirty]
</metadata>

<nodes>
Spec-tree nodes worked on. `/pickup` selects the first `/contextualize` target
from `next_step` and these entries, then loads additional nodes only when the next
action touches them.

- `spx/{path-to-node}`
  - Status: [tests passing | partially implemented | spec only | architected | etc.]
  - Done: [What was accomplished on this node]
  - Remaining: [What's left — omit if captured in PLAN.md]
  - Coordination notes: [PLAN.md written | ISSUES.md written | none]

</nodes>

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
only what the next session would otherwise re-discover through a live-system query
(a CI, container, or cluster CLI, for example). Omit this section entirely when
every fact the next session needs already lives in the repository.

- [Live identifiers and their last-observed state — PR / run / image / job ids with status or conclusion]
- [In-flight workflows or deployments that bear on the first action]
- [Inventory or baseline counts the next session compares against]
- [What to re-confirm with one read-only command before acting]

Guide the next pickup from this state in prose. Do not encode the first action as
fixed if-then branches — the next session decides freely from the observed state.

</state_at_handoff>

<constraints>
OPTIONAL. Normative rules that hold for this continuation regardless of what the
next session observes. Scope them to this session's work — a rule that always holds
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
- **`goal`**: Required, non-empty continuation objective. Write the field in the output-shaped style from `instructions:agent-prompt-standards` `<objective_shape>`: name the deliverable or target end-state, not the activity that will produce it. Avoid opening activity verbs such as "Fix", "Finish", "Author", "Implement", or "Update"; `spx session list` and `spx session todo` truncate this field, so the first words carry the scanning value. A skill `<objective>` is atemporal ("X that does Y"); a session `goal` is a one-time target state, so present or past-participle end-states often read best ("X passing", "Y built and Z un-EXCLUDEd", "The N-case eval suite merged"). Examples:
  - `Fix spec-tree /contextualize so explicit full-path governing references load` -> `spec-tree /contextualize that loads explicit full-path governing references`
  - `Author the instructions plugin's first audit-skills [eval] suite` -> `The instructions plugin's first audit-skills [eval] suite`
- **`next_step`**: Required, non-empty first action for pickup. Write this field imperatively: name the skill, command, review step, or file inspection that should happen first.
- **Path C JSON header**: Carries the caller-supplied fields — `priority`, `goal`, `next_step`, `git_ref`, optional `specs`, optional `files`. Do not put `created_at` or `agent_session_id` in the header; `spx session handoff` prefills those when it renders the stored frontmatter.
- **Path C stdin form**: In interactive Claude Code and Codex sessions, use a quoted heredoc whose first line is the JSON header and whose remaining lines are the body. In programmatic runners that require one physical command line, use `printf '%s\n'` with each argument representing one output line and pipe it to `spx session handoff`; keep the pipeline on one physical shell line. Literal apostrophes inside a single-quoted `printf` line use `'"'"'`.
- **`git_ref`**: For Path C, supply the pushed work branch in the JSON header; `spx session handoff` records it after verifying the branch exists on `origin` (omit it only when the work landed on the default branch with no feature branch, and the command derives the base from git context — a branch name for a main checkout, a commit SHA for a detached or pool-worktree handoff). `git_ref` is the single anchor `/pickup` reads: it fetches and checks out the branch `git_ref` names in a pool worktree, and reads in place when `git_ref` is the default branch or a commit SHA. The persistence precondition (`workflows/04-execute.md` `<release_work_branch>`) guarantees the work branch exists on origin and is not behind local. Preserve the value as written; do not overwrite it during Path B rewrites.
- **`agent_session_id`**: Prefilled by `spx session handoff` from the runtime environment (`$CLAUDE_SESSION_ID` for Claude Code, `$CODEX_THREAD_ID` for Codex). Preserve the value as written; do not overwrite it. If absent, `created_at` + `git_ref` identify the session context.
- **`created_at`**: ISO 8601 UTC timestamp written by `spx session handoff`. Preserve the value as written.
- **`specs`**: Optional auto-injection list for spec or decision files pickup should read. Use repository-relative paths.
- **`files`**: Optional auto-injection list for source, test, or workflow files pickup should read. Use repository-relative paths.
- **`<nodes>`**: One entry per anchored node. Omit `Remaining` if a PLAN.md was written — the next Claude context will read that.
- **`<state_at_handoff>`**: OPTIONAL. Only observable external-infrastructure state the next session cannot re-derive from the repository — live PR/run/image/job ids and their status, deployed inventories, in-flight workflows. Omit the section entirely when the repository already carries everything the next session needs. Guide the next pickup from the state in prose; do not encode fixed if-then branches.
- **`<constraints>`**: OPTIONAL. Session-specific normative rules (NEVER X) that hold for this continuation. Omit when there are none. A rule that always holds belongs in methodology or CLAUDE.md, not a per-session file.
- **`<coordination>`**: Thin. Cross-cutting context that is neither observable external state (`<state_at_handoff>`) nor a normative rule (`<constraints>`): why the handoff exists, dependencies between nodes, environment notes, open questions. Only what cannot be reconstructed from the spec tree or git history. If in doubt, leave it out.
- **`<incorporated_sessions>`**: Include ONLY when the claimed-session set resolved by `<resolve_claimed_sessions>` is non-empty (at least one session is being archived as part of this closure). Omit the section entirely on a fresh handoff with no pickup. Every listed session must also be archived by workflow 04. Do NOT list a mid-session artifact that is being rewritten in place — this file IS that artifact.

</field_guidance>
