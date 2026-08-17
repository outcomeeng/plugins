<required_reading>

Read `spx/local/coordination.md` for the Change store, project, and Product values. Read no other overlay.

</required_reading>

<process>

This workflow replaces `${SKILL_DIR}/workflows/pickup.md` when `spx/local/coordination.md` exists. A Change is the mutable coordination object for one Output; a Handoff is the latest persisted continuation for a Change; both are GitHub issue content in the store the overlay names. Foundation loading, base sync, and node context keep their obligations from the session workflow: `/understand` before any product content, `/sync-base` before presenting anything as current, `/contextualize` before any work on a node.

<step name="resolve_target">

Classify `$ARGUMENTS`:

- An issue reference — `#N`, `owner/repo#N`, or an issue URL — names an existing Change.
- A session id `YYYY-MM-DD_HH-MM-SS` (optional `.md`) names a legacy queue file awaiting a Change.
- `--list` presents candidates. List open Changes of this Product from the store: `gh issue list --repo <store> --state open --json number,title,assignees,url --limit 50`, then read `Maturity` and `Product` from `gh project item-list <number> --owner <owner> --format json`. Offer up to three through `request_user_input`, Available (no assignee) Executable Changes first, then Available Changes at any Maturity, each labelled with number, title, and Maturity.
- No argument — the same listing as `--list`, then legacy `spx session todo` entries when no Available Change exists.

</step>

<step name="claim_or_migrate">

**Existing Change.** Read `gh issue view <N> --repo <store> --json number,title,body,state,assignees,comments,url`. When it is closed, or open with an assignee that is not the current account, classify `owned_elsewhere`, report the holder or the terminal state, and stop without mutating anything. Otherwise claim it: `gh issue edit <N> --repo <store> --add-assignee @me`. Re-read assignees; more than one assignee is a failed claim — remove the current account and report.

**Legacy file.** The file is received input; the Change does not exist yet. Claim the file with `spx session pickup <id>` so no other context takes it, then create the Change:

1. Read the complete file from `spx session show <id>` — frontmatter and body, none of the injected file bodies — and inspect it for secret values and credential payloads: tokens, keys, passwords, connection strings, cookies, or any pasted credential-shaped content. The store is a remote issue tracker; a queue file is local and gitignored and may carry such content. When any appears, do not migrate: leave the file in `doing`, report the file and the kind of content found (never the value), and ask through `request_user_input` whether the operator redacts the file or abandons the migration. Otherwise write the body to a scratch file from `mktemp`: one line `Received input: handoff document <id> from the <Product> queue (.spx/sessions), reproduced verbatim.`, a blank line, then the file inside a `text` code fence.
2. `gh issue create --repo <store> --title "<goal frontmatter value>" --body-file <scratch> --assignee @me`.
3. `gh project item-add <number> --owner <owner> --url <issue-url>`, then `gh project item-edit` setting `Product` to the overlay's Product and `Maturity` to `Proposed`, using the field and option ids from `gh project field-list <number> --owner <owner> --format json`.
4. Only after steps 2 and 3 have each returned success — the issue URL exists and `gh project item-list` shows the item with `Product` and `Maturity` set — archive the legacy file: `spx session archive <id>`. The Change now carries the input; the file has no reader. When any of steps 1–3 fails, report the failed command and its output, leave the file in `doing`, and stop; the archive never runs on a partial migration.

Delete the scratch file on every exit path.

Emit the claim markers, using the issue URL as the identity:

```text
<PICKUP_CLAIM change="<issue-url>">
claimed
</PICKUP_CLAIM>

<CLAIMED_CHANGES urls="<earlier-urls>,<issue-url>">
the Changes this conversation must release or close through /handoff
</CLAIMED_CHANGES>
```

Extend `<CLAIMED_CHANGES>` on every claim in the conversation, never replace it. A legacy `<CLAIMED_SESSIONS>` marker from an earlier turn stays valid for `/handoff`'s archive accounting.

</step>

<step name="foundation_and_currency">

Invoke `/understand`. Read the Change body sections that exist (`## Output`, `## Nodes`, `## Assertions`, `## Decisions`, `## Repository`, `## Activities`, `## Refined from`) and the newest comment beginning `Handoff:` (Branch or PR, Completed Activities, Next Activity, Blockers, Hazards). Read blockers from `gh api repos/<store>/issues/<N>/dependencies/blocked_by`.

When the Handoff names a branch or PR, fetch and switch to that branch in the assigned worktree as the session workflow's Step 3 prescribes, confirming the worktree's running claim through `spx worktree status` first. Then invoke `/sync-base`.

</step>

<step name="maturity_route">

Read `Maturity` from the project item. The Change's Maturity decides what pickup does next; a Handoff's Next Activity is executed only at Executable.

**Proposed.** Pickup triggers refinement. Invoke `/contextualize` on the node paths the received input names (the first `spx/...` node path in it, then others as they are needed). Draft a Frame from that context through `/interview`: `## Output` (the intended Output in one sentence), `## Nodes` (existing and intended, full `spx/...` paths), `## Assertions` (create, change, and remove operations, referencing existing assertions and stating each new one's node and truth), `## Decisions` (links only, full paths). Framed requires human judgment: present the drafted Frame through `request_user_input` and edit the issue body and set `Maturity` to `Framed` only on approval. Never execute an Activity from a Proposed Change, and never lift a task, plan item, or `next_step` out of the received input as if it were an Activity — the received input is history the Frame reinterprets against current truth.

**Framed.** Slice: invoke `/slice` over the Frame's Nodes to select one independently integrable unit and its target repository; a person stays accountable, so present the Slice for approval before setting `Sliced`. Refinement may continue while blockers remain.

**Sliced.** Advance to Executable inside the Frame: settle consequential implementation Decisions, invoke `/verify` to establish the delivery evidence each Assertion carries, and write `## Activities` as an ordered checklist. Set `Maturity` to `Executable`. Execution still waits for the next step's checks.

**Executable.** Validate the Frame against current truth before continuing: `/contextualize` every node in `## Nodes`; confirm each `## Decisions` link resolves and still says what the Frame relies on; confirm every `## Assertions` operation is still coherent with the loaded specs; confirm every blocker resolves to an Applied leaf; confirm no other open Change names this one in `## Refined from`. When any check fails, the current level is false: post a `Handoff:` comment, remove the assignee, set `Maturity` to the truthful lower level, and report — do not execute. When every check holds, execution proceeds from the Handoff's Next Activity, or the first unchecked Activity when no Handoff exists.

</step>

<step name="checkpoint">

Present the no-surprises proposal from the Change, never from the received input: governing truth (the Frame's Decisions and Assertions), expected outcome (the Output), changed product surface, skill path, evidence infrastructure, verification plan, inspection references (issue URL, branch, PR), and remaining-work expectation (which Activities remain, which blockers stand). Ask through `request_user_input` unless `--auto-continue` was given, then emit:

```text
<PICKUP_CHECKPOINT change="<issue-url>" claimed="<all urls>" maturity="<Maturity>" mode="[ask|auto-continue]">
  next_action: [approved next action]
</PICKUP_CHECKPOINT>
```

Check off each Activity in the issue body as it completes (`gh issue edit --body-file` after editing the checklist), so a later Handoff's Completed Activities is a projection of the body.

</step>

</process>

<success_criteria>

- The target resolves to exactly one Change; a legacy file becomes a Change with its complete document as received input and is archived only after the issue exists.
- Claim state is derived from GitHub facts: exactly one assignee after claiming; a closed or otherwise-assigned Change stops the workflow as `owned_elsewhere`.
- `<PICKUP_CLAIM change>` and a cumulative `<CLAIMED_CHANGES urls>` are emitted before any product content is read.
- No Activity executes below Executable, and an Executable Change executes only after its Frame is validated against current truth and its blockers resolve to Applied leaves; a false Maturity is recorded lower after a Handoff and release.
- The proposal names the Frame's governing Decisions and Assertions before any item from the received input, and the received input's `next_step`, plan items, or note entries never appear as the recommended action.

</success_criteria>
