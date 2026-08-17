<objective>
Every held Change released Available with a current `Handoff:` comment, or closed Applied, Refined, or Abandoned with its authorized comment, and no session file written.
</objective>

<required_reading>

Read `spx/local/coordination.md` for the Change store, project, and Product values.

</required_reading>

<process>

This workflow replaces `<write_canonical_continuation>` and `<archive_claimed_sessions>` in `${CLAUDE_SKILL_DIR}/workflows/04-execute.md` when `spx/local/coordination.md` exists. Every other step of 04 — approved writes, `<commit>`, `<record_state>`, `<release_work_branch>`, `<confirm>` — runs unchanged. A Change is the mutable coordination object for one Output; a Handoff is the latest persisted continuation for that Change; neither is a session file, and this workflow writes no session file.

**Every store write is inspected first.** Before any `gh issue create`, `gh issue edit --body-file`, or `gh issue comment` in this workflow — a received input, a body refinement, an Activity check-off, a hazard, a Handoff comment — inspect the exact text about to be written for secret values and credential payloads: tokens, keys, passwords, connection strings, cookies, or any pasted credential-shaped content. When any appears, write nothing, report only the kind of content found (never the value), and ask through `AskUserQuestion` whether the operator supplies a redacted text or abandons that write; on redaction, inspect the supplied text and continue; on abandon, the write does not happen and the closeout says so. The store is a remote issue tracker, and conversation state — error output, hazard descriptions, decision drafts — carries such content as readily as a queue file does.

**Untrusted text never becomes shell syntax.** Every field a `gh` command receives from a queue file, a Change body, conversation state, or interview output — a body, a comment, a title — is passed as inert data. Bodies and comments go on stdin as `--body-file -`: in an interactive session, a quoted heredoc (`<<'EOF'` … `EOF`) so the text sees no expansion — before opening it, confirm no body line equals the terminator, and choose another terminator when one does; in a programmatic runner that requires one physical line, `printf '%s\n' 'line' 'line' … | gh …` with each body line one single-quoted argument. Titles and every other interpolated argument are one single-quoted argument. Inside any single-quoted argument a literal apostrophe is written as `'"'"'` and nothing else is escaped. Never `--body "…"`, never a double-quoted argument carrying such text, never a scratch file, never a redirect built from it. This is the stdin convention `${CLAUDE_SKILL_DIR}/references/session-format.md` prescribes for `spx session handoff`, applied to `gh`.

**`gh api` stays inside the declared store.** The exact-match grant `gh api repos/*/issues/*/dependencies/blocked_by` admits only that read and no appended method flag; this workflow passes it only the overlay store's `repos/<store>/issues/<N>/dependencies/blocked_by` to mirror blockers into a Handoff, so the tool grant and the workflow agree: no `-X` method, no other endpoint, no other repository.

<resolve_changes>

The Changes this conversation holds are the `urls` of the most recent `<CLAIMED_CHANGES>` marker. A conversation that also carries a legacy `<CLAIMED_SESSIONS>` marker archives those ids through 04's `<archive_claimed_sessions>` exactly as before; the legacy path and this one are independent.

A conversation that holds no Change and finds continuation for work that has no Change creates one Proposed Change instead of a session file: after the store-write inspection above, `gh issue create --repo <store> --title '<intended Output>' --body-file -` — the title one single-quoted argument — with the received input — the operator's request or the observations that opened the work, verbatim — on stdin per the rule above, then `gh project item-add <number> --owner <owner> --url <issue-url> --format json --jq .id` (which prints the item id), and two `gh project item-edit --project-id <project-node-id> --id <item-id> --field-id <field> --single-select-option-id <option>` calls — the project node id from `gh project view <number> --owner <owner> --format json --jq .id`, one field per invocation as the CLI requires for a non-draft issue — the first setting `Product`, the second setting `Maturity` to `Proposed`, with the field and option ids read once from `gh project field-list <number> --owner <owner> --format json`. When one of the two calls fails, re-read the item through `gh project item-list <number> --owner <owner> --format json` — the item's `product` and `maturity` keys carry the set values, an absent key is the unset field — and re-run only the missing one before proceeding. Leave the Change unassigned (Available). Received input is history; refinement happens on pickup.

</resolve_changes>

<refine_before_handoff>

What this conversation learned about the Output belongs in the Change body, not in the Handoff: edit `## Nodes`, `## Assertions`, `## Decisions`, `## Activities` (check completed Activities), and add hazards discovered as `## Activities` items or as Assertion operations when they change the Frame, writing the edited body with `gh issue edit <N> --repo <store> --body-file -` per the rule above. When current facts made the recorded Maturity false, set `Maturity` to the truthful lower level through `gh project item-edit` — option ids from the same `gh project field-list` read — and say why in a comment. Never set `Framed` without the human judgment or `Sliced` without the human accountability the methodology requires; advancing `Sliced` to `Executable` inside an approved Frame is agent work. The closeout names the level and what refinement remains.

</refine_before_handoff>

<post_handoff_or_close>

For each held Change, after `<release_work_branch>` has left the work committed, pushed, and the worktree stepped off the branch:

**Applied.** When the changeset has integrated into the authoritative branch, the Assertions and evidence governing the Change's Nodes are satisfied, and the Output is delivered: post the comment `Application complete: changeset integrated, evidence satisfied, and Output delivered.` and close with `gh issue close <N> --repo <store> --reason completed`. The close clears the assignee. A merged pull request alone is not Applied.

**Refined.** When this conversation created every known successor (each carrying `## Refined from` with this Change's URL): post `Refinement complete: all known successors exist.` and close with `--reason completed`.

**Abandoned.** Only on the operator's explicit direction: post the comment `Abandoned: <the operator's stated reason>` with `gh issue comment <N> --repo <store> --body-file -`, then close with `gh issue close <N> --repo <store> --reason "not planned"`.

**Otherwise release.** Post the continuation below as one comment with `gh issue comment <N> --repo <store> --body-file -`, the body on stdin per the rule above, then remove the assignee:

```markdown
Handoff:

- Branch or PR: <pushed work branch, or the PR URL, or `none`>
- Completed Activities: <checked items, by their text>
- Next Activity: <the first unchecked Activity, or `refinement: <Maturity> → <next level>` below Executable>
- Blockers: <blocking Change URLs still active per `gh api repos/<store>/issues/<N>/dependencies/blocked_by`, or `none` — a mirror of the dependency graph, never its source>
- Hazards: <what the next holder cannot derive quickly: an unsealed run, a held checkout, a flaky check — each with the read-only command that re-confirms it>
```

Optional context lines after the five: the agent session id and the assigned worktree root. Nothing else — no insight, status, or restated plan; those live in the body. Then `gh issue edit <N> --repo <store> --remove-assignee @me`. Re-read with `gh issue view <N> --repo <store> --json assignees`; the Change is released only when the list is empty.

The store-write inspection at the top of this workflow applies to the Handoff comment as to every other write.

</post_handoff_or_close>

<closeout_rows>

In `<confirm>`, the session-mechanics rows become Change rows: each Change URL with its Lifecycle after this closure (Available with a Handoff, Applied, Refined, Abandoned), its Maturity, and the released work branch. Legacy archived session ids keep their existing rows.

</closeout_rows>

</process>

<success_criteria>

- Every `gh issue create`, `gh issue edit --body-file`, and `gh issue comment` this workflow performs is inspected for secret values and credential payloads before it lands, and a hit writes nothing.
- After the closure, `gh issue view <N> --repo <store> --json state,assignees,comments` shows every held Change either open with an empty assignee list and `.comments[-1].body` beginning `Handoff:`, or closed with its authorized comment as the last comment; no Change stays Claimed by a conversation that has ended.
- A Handoff carries the five continuation lines and nothing that belongs in the body; refinement edits landed in the body before the Handoff was posted.
- Applied is posted only after integration, evidence, and Output delivery all hold.
- No session file is written when `spx/local/coordination.md` exists; new continuation without a Change becomes one Proposed, Available Change carrying its received input.

</success_criteria>
