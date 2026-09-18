<scope>

This reference operationalizes the Lifecycle and Handoff rules of the Change chapter `change-record.md` names, for the store `spx/local/coordination.md` declares; it replaces nothing in the chapter. Lifecycle records who holds a Change or how it ended and moves independently of Maturity.

</scope>

<lifecycle_rules>

<rule id="store-binding">

Read `spx/local/coordination.md` for the Change store (`owner/repo`), the project owner and number, and the Product value. Read no other overlay for the store; a transition that moves the checkout reads `spx/local/merging.md` for the safety checks the repository declares around a detach. Every store command names only that store; a `gh` grant admits any repository the account reaches, so this discipline is the containment. An absent overlay is a blocked operation naming the missing file; no Lifecycle transition runs without a declared store.

</rule>

<rule id="canonical-state">

Product, Maturity, and Status (the store's projection of Lifecycle) are canonical project fields; the issue body carries the record; comments carry Claim, Handoff, and terminal records; the assignee list represents the holder. Read state with `gh project item-list <number> --owner <owner> --format json`, select the item whose `content.url` equals the issue URL exactly, and require exactly one match; its `product`, `maturity`, and `status` keys are the canonical values. Read the issue with `gh issue view <N> --repo <store> --json number,title,state,stateReason,assignees,comments,url`. Never derive a field from issue prose. Resolve the project node id with `gh project view <number> --owner <owner> --format json --jq .id` and the field and option ids with `gh project field-list <number> --owner <owner> --format json`; hardcode none of them.

</rule>

<rule id="ordered-write">

A transition records each successful write in its declared order. When a required command fails, a required field is absent, or a readback differs from the intended state, stop before every later mutation and report: the successful writes in order, the failed command or mismatched value, and the observed Product, Maturity, Status, assignees, issue state and reason, and newest `Claim:`, `Handoff:`, or terminal comment. Never repair a partial transition by guessing which later mutation would make it look complete.

</rule>

<rule id="complete-readback">

A transition completes only after re-reading the issue and its single project item and finding every value equal to the intended state: Product equals the overlay Product, Maturity is unchanged, Status equals the target value, the assignee list equals the intended holder set, and the newest `Claim:`, `Handoff:`, or terminal comment is the exact comment the transition posted. Report the readback values verbatim.

</rule>

<rule id="write-inspection">

Before any `gh issue comment` or `gh issue edit --body-file` write, inspect the exact text about to be written for secret values and credential payloads: tokens, keys, passwords, connection strings, cookies, or any pasted credential-shaped content. When any appears, write nothing, report only the kind of content found, never the value, and ask through the structured-question tool whether the operator supplies a redacted text or abandons the write; on redaction, inspect the supplied text and continue; on abandon, the write does not happen and the result says so.

</rule>

<rule id="inert-stdin">

Every field a `gh` command receives from a Change body, conversation state, or interview output is passed as inert data. Comments and bodies go on stdin as `--body-file -`: in an interactive session, a quoted heredoc (`<<'EOF'` … `EOF`) so the text sees no expansion — confirm no body line equals the terminator, and choose another terminator when one does; in a programmatic runner that requires one physical line, `printf '%s\n' 'line' 'line' … | gh …` with each line one single-quoted argument. Every other interpolated argument is one single-quoted argument; inside it a literal apostrophe is written as `'"'"'` and nothing else is escaped. Never `--body "…"`, never a double-quoted argument carrying such text, never a scratch file, never a redirect built from it.

</rule>

<rule id="claim-record">

A Claim is one comment, `Claim: <agent session id> <assigned worktree root>`, posted after the assignee is added. Session exclusivity comes from the Claim, never from the assignee alone, because one account may run several sessions: the earliest `Claim:` posted after the newest `Handoff:` — or since issue creation when none exists — wins.

</rule>

<rule id="handoff-record">

A Handoff is one comment carrying exactly these lines and nothing that belongs in the body:

```markdown
Handoff:

- Branch or PR: <pushed work branch, or the PR URL, or `none`>
- Completed Activities: <checked items, by their text>
- Next Activity: <the first unchecked Activity, or `refinement: <Maturity> → <next level>` below Executable>
- Blockers: <blocking Change URLs still active, or `none`>
- Hazards: <what the next holder cannot derive quickly — an unsealed run, a held checkout, a flaky check — each with the read-only command that re-confirms it>
```

Optional context lines after the five: the current agent session id and the assigned worktree root. The Handoff records what was true when it was posted; refinement of the Output belongs in the body, before the release.

</rule>

<rule id="terminal-record">

A terminal record is one comment whose text the terminal value fixes: `Application complete: changeset integrated, evidence satisfied, and Output delivered.` for `Applied`; `Refinement complete: all known successors exist.` for `Refined`, which requires at least one successor; `Abandoned: <the operator's stated reason>` for `Abandoned`. The close reason is `completed` for `Applied` and `Refined` and `not planned` for `Abandoned`. A terminal Change receives no Handoff and never returns to `Available`.

</rule>

</lifecycle_rules>
