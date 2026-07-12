<contents>

- `<template>` — JSON header, stdin forms, and canonical body
- `<field_guidance>` — frontmatter and body-field ownership

</contents>

<template>
This reference defines the JSON header and stdin form, body template, and field guidance for frontmatter and body sections.

The session file content has two parts: a header of caller-supplied fields and the markdown body below.

Creating a new session file pipes to `spx session handoff`. stdin is a single JSON header object on the first line, then the body bytes verbatim — no YAML frontmatter, and a leading `#` or `---` in the body is literal. Before filing, resolve the current runtime identity verbatim (`printenv CODEX_THREAD_ID` in Codex; `printenv CLAUDE_SESSION_ID` in Claude Code) and STOP when it is empty. The command writes `<SESSION_FILE>`, renders the stored YAML frontmatter from the header, and prefills `created_at` and `agent_session_id`. When the handoff points at a pushed work branch, including a linked pool worktree detached to `origin/<default-branch>` after pushing, the header supplies `git_ref` and the CLI verifies it exists on `origin`; when the work has already reached the default branch or no work branch must be preserved, omit `git_ref` and let the CLI derive the branch name or commit SHA from git context. Before filing, record the expected anchor: the supplied work branch, the current default branch name, or the full detached HEAD SHA. After filing, read the session through `spx session show --json <HANDOFF_ID>` and require its stored `git_ref` to equal that expected anchor and its stored `agent_session_id` to equal the runtime identity before treating the handoff as verified. The JSON header carries the caller-supplied fields:

```text
{"priority": "medium", "goal": "[Output-shaped deliverable or target end-state]", "next_step": "[The first concrete action for pickup]", "git_ref": "[optional pushed work branch]", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}
```

The workflow chooses its stdin form by harness: interactive Claude Code and Codex sessions use a quoted heredoc; programmatic runners that require one physical command line use `printf '%s\n'` with one argument per output line piped to `spx session handoff`. Both forms send the same bytes to stdin. Never assemble the body through temporary files, helper files, command substitution, or post-hoc text substitution.

Interactive Claude Code and Codex sessions use this quoted-heredoc form:

```bash
spx session handoff <<'SPX_SESSION_HANDOFF'
{"priority": "medium", "goal": "...", "next_step": "...", "git_ref": "<work-branch>", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}
<metadata>
  timestamp: [UTC timestamp]
  product: [Product name from cwd]
  git_ref: [work branch]
  git_status: clean
</metadata>
SPX_SESSION_HANDOFF
```

Programmatic runners that require one physical command line use this form. The rendered command may wrap visually; keep it on one physical line. Literal apostrophes inside a line use the single-quote splice `'"'"'`. Do not use heredocs or backslash-newline continuations in this form:

```bash
printf '%s\n' '{"priority": "medium", "goal": "...", "next_step": "...", "git_ref": "<work-branch>", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}' '<metadata>' '  timestamp: [UTC timestamp]' '  product: [Product name from cwd]' '  git_ref: [work branch]' '  git_status: clean' '</metadata>' | spx session handoff
```

**Body** — the content piped after the JSON header:

```text
<metadata>
  timestamp: [UTC timestamp]
  product: [Product name from cwd]
  git_ref: [value from frontmatter git_ref — the branch or commit anchor /pickup uses]
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

- [Live identifiers and their last-observed state — PR ids use `PR #<number>`; run / image / job ids include status or conclusion]
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
- **`goal`**: Required, non-empty continuation objective. Name the deliverable or target end-state, not the activity that will produce it. Avoid opening activity verbs such as "Fix", "Finish", "Author", "Implement", or "Update"; `spx session list` and `spx session todo` truncate this field, so the first words carry the scanning value. A session `goal` is a one-time target state, so present or past-participle end-states often read best ("X passing", "Y built and Z un-EXCLUDEd", "The N-case eval suite merged"). Examples:
  - `Fix spec-tree /contextualize so explicit full-path governing references load` -> `spec-tree /contextualize that loads explicit full-path governing references`
  - `Author the instructions plugin's first audit-skills [eval] suite` -> `The instructions plugin's first audit-skills [eval] suite`
- **`next_step`**: Required, non-empty first action for pickup. Write this field imperatively: name the skill, command, review step, or file inspection that should happen first.
- **JSON header**: Carries the caller-supplied fields — `priority`, `goal`, `next_step`, `git_ref`, optional `specs`, optional `files`. Do not put `created_at` or `agent_session_id` in the header; `spx session handoff` prefills those when it renders the stored frontmatter.
- **Stdin form**: In interactive Claude Code and Codex sessions, use a quoted heredoc whose first line is the JSON header and whose remaining lines are the body. In programmatic runners that require one physical command line, use `printf '%s\n'` with each argument representing one output line and pipe it to `spx session handoff`; keep the pipeline on one physical shell line. Literal apostrophes inside a single-quoted `printf` line use `'"'"'`.
- **`git_ref`**: For feature-branch handoffs, supply the pushed work branch in the JSON header; `spx session handoff` records it after verifying the branch exists on `origin`, and `/pickup` fetches and checks out that branch in a pool worktree. This includes linked pool-worktree releases: after the work branch is pushed and the worktree is detached to `origin/<default-branch>` for the CLI git-context gate, the header still supplies the pushed work branch so the recorded anchor remains the branch `/pickup` checks out. For default-branch or commit-SHA handoffs with no work branch to preserve, omit `git_ref`; the command derives a branch name for a main checkout or a commit SHA for a detached anchor, and `/pickup` reads that anchor in place. The persistence precondition (`${CLAUDE_SKILL_DIR}/workflows/04-execute.md` `<release_work_branch>`) guarantees any supplied work branch exists on origin and is not behind local.
- **`agent_session_id`**: Required for every fresh handoff and prefilled by `spx session handoff` from the runtime environment (`$CLAUDE_SESSION_ID` for Claude Code, `$CODEX_THREAD_ID` for Codex). Resolve the expected value before filing, STOP when it is empty, and require the stored value to match exactly. Do not supply it in the JSON header.
- **`created_at`**: ISO 8601 UTC timestamp written by `spx session handoff`. Do not supply it in the JSON header.
- **`specs`**: Optional auto-injection list for spec or decision files pickup should read. Use repository-relative paths.
- **`files`**: Optional auto-injection list for source, test, or workflow files pickup should read. Use repository-relative paths.
- **`<nodes>`**: One entry per anchored node. Omit `Remaining` if a PLAN.md was written — the next Claude context will read that.
- **`<state_at_handoff>`**: OPTIONAL. Only observable external-infrastructure state the next session cannot re-derive from the repository — live PR/run/image/job ids and their status, deployed inventories, in-flight workflows. Record every pull-request identifier in canonical `PR #<number>` form so `/pickup` can parse and reconcile it. Omit the section entirely when the repository already carries everything the next session needs. Guide the next pickup from the state in prose; do not encode fixed if-then branches.
- **`<constraints>`**: OPTIONAL. Session-specific normative rules (NEVER X) that hold for this continuation. Omit when there are none. A rule that always holds belongs in methodology or CLAUDE.md, not a per-session file.
- **`<coordination>`**: Thin. Cross-cutting context that is neither observable external state (`<state_at_handoff>`) nor a normative rule (`<constraints>`): why the handoff exists, dependencies between nodes, environment notes, open questions. Only what cannot be reconstructed from the spec tree or git history. If in doubt, leave it out.
- **`<incorporated_sessions>`**: Include when the claimed-session set or the current thread partition's `archive_ids` is non-empty. List every claimed session incorporated into this continuation and only the artifacts this fresh handoff replaces, with archive disposition. Omit the section only when both sets are empty. Every listed artifact id belongs to exactly one thread partition and is archived only after that partition's continuation is verified.

</field_guidance>
