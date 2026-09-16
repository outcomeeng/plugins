<objective>
Every held Change either closed through its verified terminal transition or released Available with a current `Handoff:` comment and complete canonical state, with no session file written.
</objective>

<required_reading>

Read `spx/local/coordination.md` for the Change store, project, and Product values.

</required_reading>

<process>

This workflow fills two ordered insertion points in `${CLAUDE_SKILL_DIR}/workflows/04-execute.md` when `spx/local/coordination.md` exists. At `<write_canonical_continuation>`, run `<resolve_changes>` and `<refine_before_handoff>`, then return to 04 for `<release_work_branch>`. At `<archive_claimed_sessions>`, after branch release, run `<post_handoff_or_close>` and `<closeout_rows>` for held Changes while 04 archives any legacy claimed sessions. Every other step of 04 — approved writes, `<commit>`, `<record_state>`, `<release_work_branch>`, `<confirm>` — runs unchanged. A Change is the mutable coordination object for one Output; a Handoff is the latest persisted continuation for that Change; neither is a session file, and this workflow writes no session file.

**Every store write is inspected first.** Before any `gh issue create`, `gh issue edit --body-file`, or `gh issue comment` in this workflow — a received input, a body refinement, an Activity check-off, a hazard, a Handoff comment — inspect the exact text about to be written for secret values and credential payloads: tokens, keys, passwords, connection strings, cookies, or any pasted credential-shaped content. When any appears, write nothing, report only the kind of content found (never the value), and ask through `AskUserQuestion` whether the operator supplies a redacted text or abandons that write; on redaction, inspect the supplied text and continue; on abandon, the write does not happen and the closeout says so. The store is a remote issue tracker, and conversation state — error output, hazard descriptions, decision drafts — carries such content as readily as a queue file does.

**Untrusted text never becomes shell syntax.** Every field a `gh` command receives from a queue file, a Change body, conversation state, or interview output — a body, a comment, a title — is passed as inert data. Bodies and comments go on stdin as `--body-file -`: in an interactive session, a quoted heredoc (`<<'EOF'` … `EOF`) so the text sees no expansion — before opening it, confirm no body line equals the terminator, and choose another terminator when one does; in a programmatic runner that requires one physical line, `printf '%s\n' 'line' 'line' … | gh …` with each body line one single-quoted argument. Titles and every other interpolated argument are one single-quoted argument. Inside any single-quoted argument a literal apostrophe is written as `'"'"'` and nothing else is escaped. Never `--body "…"`, never a double-quoted argument carrying such text, never a scratch file, never a redirect built from it. This is the stdin convention `${CLAUDE_SKILL_DIR}/references/session-format.md` prescribes for `spx session handoff`, applied to `gh`.

**`gh api` stays inside the declared store.** The exact-match grant `gh api repos/*/issues/*/dependencies/blocked_by` admits only that read and no appended method flag; this workflow passes it only the overlay store's `repos/<store>/issues/<N>/dependencies/blocked_by` to mirror blockers into a Handoff, so the tool grant and the workflow agree: no `-X` method, no other endpoint, no other repository.

**Every Change transition is an ordered write with a complete readback.** Run `gh project item-list <number> --owner <owner> --format json`, select by exact issue URL, and require exactly one matching item; its `product`, `maturity`, and `status` keys are the canonical Product, Maturity, and Status values. Read those values together with `gh issue view <N> --repo <store> --json assignees,body,comments,state,stateReason,url`; never derive a field from issue prose. A transition records each successful write in order. When a required command fails, a required field is absent, or readback differs from the intended state, stop before every later mutation and report: the successful writes in order, the failed command or mismatched value, and the observed Product, Maturity, Status, assignees, issue state and reason, and newest `Claim:`, `Handoff:`, or terminal comment. Never repair a partial transition by guessing which later mutation would make it look complete.

**Legacy body metadata migrates only after canonical state is settled.** A leading prose line that carries `Product:`, `Maturity:`, `Lifecycle:`, or `Status:` is legacy input, never a fourth metadata store. Compare it with the project fields and the issue's edit, comment, and project-item history. When they disagree, reconstruct the latest intended value from that history; when the history does not decide, stop before editing the body and ask through `AskUserQuestion`. Write and verify the canonical project fields first. Then remove only the legacy metadata line with `gh issue edit <N> --repo <store> --body-file -` and re-read the body. New and refined bodies never add such a line.

<resolve_changes>

The Changes this conversation holds are the `urls` of the most recent `<CLAIMED_CHANGES>` marker. A conversation that also carries a legacy `<CLAIMED_SESSIONS>` marker archives those ids through 04's `<archive_claimed_sessions>` exactly as before; the legacy path and this one are independent.

A conversation that holds no Change and finds continuation for work that has no Change creates one Proposed Change instead of a session file. After the store-write inspection above:

1. Create the unassigned issue with `gh issue create --repo <store> --title '<intended Output>' --body-file -`, the received input on stdin and no Product, Maturity, Lifecycle, or Status line in the body.
2. Add it to the declared project with `gh project item-add <number> --owner <owner> --url <issue-url> --format json --jq .id`.
3. Resolve the project node id through `gh project view <number> --owner <owner> --format json --jq .id`, and resolve the Product, Maturity, and Status field and option ids once through `gh project field-list <number> --owner <owner> --format json`.
4. Run three separate `gh project item-edit` calls in this order: Product to the overlay's Product, Maturity to `Proposed`, Status to `Available`.
5. Read back the single project item and issue. Continue only when Product equals the overlay Product, Maturity is `Proposed`, Status is `Available`, and the assignee list is empty.

Every step uses the transition failure boundary above. A partial creation remains visible at its created issue URL and receives no Handoff until the complete Available state verifies. Received input is history; refinement happens on pickup.

</resolve_changes>

<refine_before_handoff>

What this conversation learned about the Output belongs in the Change body, not in the Handoff. Edit `## Nodes`, `## Assertions`, `## Decisions`, and `## Activities` (including completed Activities and newly discovered hazards), writing the body with `gh issue edit <N> --repo <store> --body-file -` per the rule above and without metadata prose. When current facts made the recorded Maturity false, write the truthful lower Maturity through `gh project item-edit`; never set `Framed` without the human judgment or `Sliced` without the human accountability the methodology requires. Advancing `Sliced` to `Executable` inside an approved Frame is agent work.

An in-place refinement completes through the release sequence below: body first, target Maturity second, Handoff third, assignee removal fourth, Status `Available` fifth, then complete readback. Reassert Status even when it already reads `Available`. The closeout names the verified level and what refinement remains.

</refine_before_handoff>

<post_handoff_or_close>

For each held Change, after `<release_work_branch>` has left the work committed, pushed, and the worktree stepped off the branch:

**Applied.** When the changeset has integrated into the authoritative branch, the Assertions and evidence governing the Change's Nodes are satisfied, and the Output is delivered, target Status `Applied`, comment `Application complete: changeset integrated, evidence satisfied, and Output delivered.`, and close reason `completed`. A merged pull request alone is not Applied.

**Refined.** When this conversation created every known successor and complete readback shows each successor carrying `## Refined from` with this Change's URL, target Status `Refined`, comment `Refinement complete: all known successors exist.`, and close reason `completed`.

**Abandoned.** Only on the operator's explicit direction, target Status `Abandoned`, comment `Abandoned: <the operator's stated reason>`, and close reason `not planned`.

When one terminal condition holds, execute this sequence and record each successful write:

1. Re-read the issue and its single project item and verify the terminal precondition above from current authoritative state.
2. Post the exact authorized terminal comment with `gh issue comment <N> --repo <store> --body-file -`.
3. Remove the current assignee with `gh issue edit <N> --repo <store> --remove-assignee @me`.
4. Write the target terminal Status with `gh project item-edit`.
5. Close the issue with `gh issue close <N> --repo <store> --reason 'completed'` for Applied or Refined, or `gh issue close <N> --repo <store> --reason 'not planned'` for Abandoned.
6. Re-read the issue and single project item. Terminal closure completes only when Product equals the overlay Product, Maturity equals the intended current level, Status equals the target terminal Status, the assignee list is empty, issue state is `CLOSED`, `stateReason` is `COMPLETED` for Applied or Refined and `NOT_PLANNED` for Abandoned, and the newest terminal comment is the exact comment just posted.

Each step is subject to the transition failure boundary above. A failure leaves the completed prefix visible, performs no later mutation, and reports the complete observed partial state. A terminal Change receives no `Handoff:` release comment and is never written back to `Available`.

**Otherwise release.** Post the continuation below as one comment with `gh issue comment <N> --repo <store> --body-file -`, the body on stdin per the rule above, then remove the assignee:

```markdown
Handoff:

- Branch or PR: <pushed work branch, or the PR URL, or `none`>
- Completed Activities: <checked items, by their text>
- Next Activity: <the first unchecked Activity, or `refinement: <Maturity> → <next level>` below Executable>
- Blockers: <blocking Change URLs still active per `gh api repos/<store>/issues/<N>/dependencies/blocked_by`, or `none` — a mirror of the dependency graph, never its source>
- Hazards: <what the next holder cannot derive quickly: an unsealed run, a held checkout, a flaky check — each with the read-only command that re-confirms it>
```

Optional context lines after the five: the current session id and the assigned worktree root. Nothing else — no insight, status, or restated plan; those live in the body. Then remove the assignee with `gh issue edit <N> --repo <store> --remove-assignee @me`, and write Status `Available` with `gh project item-edit`. Re-read the single project item and issue. Release completes only when Product equals the overlay Product, Maturity equals the intended current level, Status is `Available`, the assignee list is empty, and the newest Handoff is the exact comment just posted. A failure stops at its observed partial state under the transition failure boundary above.

The store-write inspection at the top of this workflow applies to the Handoff comment as to every other write.

</post_handoff_or_close>

<closeout_rows>

In `<confirm>`, the session-mechanics rows become Change rows: each Change URL with its verified terminal Status and close reason, or verified Status `Available`, Maturity, and released work branch. Legacy archived session ids keep their existing rows.

</closeout_rows>

</process>

<success_criteria>

- Every `gh issue create`, `gh issue edit --body-file`, and `gh issue comment` this workflow performs is inspected for secret values and credential payloads before it lands, and a hit writes nothing.
- After the closure, every held Change is either closed with Product and Maturity verified, its intended terminal Status, matching close reason, empty assignee list, and exact authorized terminal comment, or open with Product and Maturity verified, Status `Available`, an empty assignee list, and the exact new `Handoff:` as its newest Handoff; no Change stays Claimed by a conversation that has ended.
- A Handoff carries the five continuation lines and nothing that belongs in the body; refinement edits landed in the body before the Handoff was posted.
- Every terminal condition is executed through the authorized comment, assignee removal, terminal Status write, issue close, and complete readback sequence; a failed prefix stops before later mutation.
- Every failed transition stops before later mutation and reports the ordered successful writes, failed operation, and complete observed state.
- No session file is written when `spx/local/coordination.md` exists; new continuation without a Change becomes one Proposed, Available Change carrying its received input.

</success_criteria>
