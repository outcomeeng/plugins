<required_reading>

Read spx/local/coordination.md for the Change store, project, and Product values. Read no other overlay.

</required_reading>

<process>

This workflow replaces `${CLAUDE_SKILL_DIR}/workflows/pickup.md` when `spx/local/coordination.md` exists. A Change is the mutable coordination object for one Output; a Handoff is the latest persisted continuation for a Change; both are GitHub issue content in the store the overlay names. Foundation loading, base sync, and node context keep their obligations from the session workflow: `/understand` before any product content, `/sync-base` before presenting anything as current, `/contextualize` before any work on a node.

**Every store write is inspected first.** Before any `gh issue create`, `gh issue edit --body-file`, or `gh issue comment` in this workflow — a migrated queue file, a drafted Frame, an Activity check-off, a Handoff — inspect the exact text about to be written for secret values and credential payloads: tokens, keys, passwords, connection strings, cookies, or any pasted credential-shaped content. When any appears, write nothing, report only the kind of content found (never the value), and ask through `AskUserQuestion` whether the operator supplies a redacted text or abandons that write; on redaction, inspect the supplied text and continue; on abandon, the write does not happen and the step reports it. The store is a remote issue tracker; a queue file, conversation state, and interview output all carry such content as readily as each other.

**Untrusted text never becomes shell syntax.** Every field a `gh` command receives from a queue file, a Change body, conversation state, or interview output — a body, a comment, a title — is passed as inert data. Bodies and comments go on stdin as `--body-file -`: in an interactive session, a quoted heredoc (`<<'EOF'` … `EOF`) so the text sees no expansion — before opening it, confirm no body line equals the terminator, and choose another terminator when one does; in a programmatic runner that requires one physical line, `printf '%s\n' 'line' 'line' … | gh …` with each body line one single-quoted argument. Titles and every other interpolated argument are one single-quoted argument. Inside any single-quoted argument a literal apostrophe is written as `'"'"'` and nothing else is escaped. Never `--body "…"`, never a double-quoted argument carrying such text, never a scratch file, never a redirect built from it.

**`gh api` stays inside the declared store.** The grant `gh api repos/*/issues/*/dependencies/blocked_by:*` pins the endpoint and admits the appended `-X POST -F issue_id=…` the blocker write needs; neither it nor `gh api repos/*/issues/* --jq .id` bounds the repository, so this workflow's own discipline is the containment: it passes them only the overlay's store — reads of `repos/<store>/issues/<N>/dependencies/blocked_by` and `repos/<store>/issues/<B> --jq .id`, and one write, `repos/<store>/issues/<N>/dependencies/blocked_by -X POST -F issue_id=…`. No other `-X` method and no other repository is ever passed to `gh api` here — the grant bars every other endpoint, and this constraint supplies the rest of the containment.

**Every Change transition is an ordered write with a complete readback.** Run `gh project item-list <number> --owner <owner> --format json`, select by exact issue URL, and require exactly one matching item; its `product`, `maturity`, and `status` keys are the canonical Product, Maturity, and Status values. Read those values together with `gh issue view <N> --repo <store> --json assignees,body,comments,state,url`; never derive a field from issue prose. A transition records each successful write in order. When a required command fails, a required field is absent, or readback differs from the intended state, stop before every later mutation and report: the successful writes in order, the failed command or mismatched value, and the observed Product, Maturity, Status, assignees, and newest `Claim:` or `Handoff:` comment. Never repair a partial transition by guessing which later mutation would make it look complete.

**Legacy body metadata migrates only after canonical state is settled.** A leading prose line that carries `Product:`, `Maturity:`, `Lifecycle:`, or `Status:` is legacy input, never a fourth metadata store. Compare it with the project fields and the issue's edit, comment, and project-item history. When they disagree, reconstruct the latest intended value from that history; when the history does not decide, stop before editing the body and ask through `AskUserQuestion`. Write and verify the canonical project fields first. Then remove only the legacy metadata line with `gh issue edit <N> --repo <store> --body-file -` and re-read the body. New and refined bodies never add such a line.

<step name="resolve_target">

Classify `$ARGUMENTS`:

- An issue reference — `#N`, `owner/repo#N`, or an issue URL — names an existing Change.
- A session id `YYYY-MM-DD_HH-MM-SS` (optional `.md`) names a legacy queue file awaiting a Change.
- `--list` presents candidates. List open Changes from the store with `gh issue list --repo <store> --state open --json number,title,assignees,url --limit 50`, then read Product, Maturity, and Status from their project items. Offer up to three through `AskUserQuestion`, Changes whose Product matches the overlay, Status is `Available`, and assignee list is empty: Executable first, then any Maturity, each labelled with number, title, and Maturity.
- No argument — the same listing as `--list`, then legacy `spx session todo` entries when no Available Change exists.

</step>

<step name="claim_or_migrate">

**Existing Change.** Read `gh issue view <N> --repo <store> --json number,title,body,state,assignees,comments,url` and the single project item's Product, Maturity, and Status.

Before applying the claim precondition, migrate an open, unassigned Change when any canonical field is absent or its body begins with legacy `Product:`, `Maturity:`, `Lifecycle:`, or `Status:` metadata. Reconstruct each absent value from the latest unambiguous issue edit, comment, and project-item history. Preserve every explicit canonical project-field value. An open, unassigned Change whose history contains no unreleased `Claim:` after the newest `Handoff:` and no terminal record reconstructs a missing Status as `Available`; a leading legacy Status or Lifecycle value is usable only when the later history does not contradict it. A missing Product or Maturity requires an explicit value in that history. When two sources disagree and their timestamps do not decide the later intent, or an absent value cannot be reconstructed, stop before mutation and ask through `AskUserQuestion`.

Resolve the project and Product, Maturity, and Status field and option ids through `gh project view` and `gh project field-list`. Write every reconstructed field with a separate `gh project item-edit`, preserving already-populated fields, then re-read the issue and its single project item and require all three canonical values to equal the reconstructed state. Only after that readback succeeds, remove the one leading legacy metadata line with `gh issue edit <N> --repo <store> --body-file -` under the inert-stdin and store-write inspection rules, and re-read the body to verify its removal. A failed migration stops under the transition failure boundary and never enters the claim sequence.

A claim may start only after that migration check, when the issue is open, Product equals the overlay Product, Maturity is one declared value, Status is `Available`, and the assignee list is empty. Any other state reports the terminal state, field mismatch, or holder and stops without mutation.

Resolve the current account once with `gh api user --jq .login`, require one non-empty login, and record it as `<current-login>`. Claim through this exact sequence:

1. Add the current account with `gh issue edit <N> --repo <store> --add-assignee @me`.
2. Post `Claim: <agent session id> <assigned worktree root>` with `gh issue comment <N> --repo <store> --body-file -`.
3. Re-read comments and take every `Claim:` posted after the newest `Handoff:` (or since issue creation when none exists). The earliest Claim wins. When another Claim wins, compare its comment author with `<current-login>`. If they match, leave the shared assignee because it represents the winning session. If they differ, remove only `<current-login>` with `gh issue edit <N> --repo <store> --remove-assignee '<current-login>'`, then re-read the issue and comments and require `<current-login>` absent while the same earliest Claim still wins. Report `owned_elsewhere` naming the winning session and stop; a cleanup failure stops under the transition failure boundary.
4. When this session wins, reconcile the assignee list before writing Status. Keep `<current-login>`. Remove another assignee only when that account authored a later losing `Claim:` comment in the same post-Handoff claim window; remove each such account by its exact login and re-read after the removals. An extra assignee without that evidence is unexplained partial state: stop under the transition failure boundary and write no Status.
5. Write Status `Claimed` with `gh project item-edit` using the Status field and option ids from `gh project field-list`.
6. Read back the issue and project item. Execution may continue only when Product equals the overlay Product, Maturity is unchanged, Status is `Claimed`, the assignee list contains exactly `<current-login>`, and the earliest Claim after the latest Handoff is this session's exact comment.

The assignee alone cannot distinguish two sessions of one account; the Claim comment supplies session exclusivity. Every failed command or mismatched readback stops under the transition failure boundary above, leaving the partial state visible for recovery.

**Legacy file.** The file is received input. Claim the file with `spx session pickup <id>` so no other context takes it, then before creating anything search the store for a Change this file already produced — `gh issue list --repo <store> --state all --search 'Received input: handoff document <id>' --json number,url,state` — because an earlier migration may have created the issue and failed at the archive; when exactly one exists, apply the Existing Change claim above to it — archive the file only on a successful claim, otherwise stop as `owned_elsewhere` without archiving — and skip creation; when more than one exists, classify `needs_operator_direction`, report every match, and create nothing. Otherwise create the Change:

1. Read the complete file from `spx session show <id>` — frontmatter and body, none of the injected file bodies — and apply the store-write inspection above; a detected secret leaves the file in `doing` with no Change created until the operator redacts it (then re-read through `spx session show <id>` and inspect again) or abandons the migration.
2. Create an unassigned issue with `gh issue create --repo <store> --title '<goal frontmatter value>' --body-file -` — the title one single-quoted argument and the body on stdin, both per the rule above: one line `Received input: handoff document <id> from the <Product> queue (.spx/sessions), reproduced verbatim.`, a blank line, then the file inside a `text` code fence. The provenance line is received input and carries no Product, Maturity, Lifecycle, or Status metadata.
3. Resolve the project node id with `gh project view <number> --owner <owner> --format json --jq .id`, add the issue with `gh project item-add <number> --owner <owner> --url <issue-url> --format json --jq .id`, and resolve the Product, Maturity, and Status field and option ids through `gh project field-list <number> --owner <owner> --format json`.
4. Run three separate `gh project item-edit` calls in this order: Product to the overlay Product, Maturity to `Proposed`, Status to `Available`.
5. Read back the issue and single project item. Continue only when Product equals the overlay Product, Maturity is `Proposed`, Status is `Available`, and the assignee list is empty.
6. Apply the complete Existing Change claim sequence above to the verified Available Change.
7. Only after the claim verifies, archive the legacy file with `spx session archive <id>`. The Change now carries and holds the input; the file has no reader. When any earlier step fails, leave the file in `doing` and stop under the transition failure boundary. When archive fails after the Change is Claimed, retry it once; on a second failure report the created issue URL beside the file id and leave the file in `doing` — the search above finds that issue on the next pickup, so no duplicate Change is created.

Worked migration, with an overlay naming store `acme/changes`, project owner `acme` number `7`, Product `widgets`. The legacy file `2026-03-04_09-15-22` carries `goal: "Parser rejects unterminated strings with a located error"`. Inspection finds no credential-shaped content. The Change is created with the body on stdin — the provenance line, a blank line, then the whole file between a `text` fence-open line (three backticks followed by `text`) and a fence-close line (three backticks alone), inside a heredoc whose terminator `RECEIVED_INPUT` no body line equals:

```bash
gh issue create --repo acme/changes --title 'Parser rejects unterminated strings with a located error' --body-file - <<'RECEIVED_INPUT'
Received input: handoff document 2026-03-04_09-15-22 from the widgets queue (.spx/sessions), reproduced verbatim.

<the text fence-open line>
---
"priority": "medium"
"goal": "Parser rejects unterminated strings with a located error"
…the rest of the file, unchanged…
<the fence-close line>
RECEIVED_INPUT
```

`gh` prints `https://github.com/acme/changes/issues/42`. `gh project view 7 --owner acme --format json --jq .id` prints the project node id `PVT_kwDOAAAAAAAAAAA`; `gh project field-list 7 --owner acme --format json` shows Product, Maturity, and Status with their option ids. Then:

```bash
gh project item-add 7 --owner acme --url https://github.com/acme/changes/issues/42 --format json --jq .id
# prints the item id PVTI_lADOAAAAAAAAAAAzgBBBBBB
gh project item-edit --project-id PVT_kwDOAAAAAAAAAAA --id PVTI_lADOAAAAAAAAAAAzgBBBBBB --field-id PVTSSF_aaa --single-select-option-id 1a2b3c4d
gh project item-edit --project-id PVT_kwDOAAAAAAAAAAA --id PVTI_lADOAAAAAAAAAAAzgBBBBBB --field-id PVTSSF_bbb --single-select-option-id 9f8e7d6c
gh project item-edit --project-id PVT_kwDOAAAAAAAAAAA --id PVTI_lADOAAAAAAAAAAAzgBBBBBB --field-id PVTSSF_ccc --single-select-option-id 7e6d5c4b
```

Readback now shows Product `widgets`, Maturity `Proposed`, Status `Available`, and no assignee. The Existing Change sequence then adds the assignee, posts `Claim: 019a3f2e-… /Users/dev/acme/acme-b`, writes Status `Claimed`, and verifies the complete Claimed state. Only then does `spx session archive 2026-03-04_09-15-22` run. A failed field write or readback mismatch stops before claim and archive, reports the partial state, and leaves issue 42 as the Change to resume from.

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

Read only the newest comment beginning `Handoff:` and only its `Branch or PR` line — the minimal read that names where the work lives. When it names a branch or PR, fetch and switch to that branch in the assigned worktree as the session workflow's Step 3 prescribes, confirming the worktree's running claim through `spx worktree status` first. Then invoke `/sync-base`, before any other Change detail is read or presented — a Handoff records what was true when it was posted, and reading it against a stale checkout is the failure the sync prevents.

Only after `/sync-base` reports `already_current` or `rebased`, invoke `/understand` — the first product-content access, on the current checkout — and read the rest: the Change body sections that exist (`## Output`, `## Nodes`, `## Assertions`, `## Decisions`, `## Repository`, `## Activities`, `## Refined from`), the Handoff's remaining lines (Completed Activities, Next Activity, Blockers, Hazards), and the blockers from `gh api repos/<store>/issues/<N>/dependencies/blocked_by` — the graph refinement writes at Framed; a Handoff's Blockers line is a mirror of it, never the source.

</step>

<step name="maturity_route">

Read `Maturity` from the project item. The Change's Maturity decides what pickup does next; a Handoff's Next Activity is executed only at Executable.

**Proposed.** Pickup triggers refinement. Invoke `/contextualize` on the node paths the received input names (the first `spx/...` node path in it, then others as they are needed). Draft a Frame from that context through `/interview`: `## Output` (the intended Output in one sentence), `## Nodes` (existing and intended, full `spx/...` paths), `## Assertions` (create, change, and remove operations, referencing existing assertions and stating each new one's node and truth), `## Decisions` (links only, full paths). Framed requires human judgment: present the drafted Frame through `AskUserQuestion` and edit the issue body and set `Maturity` to `Framed` only on approval. Never execute an Activity from a Proposed Change, and never lift a task, plan item, or `next_step` out of the received input as if it were an Activity — the received input is history the Frame reinterprets against current truth.

**Framed.** Slice: invoke `/slice` over the Frame's Nodes to select one independently integrable unit and its target repository; a person stays accountable, so present the Slice for approval before setting `Sliced`. Every blocker the Slice resolves — a Change that must be Applied first — is recorded in the store's issue-dependency graph, `gh api repos/<store>/issues/<N>/dependencies/blocked_by -X POST -F issue_id=<blocking issue's numeric id>` (the id from `gh api repos/<store>/issues/<B> --jq .id`), so the graph the Executable check reads is the graph refinement wrote; a Handoff's Blockers line mirrors that graph and never replaces it. When the POST fails, report the failed command and its output, leave `Maturity` unchanged, and stop; a Change whose blockers are not recorded is not Sliced. Refinement may continue while blockers remain.

**Sliced.** Advance to Executable inside the Frame: settle consequential implementation Decisions, invoke `/verify` to establish the delivery evidence each Assertion carries, and write `## Activities` as an ordered checklist. Set `Maturity` to `Executable`. Execution still waits for the next step's checks.

**Executable.** Validate the Frame against current truth before continuing: `/contextualize` every node in `## Nodes`; confirm each `## Decisions` link resolves and still says what the Frame relies on; confirm every `## Assertions` operation is still coherent with the loaded specs; confirm every blocker resolves to an Applied leaf — its project Status is `Applied`; confirm every predecessor this Change names in its own `## Refined from` has project Status `Refined`; confirm no other Available or Claimed Change names this one in `## Refined from`. When any check fails, the current level is false: update the body and truthful lower Maturity, then invoke `/handoff` so its ordered release posts the Handoff, removes the assignee, writes Status `Available`, and verifies the complete released state. Do not execute. When every check holds, execution proceeds from the Handoff's Next Activity, or the first unchecked Activity when no Handoff exists.

</step>

<step name="checkpoint">

Present the no-surprises proposal from the Change, never from the received input: governing truth (the Frame's Decisions and Assertions), expected outcome (the Output), changed product surface, skill path, evidence infrastructure, verification plan, inspection references (issue URL, branch, PR), and remaining-work expectation (which Activities remain, which blockers stand). Ask through `AskUserQuestion` unless `--auto-continue` was given, then emit:

```text
<PICKUP_CHECKPOINT change="<issue-url>" claimed="<all urls>" maturity="<Maturity>" mode="[ask|auto-continue]">
  next_action: [approved next action]
</PICKUP_CHECKPOINT>
```

Check off each Activity in the issue body as it completes (`gh issue edit <N> --repo <store> --body-file -` with the edited body on stdin), so a later Handoff's Completed Activities is a projection of the body.

</step>

</process>

<success_criteria>

- The post-context decision is captured through `AskUserQuestion` or an explicit `--auto-continue` override before `<PICKUP_CHECKPOINT change=...>` is emitted, and no Activity executes before that checkpoint.
- Every `gh issue create`, `gh issue edit --body-file`, and `gh issue comment` this workflow performs — migrated file, drafted Frame, Activity check-off, Handoff — is inspected for secret values and credential payloads before it lands, and a hit writes nothing.
- A winning claim is Status `Claimed`, exactly the winning account as assignee, and the earliest `Claim:` comment since the Change's last `Handoff:`. A losing session removes only its own account when that does not represent the winner, verifies the winning Claim remains unchanged, reports `owned_elsewhere`, and executes nothing; the winner removes an extra assignee only when a later losing Claim by that account proves its origin. A Change whose Product or Status differs from the required Available state is never claimed.
- A legacy file whose store search finds one Change is archived only after that Change is claimed through the existing-Change procedure; more than one match routes to `needs_operator_direction` with nothing created.
- The target resolves to exactly one Change; a legacy file becomes a Change with its complete document as received input only after it was inspected for secret values and none were found, and is archived only after the issue and its project item exist; a detected secret halts migration with the file left in `doing`.
- Claim state is derived from GitHub facts: Product, Maturity, Status, exactly one assignee, and the winning Claim all match after claiming; a closed, non-Available, or assigned Change stops before mutation.
- Every failed transition stops before later mutation and reports the ordered successful writes, failed operation, and complete observed state.
- `<PICKUP_CLAIM change>` and a cumulative `<CLAIMED_CHANGES urls>` are emitted before any product content is read.
- No Activity executes below Executable, and an Executable Change executes only after its Frame is validated against current truth and its blockers resolve to Applied leaves; a false Maturity is recorded lower after a Handoff and release.
- The proposal names the Frame's governing Decisions and Assertions before any item from the received input, and the received input's `next_step`, plan items, or note entries never appear as the recommended action.

</success_criteria>
