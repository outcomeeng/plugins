<objective>
Every held Change released Available with a current `Handoff:` comment, or closed Applied, Refined, or Abandoned with its authorized comment, and no session file written.
</objective>

<required_reading>

Read `spx/local/coordination.md` for the Change store, project, and Product values.

</required_reading>

<process>

This workflow replaces `<write_canonical_continuation>` and `<archive_claimed_sessions>` in `${SKILL_DIR}/workflows/04-execute.md` when `spx/local/coordination.md` exists. Every other step of 04 — approved writes, `<commit>`, `<record_state>`, `<release_work_branch>`, `<confirm>` — runs unchanged. A Change is the mutable coordination object for one Output; a Handoff is the latest persisted continuation for that Change; neither is a session file, and this workflow writes no session file.

<resolve_changes>

The Changes this conversation holds are the `urls` of the most recent `<CLAIMED_CHANGES>` marker. A conversation that also carries a legacy `<CLAIMED_SESSIONS>` marker archives those ids through 04's `<archive_claimed_sessions>` exactly as before; the legacy path and this one are independent.

A conversation that holds no Change and finds continuation for work that has no Change creates one Proposed Change instead of a session file: `gh issue create --repo <store> --title "<intended Output>" --body-file <scratch>` where `<scratch>` comes from `mktemp` and holds the received input — the operator's request or the observations that opened the work, verbatim, non-secret — then `gh project item-add`, and `Product` / `Maturity: Proposed` through `gh project item-edit` with the field and option ids read once from `gh project field-list <number> --owner <owner> --format json`. Delete the scratch file on every exit path. Leave the Change unassigned (Available). Received input is history; refinement happens on pickup.

</resolve_changes>

<refine_before_handoff>

What this conversation learned about the Output belongs in the Change body, not in the Handoff: edit `## Nodes`, `## Assertions`, `## Decisions`, `## Activities` (check completed Activities), and add hazards discovered as `## Activities` items or as Assertion operations when they change the Frame. When current facts made the recorded Maturity false, set `Maturity` to the truthful lower level through `gh project item-edit` — option ids from the same `gh project field-list` read — and say why in a comment. Never advance Maturity past Framed without the human judgment the methodology requires; the closeout names the level and what refinement remains.

</refine_before_handoff>

<post_handoff_or_close>

For each held Change, after `<release_work_branch>` has left the work committed, pushed, and the worktree stepped off the branch:

**Applied.** When the changeset has integrated into the authoritative branch, the Assertions and evidence governing the Change's Nodes are satisfied, and the Output is delivered: post the comment `Application complete: changeset integrated, evidence satisfied, and Output delivered.` and close with `gh issue close <N> --repo <store> --reason completed`. The close clears the assignee. A merged pull request alone is not Applied.

**Refined.** When this conversation created every known successor (each carrying `## Refined from` with this Change's URL): post `Refinement complete: all known successors exist.` and close with `--reason completed`.

**Abandoned.** Only on the operator's explicit direction: close with `--reason "not planned"`.

**Otherwise release.** Write the continuation below to a `mktemp` scratch file, post it as one comment with `gh issue comment <N> --repo <store> --body-file <scratch>` — never an inline `--body` string, whose bullets and colons break shell quoting — delete the scratch file, then remove the assignee:

```markdown
Handoff:

- Branch or PR: <pushed work branch, or the PR URL, or `none`>
- Completed Activities: <checked items, by their text>
- Next Activity: <the first unchecked Activity, or `refinement: <Maturity> → <next level>` below Executable>
- Blockers: <blocking Change URLs still active, or `none`>
- Hazards: <what the next holder cannot derive quickly: an unsealed run, a held checkout, a flaky check — each with the read-only command that re-confirms it>
```

Optional context lines after the five: the agent session id and the assigned worktree root. Nothing else — no insight, status, or restated plan; those live in the body. Then `gh issue edit <N> --repo <store> --remove-assignee @me`. Re-read `assignees`; the Change is released only when the list is empty.

Secret values and credential payloads never enter a body, comment, or Handoff.

</post_handoff_or_close>

<closeout_rows>

In `<confirm>`, the session-mechanics rows become Change rows: each Change URL with its Lifecycle after this closure (Available with a Handoff, Applied, Refined, Abandoned), its Maturity, and the released work branch. Legacy archived session ids keep their existing rows.

</closeout_rows>

</process>

<success_criteria>

- Every Change in `<CLAIMED_CHANGES>` ends Available with a current `Handoff:` comment and no assignee, or closed as Applied, Refined, or Abandoned with the matching authorized comment; no Change stays Claimed by a conversation that has ended.
- A Handoff carries the five continuation lines and nothing that belongs in the body; refinement edits landed in the body before the Handoff was posted.
- Applied is posted only after integration, evidence, and Output delivery all hold.
- No session file is written when `spx/local/coordination.md` exists; new continuation without a Change becomes one Proposed, Available Change carrying its received input.

</success_criteria>
