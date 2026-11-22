---
id: 01a1be73-4a1c-73a4-bda9-4b1aee86c53b
malleability: spec
---

# Changes

PROVIDES the Change record and the skills that state it, record it, and audit it
SO THAT product engineers and the agents that refine and apply Changes
CAN write, check, and audit every Change record in one form

## Assertions

### Test.Compliance: form check tree

- [form-check-tree](tests/test_form_check_tree.compliance.l2.py): ALWAYS: the form check treats a repository as having a Product Tree exactly when the tree of the record's Base holds, directly under `spx/`, a root Product spec, which is a `{slug}.spec.md` whose front matter holds `kind: product` or a `{slug}.product.md` of the 3.x grammar, or an indexed Node directory, which is an index, a hyphen, a slug and a Node kind suffix, `.enabler` or `.outcome` of the 3.x grammar or `.product`, `.substrate`, `.capability`, `.domain`, `.interface`, `.surface` or `.variant` of the 4.0 grammar; it judges every Declarations heading as a path from the repository root when the Base holds neither, and reads no directory of the checkout for this.
- [form-check-overlay-headings](tests/test_form_check_overlay_headings.compliance.l2.py): ALWAYS: when the Base's `spx/local/changes.md` holds the line `- Repository-root headings: admitted`, the form check judges a Declarations heading outside `spx/` as a path from the repository root and accepts the labelled diff lines and the `new file`, `deleted file`, move, and replacement operations the no-tree rows admit for that file; without the line, it fails that heading with `subsection-headings`.

### Test.Compliance: form check rows

- [form-check-merged-base](tests/test_form_check_rows.compliance.l2.py): ALWAYS: for a Leaf whose Changeset has merged into the default branch, the form check reads each deletion, move or replacement at the Base the latest advance to Sliced recorded, and refuses no publish on a new base.
- [form-check-linked-heading](tests/test_form_check_rows.compliance.l2.py): ALWAYS: the form check takes the slug of a Mapping or Evaluate subsection whose heading carries a slug link as that link's text, and accepts the infrastructure line keyed by that slug.
- [form-check-scenario-steps](tests/test_form_check_rows.compliance.l2.py): ALWAYS: the form check reads every indented line opening with Given, When, Then or And that follows a `+` Scenario row as part of that row, and requires no slug of it.
- [form-check-stored-body](tests/test_form_check_rows.compliance.l2.py): ALWAYS: the form check fails a stored record whose body is a link alone or lacks the Output, the Why or the Verification of its Statement of Intent, and passes one that holds all three.
- [form-check-foreign-proposed](tests/test_form_check_rows.compliance.l2.py): ALWAYS: the form check passes a Proposed Draft of another Product that holds only its Statement of Intent, run against a checkout of a different repository.

### Audit: change-standards

- standards-keys: change-standards states the twelve metadata keys of a record, the value of each key, and the operations that change it, as record-keys of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-draft: change-standards states that a Change Draft holds every key of its record except holder, and states the Lifecycle and the base a Draft holds, as draft-lifecycle and draft-base of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) state them.
- standards-body: change-standards states the sections of the body of a Leaf and of a Parent, as record-body of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-intent: change-standards states the three parts of the Statement of Intent and its limit of 120 words, and the limit of 15 words for the title, as statement-of-intent and record-keys of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) state them.
- standards-declarations: change-standards states the heading of each kind of Declarations subsection, the payloads, the git headers, the form of each diff line, and the infrastructure lines, as [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-maturity: change-standards states the condition of each Maturity, who advances a Change to it, and what the review and the audit bind, as [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-transitions: change-standards states the seven Transitions, what each requires and changes, who makes each, and the keys of the comment that logs each, as [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-structure: change-standards states when a Change is a Leaf or a Parent, that every Change names one Product, and how a merge and a blocker resolve, as [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-form-check: change-standards states every rule the form check judges before a publish, as [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-store: change-standards states the home of each part of a record in a GitHub Change Store, as the github-store Mapping of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- standards-closing: change-standards states when a Leaf closes Applied, and that no Transition moves an Applied or Abandoned Change, as leaf-applied and terminal of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) state them.
- standards-replaced: change-standards states no `## Intent` section, no Governance mutations or Spec mutations block, no Executable Maturity, no Claimed Lifecycle, no Executor, no merge composition, and no authority read from a move out of Submitted.

### Audit: form check

- form-check-run: author-change runs the form check, one standard-library script in change-standards, before every publish below Applicable and before every publish that writes the body of an Applicable record, and publishes nothing while the check fails.
- form-check-rules: The form check fails a Draft for each breach of these rules of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md), and names the slug of the rule each finding breaks: record-keys, record-body, statement-of-intent, subsection-headings, payloads, headers, diff-lines, body-lines-only, no-tag, plain-slug, table-case, front-matter-block, no-index, depends-on-form, precedes-form, new-path-reference, move-reads, one-payload, fence, no-mode, operation-kinds, spec-deletion, one-subsection-per-file, new-sibling-names, slug-rename, path-naming, infrastructure-line, replaced-assertion, infrastructure-form, infrastructure-exists, spec-node-none, none-leaf, one-product, draft-lifecycle, draft-base, size-limit, stale-revision, operator-bound-base, and one-home.
- form-check-reads-only: NEVER: the form check writes a file or the Change Store.

### Audit: author-change

- author-publish: author-change records a Change, publishes a revision of its record, and splits a Leaf, each from a Change Draft, and writes each part of the record to its home in the GitHub issue, as the github-store Mapping of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- author-trace: Before each publish at Framed or Sliced, author-change traces each result the Verification part of the Statement of Intent names to the Declarations line that carries it, and repairs the record for each result no line carries.
- author-audit-dispatch: author-change dispatches change-auditor for a Sliced Leaf, with the issue reference of its record and the checkout root, and the holder advances the Leaf to Applicable only when the sealed run of that audit holds no finding at the current Base of the record.
- author-publish-command: author-change routes every publish through one command that runs the form check on the exact Draft and writes to the Change Store only when it passes, writing the title, Product, Parent, predecessors, blockers and base from the Draft, clearing each of them the Draft empties or leaves out, and leaving every other field as the Change Store holds it; its SKILL.md names no other way to write a record.
- author-foreign-proposed: author-change records a Proposed Change for another Product of the declared Change Store from a checkout of a different repository.
- author-draft-store: author-change creates each Change Draft through `spx draft create --kind change`, which names the Draft's one file before any Draft text exists, writes and edits the Draft only at the absolute path that command returns, passes no Draft text on standard input and writes no payload file, finds a Draft to resume through `spx draft list --kind change`, and never deletes a Draft.

### Audit: audit-change

- audit-record: audit-change audits one Sliced Leaf, each Declarations line against every Decision Record that governs its Node at the Base, read as the Declarations change it, and every finding blocks, as audit-before-applicable of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states it.
- audit-close: audit-change audits the default branch against the record of a Leaf before the Leaf closes Applied, as audit-at-close of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states it.
- audit-auditor: The change-auditor definition fronts audit-change, takes the issue reference of the record and the checkout root as its task message, and returns a blocked result for any other task message.
- audit-retention: NEVER: the session that runs audit-change writes a copy of the record it audits; the runner of audit-change retains the record's Change Draft, and the session writes only runner request files.
- draft-command-retired: NEVER: a Change skill, the runner of audit-change, or the change-auditor definition invokes `spx change draft`.

### Audit: manage-change

- manage-transitions: manage-change makes each of the seven Transitions on one Change, one subcommand per Transition, as the transitions Mapping of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states them.
- manage-requires: manage-change refuses a Transition on a Change that does not stand in the state the transitions Mapping requires, and names the state it found.
- manage-actors: manage-change makes a Transition only for the actor transition-actor of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) names for it, and refuses every other caller.
- manage-log: manage-change posts the one comment that logs each Transition, as log-block, log-keys, log-position, and log-extras of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) state it.
- manage-store: manage-change writes each field a Transition changes to its home in the GitHub issue, as the github-store Mapping of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) states it, and keeps at most one assignee on the issue.
- store-options: author-change and manage-change write to the Maturity, Lifecycle, Value, and Investment fields of a GitHub Change Store only the values record-keys of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) names for maturity, lifecycle, primary_value, and investment, and stop with a blocked result naming the field when its options differ from those values.
- manage-only: NEVER: a claim-change, release-change, close-change, or confirm-change skill exists beside manage-change.
