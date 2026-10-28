# Change Record Contract

A Change is a self-contained, store-neutral coordination record for one intended Output. Its body carries content only and opens with an Intent; every state and every authority event is read from the coordination store. Its record shape, Maturity-specific Definitions of Ready, authority, Lifecycle transitions, persistence behavior, and compatibility boundary are fixed by this decision; `audit-change` produces its Agentic verdict under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).

## Record

The store holds these fields of a Change; the body holds none of them:

| Field          | Contract                                                                                                                                                                                                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | The intended Output, stated as a title.                                                                                                                                                                                                                                           |
| `product`      | The one Product that owns the Change; a root whose work spans Products carries none.                                                                                                                                                                                              |
| `maturity`     | Exactly one of `Proposed`, `Framed`, `Sliced`, or `Applicable`.                                                                                                                                                                                                                   |
| `lifecycle`    | Exactly one of `Available`, `Submitted`, `Applied`, or `Abandoned`; Lifecycle changes independently of Maturity.                                                                                                                                                                  |
| `predecessors` | The append-only list of Change identities this Change absorbed by a merge; a Change that absorbed none carries `[]`.                                                                                                                                                              |
| `blocked_by`   | The mutable list of Change identities that must close `Applied`, or resolve through the Change that absorbed them, before this Change is unblocked; a blocker closed `Abandoned` that no Change absorbed returns this Change to refinement, and an unblocked Change carries `[]`. |
| `parent`       | The canonical identity of the Parent Change in the same store; a Change with no Parent carries `null`.                                                                                                                                                                            |

The body opens with `## Intent`, which carries these parts:

| Part        | Content                                                                                                                                               |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| What        | The Output the Change achieves: a decision or spec evolution, a lower-layer reconciliation, or both.                                                  |
| Why         | What makes the work worth doing: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves. |
| Observation | Optional: the observed state that gives rise to the Change.                                                                                           |
| Evidence    | The observable result by which anyone checks that the Output is achieved.                                                                             |

The title has at most 15 words.

The body carries no attestation, accountable-person, priority, or overrule text; the authority for each Maturity is read from the store, as Authority states. Field values are never restated or maintained as body lines; each place that holds a Change keeps each field in its one home, as Persistence states. Provider conversations, transcripts, cost estimates, resource accounting, and routine local commands are not record content.

## Final format

- record-no-front-matter: A Change record carries no front matter; its title, Product, Maturity, Lifecycle, Parent, predecessors, and blockers are fields of the store, and its body opens with `## Intent`.
- record-sections: The record body opens with `## Intent` and continues with `## Verification` and `## Governance`, in that order; a Leaf carries `## Verification` from Proposed on, a Parent carries none, Framed adds `## Assumptions` when the Frame settled a question, Sliced adds `## Slice`, Applicable adds no section, and a Proposed record may end with `## Open questions`, which Framed and every later Maturity omit.
- record-intent: The Intent runs at most 60 words including its labels. It holds What, Why, an optional Observation, and Evidence, and a list inside a part stands in parentheses.
- record-verification: `## Verification` holds one subsection for each Node the Change touches and each Decision Record it writes, flat and in Application order; a subsection is a `###` heading with the full path from `spx/`, followed by one fenced `diff` block.
- verification-diff-lines: The first character of each line in a `diff` block is its operation, a space for context, `-` for removal, or `+` for addition; `+ <slug>: <text>` adds an Assertion or decision, `- <slug>` removes it, a `-` line followed by a `+` line on the same slug replaces it, and renaming a slug is a removal and an add.
- verification-node-lines: A Node's opening and malleability stand as context lines; a `-` and `+` pair changes either; a Node the Change creates holds `+` lines only; removing the opening deletes the Node; a `- path:` line followed by a `+ path:` line moves it, and the subsection heading names the new path; `+ title:` names a new Decision Record, and removing every decision deletes the record.
- assertion-tags: Tags close an Assertion line in this order, each present only when it carries a value: the verification type, exactly one of `[test: scenario]`, `[test: mapping]`, `[test: conformance]`, `[test: property]`, `[test: compliance]`, `[eval]`, `[probe]`, or `[audit]`; `[level: l1]`; `[infra: <node path>]`, which names the spec Node that governs the harness, generator, or fixture the test needs; and `[carries: spx/<record>#<slug>]`, one for each decision rule the Assertion carries; the Assertion text before the tags holds no `[`.
- compliance-rule: A `[test: compliance]` line and a `testing: compliance` decision state an ALWAYS or NEVER rule.
- decision-sections: A decision line ends with its section, `[statement]`, `[property]`, `[testing: <assertion type>]`, or `[audit]`.
- line-states-meaning: A diff line states what the Assertion or decision asserts and copies no file wording; the Applier writes the file's wording, and an Audit checks the meaning against the line.
- record-governance: `## Governance` opens with `- Base: <commit SHA>`, a commit on the default branch, and then lists `- [<path>](<path>): <value>` for each Decision Record the Change writes and each one in the Walk of a Node it touches; the value is `new`, `amended`, or `in force`.
- record-slice: `## Slice` holds `- Repository:` and `- Check:`, one repository and one observable check, which is one trigger and its result.
- node-bound: A Change touches at most five Nodes, Decision Records not counted; a wider Change splits into ordered children of a Parent.
- malleability-step: Malleability moves one layer per Change.
- infrastructure-blocking: Missing test infrastructure is the Output of a separate Change, which the store records as blocking the Change that needs it; a Node may govern the test infrastructure its own tests need.
- rationale-home: Settled rationale has one home; a child Change links it and records only the assumptions it adds or changes, and a Parent copies none of its children's content.
- operator-review: The Operator reviews every decision line, every removal, and every replace on a Node whose malleability before the Change is not `spec`, as part of the Confirmation at Sliced.
- application-check: Before the first block, a check evaluates the lines as one transaction against the current default branch and the ordered effects of the earlier subsections of the same Change: a `-` and `+` pair on one slug requires the slug present, a `+` slug with no `-` partner requires it absent, a `-` slug with no partner requires it present, an opening or malleability line of a Node the Change creates requires the Node absent, each other `-` malleability line and each opening line matches the Node, each move destination is free, a target an earlier subsection produces is checked against that projected state, and each `carries` target and `infra` Node resolves in the current tree or in an earlier subsection.
- application-base: The check also compares the text of each target that exists at the declared Base, an Assertion, decision, opening, or malleability line a `-` or context line names, with its text on the default branch; a changed target, or a failed line, returns the Change to Sliced with the failed lines named, and a bundled script of the execution skill runs the check.
- application-waits: A Change whose blocking Change is not yet delivered waits for it; only a failed check returns a Change to Sliced.
- form-readers: The Change skills write and execute only the new form; `author-change` reads a record in the earlier form only to carry its proposal into the new form at that revision and converts no body in place, and a record in the earlier form at `Executable`, the earlier name of `Applicable`, executes under the skills it was refined for, before the Change skills ship.
- option-names: The Maturity values are `Proposed`, `Framed`, `Sliced`, and `Applicable`, the Lifecycle values are `Available`, `Submitted`, `Applied`, and `Abandoned`, `Executable` maps to `Applicable` alone, and `Claimed` has no successor value.
- held-change: A Change is held when its assignee list is not empty, in every Lifecycle; `claim-change` writes no Lifecycle value, and `release-change` and `close-change` require this session's assignee and winning Claim in place of Lifecycle `Claimed`.
- retired-names: The Change skills refuse `Executable` and `Claimed` and hold no handling for either name.
- audit-at-applicable: `author-change` dispatches the change audit once, when a Leaf reaches Applicable; a revision below Applicable takes only a deterministic check of the record's form, and its publication and Confirmation need no change audit.
- no-execution-status: The record carries no execution status: no Node state, no link to produced content, and no progress. Execution records its progress only in its Handoff.
- store-predecessors: The store field `Predecessors` names the Changes this Change absorbed by a merge.
- change-type: A Change whose record carries a `## Verification` section is a Leaf, a Change that another Change names in `parent` is a Parent, and a Change with neither is a root.
- parent-product: A Change carries the Product that owns its Output, and a Parent and its children may carry different Products.
- execution-order: Execution takes the Verification subsections in record order, which is Application order. The merge composition for the Node's malleability after, and the decision-record audit of a record, select each subsection's results and Verifiers.
- applied-leaf: A Leaf closes Applied when the merge commit of the pull request or branch its newest Handoff names is an ancestor of the default branch, every Node holds every result the merge composition for its malleability after selects, every amended or new record holds an approving decision-record audit, and the Intent's Evidence is met.
- handoff-blocks: A Handoff names the branch or pull request with its head commit, the completed Verification subsections by path, and the next one, or `refinement: <Maturity> → <next level>` below Applicable.
- change-path-root: A change audit resolves each path a record names, its Governance records and its Spec mutations Nodes, in the repository of the Change's Product, whatever checkout holds the draft or runs the audit.

## Slugs

- migration-first: The slug migration is no diff-line Change; `migrate-3-to-4` runs on a Product's tree before any diff-line Change against that tree reaches Sliced, so every `-` line names a slug that exists.
- slug-stability: A slug is the stable name of its Assertion or decision; a move, extraction, or consolidation keeps it; every `carries` reference whose target identity, path or slug, changes is rewritten in the same move, a Decision Record that moves to a new path with its slugs unchanged included; a slug a move would repeat in the destination file changes in that move; the migration keeps each `[audit:{rule-slug}]` rule slug as the leading slug, so a stored audit result key keeps identifying the same Assertion; an audit result whose slug a collision rename changes is remapped only when the unchanged text and path prove the subject and is otherwise invalidated, and a destination's existing result under the same slug is never reused; an audit result for a slug whose text changed is invalid and produced again.

## Definitions of Ready

Each Definition of Ready is an independently loadable criterion set, and the sets are cumulative: a level's Definition of Ready includes every criterion of the preceding level's. No criterion is an audit verdict, and no criterion requires a body authority line.

### Proposed

- proposed-ready: A Proposed Change is ready when its Intent states What, Why, and Evidence, a Leaf's `## Verification` holds a subsection for every Node it touches and every Decision Record it writes, and `## Governance` opens with its Base and lists every record the Output touches or that governs it.

Readiness at Proposed requires no operator review statement in the record.

### Framed

- framed-ready: A Framed Change is ready when the Proposed Definition of Ready holds, every subsection of a Leaf's `## Verification` states its Assertions and decisions as diff lines, and no question stays open: each question the Frame settled stands under `## Assumptions` as its answer and one sentence of reason. A Parent has no Node of its own, carries no `## Verification`, and meets the Framed criteria without one.

### Sliced

A Sliced Change is ready when:

- the Framed Definition of Ready holds;
- a Leaf's `## Slice` names the one repository and the one observable check of one coherent, independently integrable unit whose dependencies and sequence are resolved; and
- a Parent is Sliced when every child exists naming it in `parent` and its record carries no `## Verification`; a Parent never reaches Applicable.

### Applicable

An Applicable Change is ready when:

- the Sliced Definition of Ready holds;
- `## Slice` is complete and the Verification subsections state every consequential decision for the changeset; Applicable adds no section.

The merge composition is the one the `Merge` section of the 4.0 Projection chapter states — `versions/4.0/methodology/product-tree/verification/projection.md` inside the declared `methodology.source` — which defines when a changeset touches a node, the predicates a changeset selects by its least malleable touched node and by a product spec or outcome-record change, when a result is produced again before merge, the dependency protection that fails a changeset raising a malleability or ending `Passing` in the closure of an effectively `Passing` consumer, and the decision-record audit as an authoring check that produces no node-local result.

## Review bar

- review-bar: A Change record is held only to what its review needs. A failed Definition of Ready criterion is a blocking finding; a finding against any other record rule, among them the title and Intent word limits, section order, heading form, verdict wording, and malleability notation, is non-blocking and is returned `filed`.
- one-audit: A Leaf receives its change audit once, when it reaches Applicable, and its findings never withhold publication, claiming, or execution; the Author repairs what takes a minute and publishes. A blocking finding refuses only the Maturity it judges: the record publishes at the highest Maturity whose blocking criteria it meets, and at Proposed when it meets none. A revision below Applicable takes only a deterministic check of the record's form.
- unsettled-question: A question no assumption can defend goes, with the Refiner's best answer, to the superior that assigned the refinement — the agent that gave the task, or the operator when no agent did — and refinement continues on every part that does not depend on the answer.

## Authority

Maturity advances past Proposed, Framed, and Sliced only when the store shows the Product's Maintainer's move of the Change out of `Submitted` at that Maturity. At Proposed that move is the priority decision; at Framed it attests that the Change captures the operator's intent; at Sliced it confirms the slice. The Refiner advances Sliced to Applicable inside the authority of the confirmed slice, with no further move.

- authority-move: The authority for leaving a Maturity is the Product's Maintainer's Lifecycle move of the Change out of `Submitted` to `Available` while the Change held that Maturity; the store's field-change event gives its actor and time, and no confirmation comment is posted or read. A rejection is an instruction naming what to fix, sent to the Director or the Product's Maintainer or written as a plain comment on the Change; no rejection record exists, and the holder repairs the record and submits it again.
- frame-next: A Change the Product's Maintainer confirms at Proposed is framed next, ahead of the Product's other Proposed Changes.
- rejection-lowering: A rejection at Framed or Sliced lowers Maturity one level in the same move that takes the Change out of `Submitted`, written by whoever rejects, so that move authorizes leaving only the lowered Maturity, the one the Change held before the rejected stage; whoever rejects writes the lowered Maturity before the Lifecycle move out of `Submitted`; `author-change` writes no rejection lowering; a rejection at Proposed leaves the Change `Submitted`, and it means not now. `change-standards`, `author-change`, and `release-change` state one order: the holder's release comes first, the rejecting lowering of Maturity second, the rejecting move out of `Submitted` third, and further refinement only after a session claims the Change again.

## Lifecycle

- lifecycle-transitions: Lifecycle records whether the Change waits for the Product's Maintainer, or how it ended: `Available` means no stage waits for the Maintainer, `Submitted` means a published stage waits for the Maintainer, and `Applied` and `Abandoned` are terminal. Holding is the assignee list alone, as held-change states; `Submitted` has no holder. One skill moves each transition and moves nothing else: `claim-change` adds the holder and writes no Lifecycle value; `release-change` removes the holder and writes `Available`, or `Submitted` for its `submit` result; `confirm-change` moves `Submitted` to `Available`; and `close-change` moves a held Change to the terminal value its one argument names. None of the four writes Maturity or a body section; `claim-change`, `release-change`, and `close-change` each post only their own comment — the Claim, the Handoff, or the terminal record — and `confirm-change` posts none. Maturity moves only through `author-change`, except that a rejection lowers it one level, written before the move out of `Submitted`. Author, Fixer, and Verifier roles hold no claim.
- submitted-not-ready: Lifecycle `Submitted` means the record waits for the Product's Maintainer's review and is not ready for work at the next Maturity; no session claims, refines, or executes it until the Maintainer moves it out of `Submitted`.

A claim requires an open record whose Product is the configured Product, or that is a root carrying no Product, whose Maturity is one declared value, whose Lifecycle is `Available`, and whose assignee list is empty; any other state, `Submitted` included, is reported without mutation. The claim adds the holder and records the Claim — the claiming agent session and the worktree root the Change is claimed for, which is the session's own assigned root or a root it names. When two sessions claim at once, the earliest Claim after the latest Handoff wins, and the losing session withdraws its own holder record and reports the winner. The Change's holder is the session whose assigned worktree root equals the root the winning Claim names; a release or a close runs only for that session.

A release requires the Handoff: branch or changeset, the completed Verification subsections and the next one, blockers, and the hazards the next holder cannot derive quickly — never a secret and never content that belongs in the body. What the holder learned about the Output is refined into the body through `author-change` before the release. The release writes the Handoff, removes the holder, and writes `Available`; with the `submit` result, the holder publishes the record at the Maturity it reached and the release writes `Submitted` in place of `Available`. Maturity stays as it is, and an `Available` Change may be claimed by any agent session next.

- lifecycle-confirmation: A confirmation acts for the Product's Maintainer on a `Submitted` Change only, and reports any other Lifecycle without mutation. It writes `Available` and posts no comment.

A close requires its terminal precondition from current state, not from the holder's account. A Leaf's `Applied` follows the decision applied-leaf of `## Final format`; a merged pull request alone is not `Applied`. A Parent closes `Applied` when every child has closed and its last child closed `Applied`; a Parent that has a Parent closes this way through the cascade, and a Parent with no Parent closes the same way through `close-change`. A root closes `Applied` when the operator judges its Intent met, and `Abandoned` when the operator drops it. `Abandoned` requires the operator's explicit direction and records the operator's stated reason. The close writes the terminal record, removes the holder, writes the terminal Lifecycle, and closes the record with the matching reason. A terminal Change receives no Handoff and never returns to `Available`.

A split creates children that name the source in `parent`, and the source drops its `## Verification`. A merge closes the absorbed Change `Abandoned` and adds it to the survivor's `predecessors`. A reframe edits the Change in place and lowers its Maturity to `Proposed`. Execution begins only on a held, Applicable Leaf whose every predecessor is closed and whose blockers are resolved.

Every transition is an ordered write with a complete readback: each write lands in its declared order, the transition reads Product, Maturity, Lifecycle, the holder, and the newest Claim, Handoff, or terminal record back from the store, and it completes only when every value equals the intended state. When a write fails or a readback differs, the transition stops before every later mutation and reports the completed writes in order, the failed operation, and the observed state; no later write is guessed to make a partial transition look complete.

## Persistence

Each of the seven fields has exactly one home in each place that holds the Change, and no place writes a field twice. A coordination store holds each field in the one native feature the plugin assigns it, and its body holds the Intent and the sections the Maturity adds, with no front matter and no lineage line. A local draft is the body alone. Persistence writes each field to its home and the body to the store body, reads each back unchanged, and reports success only then. A coordination-store limit never shapes the record.

In the GitHub store the homes are:

| Field          | Home                                                                                                                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | The issue title                                                                                                                                                                          |
| `product`      | The organization issue field `Product`                                                                                                                                                   |
| `maturity`     | The organization issue field `Maturity`                                                                                                                                                  |
| `lifecycle`    | The organization issue field `Lifecycle`                                                                                                                                                 |
| `predecessors` | The organization text issue field `Predecessors`: the canonical identities, such as `outcomeeng/changes#17`, separated by a comma and one space, and empty when the Change absorbed none |
| `parent`       | The organization number issue field `Parent`: the Parent's issue number, empty for none                                                                                                  |
| `blocked_by`   | GitHub's native issue dependencies                                                                                                                                                       |

No project field holds a Change field.

- persistence-authority: The GitHub store records each change of an issue field as an `IssueFieldChangedEvent` carrying its actor, its time, and the previous and new value; the event for a Lifecycle move out of `Submitted` is the store's record of authority. The Lifecycle comments — the Claim, the Handoff, and the terminal record — are the store's record of holding and continuation, not of the Change's content.

The persistence skill instruction selects the client for the configured store; the record embeds no store commands or provider identifiers.

## Compatibility

A record in the earlier form — front matter, a body that opens with `# Output`, `## Governance mutations` or `## Spec mutations` sections, or the sections `## Nodes`, `## Assertion operations`, `## Decisions`, `## Mutations`, or `## Activities` — receives no in-place conversion. `author-change` reads it only to carry its proposal into the new form at that revision, and `audit-change` judges the new form alone. A record in the earlier form at `Executable` executes under the skills it was refined for, before the Change skills ship, as form-readers states.

## Rationale

One self-contained record preserves Change meaning across local drafting and coordination stores, and one home per field in each place leaves no second copy to drift from the first, while cumulative, independently loadable Definitions of Ready let authoring and audit judge exactly the Maturity a record declares. The Intent opens every record so that what a Change achieves and how anyone checks it are settled before refinement starts. Diff lines give an Assertion, an audit result, and a test file one stable slug, and a check against the current default branch catches a stale line before any block runs.

- authority-rationale: Authority lives in the store because any writer of the body can type an attestation line, while the store's field-change event carries an actor and a time no body writer controls. Proposed readiness is the Proposed Definition of Ready, and the audit verdict stays outside every criterion set it judges, so each Definition of Ready is decidable and a higher level inherits the preceding level's criteria, never a verdict about another level.

Authoring a record in another form anew from its proposal leaves no inferred field to disagree with the final format. The holder is keyed on the worktree the Claim names, because one account runs several sessions and a session that claims for another — one that starts the Executor's session in a worktree of its own — is not the session that later releases or closes; the worktree separates the holder from every other session of the account while letting the session started in it hold what was claimed for it. Holding is the assignee list in every Lifecycle, so no Lifecycle value duplicates it. Execution derives each subsection's results and Verifiers from the merge composition, because an obligation the composition does not select sends an Executor through Verifier rounds no gate requires, and an omitted one lets a Change reach `Applied` short of the results its Nodes' merge compositions select. A Change's type derives from what its record and the store name, so no stored type can disagree with them, and a Parent hands its `## Verification` to its children, so no Change both coordinates children and carries a changeset. One change audit at Applicable spends time and tokens on the small fraction of Changes that reach it.

## Product properties

1. A Change's record carries content only — its Intent and the sections its Maturity adds — and remains portable across coordination stores; who holds the Change, who authorized each Maturity, and where its work continues are read from the store's field-change events, assignee list, and Lifecycle comments under the Lifecycle rules.
2. Maturity advances only when the declared level's cumulative Definition of Ready holds and, past Proposed, Framed, and Sliced, the store shows the Product's Maintainer's move out of `Submitted` at that Maturity.
3. Lifecycle moves through one skill per transition — claim, release with a Handoff or submission, confirmation, close to a named terminal value — each an ordered write with a complete readback that never touches Maturity; persistence preserves field equality, and the Change skills write and judge the new form alone.
4. An Assertion or decision keeps one slug across its diff line, its audit result, and its test file, through every move, extraction, and consolidation.

## Verification

- record-no-front-matter-compliance: ALWAYS a Change record carries no front matter, and its body opens with `## Intent` carrying What, Why, and Evidence, followed by `## Verification`, `## Governance`, and the sections its declared Maturity adds in their declared order.
- dor-cumulative: ALWAYS Proposed, Framed, Sliced, and Applicable each have one independently loadable, cumulative Definition of Ready, and no Definition of Ready requires a body authority line.
- maturity-authority: ALWAYS Maturity advances past Proposed, Framed, and Sliced only when the target level's Definition of Ready holds and the store shows the Product's Maintainer's move of the Change out of `Submitted` at the Maturity it leaves, read from the store's field-change event with its actor and time.
- no-body-authority: NEVER a Change body carries attestation, accountable-person, priority or overrule text.
- word-limits: ALWAYS the change audit counts the title's words and the Intent's words and reports a record over a limit as a non-blocking finding naming the section, the limit, and the count.
- field-homes: ALWAYS persistence writes each field to its one home in the configured coordination store and the body to the store body, and reads each back unchanged before reporting success; a coordination-store limit never shapes the record.
- no-second-home: NEVER a place holds a Change field in two homes, a store body carries front matter or a lineage line, or a project field holds a Change field.
- form-readers-compliance: ALWAYS the Change skills write and execute only the new form, and `author-change` reads a record in the earlier form only to carry its proposal into the new form at that revision and converts no body in place.
- retired-names-compliance: NEVER a Change skill accepts `Executable` or `Claimed` as a value or holds handling for either name.
- claim-contract: ALWAYS `claim-change` claims only an open record whose Product — the configured Product, or none for a root — Maturity, `Available` Lifecycle, and empty assignee list verify from current state, and reports any other Lifecycle, `Submitted` included, without mutation; it adds the holder, records the Claim naming the claiming session and the worktree root the Change is claimed for, writes no Lifecycle value, and reads the complete state back before execution begins, and a losing concurrent claim withdraws its own holder record and reports the winner.
- holder-only: ALWAYS `release-change` and `close-change` run only for the session whose assigned worktree root equals the root the winning Claim names and whose assignee is the holder, and report any other caller without mutation.
- release-contract: ALWAYS `release-change` writes a Handoff carrying branch or changeset, the completed Verification subsections and the next one, blockers, and hazards, then removes the holder, writes `Available` — or `Submitted` for its `submit` result — and reads the complete state back, leaving Maturity unchanged.
- confirm-contract: ALWAYS `confirm-change` moves only a `Submitted` Change, writing `Available` with no comment, and reads the complete state back; it reports any other Lifecycle without mutation.
- close-contract: ALWAYS `close-change` verifies the named terminal precondition from current state, writes the terminal record, removes the holder, writes the terminal Lifecycle, closes the record with the matching reason, and reads the complete terminal state back; it refuses an argument outside `Applied` and `Abandoned`, refuses `Applied` for a Leaf while the merge commit of the pull request or branch its newest Handoff names is not an ancestor of the default branch, a Node lacks a result the merge composition for its malleability after selects, an amended or new record lacks an approving decision-record audit, or the Intent's Evidence is unmet, refuses `Applied` for a Parent while a child is open or its last child closed other than `Applied`, and closes a root only on the operator's direction.
- lifecycle-skills-scope: NEVER a Lifecycle skill writes Maturity or a body section, or posts a comment other than its Claim, Handoff, or terminal record.
- no-write-after-failure: NEVER a Lifecycle transition performs a later mutation after a required write fails or a readback differs from the intended state; its diagnostic names every completed write, the failed operation, and the observed state.
- no-secrets: NEVER a Handoff, Claim, terminal record, or rejection instruction carries a secret value or credential payload.
- change-path-root-compliance: ALWAYS the change audit resolves each path a record names, its Governance records and its Spec mutations Nodes, in the repository of the Change's Product, whatever checkout holds the draft or runs the audit.
- parent-no-verification: ALWAYS a Change that another Change names in `parent` carries no `## Verification` and never reaches Applicable; the change audit rejects a record that breaks the rule.
- audit-at-applicable-compliance: ALWAYS `author-change` dispatches the change audit once, when a Leaf reaches Applicable, and a revision below Applicable takes only a deterministic check of the record's form.
- diff-line-grammar: ALWAYS `audit-change` raises a finding on a `## Verification` subsection that holds no fenced `diff` block, on a diff line whose operation breaks the line grammar, on an Assertion line whose tags break their order, on a compliance line that states no ALWAYS or NEVER rule, and on a record that touches more than five Nodes.
- application-transaction: ALWAYS the application check evaluates the lines as one transaction against the current default branch and the ordered effects of the earlier subsections, compares each target's text at the declared Base with its text on the default branch, returns the Change to Sliced with the failed lines named on a failure or a changed target, and leaves a Change whose blocking Change is not yet delivered waiting.
- migration-first-compliance: ALWAYS the slug migration runs on a Product's tree before any diff-line Change against that tree reaches Sliced, and it is itself no diff-line Change.
- slug-kept-on-move: ALWAYS a move, extraction, or consolidation keeps each Assertion's and decision's slug and rewrites every `carries` reference whose target path or slug changes in the same move.
- no-result-reuse: NEVER a collision rename reuses a destination's existing audit result under the same slug, and an audit result for a slug whose text changed stays valid.
