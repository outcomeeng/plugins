# Change Record Contract

A Change is a self-contained, store-neutral coordination record for one intended Output. Its body carries content only and opens with an Intent; every state and every authority event is read from the coordination store. Its record shape, Maturity-specific Definitions of Ready, authority, Lifecycle transitions, persistence behavior, and compatibility boundary are fixed by this decision; `audit-change` produces its Agentic verdict under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).

## Record

Every Change begins with YAML front matter containing exactly these required keys:

| Key            | Contract                                                                                                                                                                                                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | The intended Output, stated as a title.                                                                                                                                                                                                                                           |
| `product`      | The one Product that owns the Change; a root whose work spans Products carries none.                                                                                                                                                                                              |
| `maturity`     | Exactly one of `Proposed`, `Framed`, `Sliced`, or `Executable`.                                                                                                                                                                                                                   |
| `lifecycle`    | Exactly one of `Available`, `Claimed`, `Submitted`, `Applied`, or `Abandoned`; Lifecycle changes independently of Maturity.                                                                                                                                                       |
| `predecessors` | The append-only list of Change identities this Change absorbed by a merge; a Change that absorbed none carries `[]`.                                                                                                                                                              |
| `blocked_by`   | The mutable list of Change identities that must close `Applied`, or resolve through the Change that absorbed them, before this Change is unblocked; a blocker closed `Abandoned` that no Change absorbed returns this Change to refinement, and an unblocked Change carries `[]`. |
| `parent`       | The canonical identity of the Parent Change in the same store; a Change with no Parent carries `null`.                                                                                                                                                                            |

No other front-matter key is valid. The body opens with `## Intent`, which carries these parts:

| Part        | Content                                                                                                                                               |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| What        | The Output the Change achieves: a decision or spec evolution, a lower-layer reconciliation, or both.                                                  |
| Why         | What makes the work worth doing: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves. |
| Observation | Optional: the observed state that gives rise to the Change.                                                                                           |
| Evidence    | The observable result by which anyone checks that the Output is achieved.                                                                             |

The title has at most 15 words.

The body carries no attestation, accountable-person, priority, or overrule text; the authority for each Maturity is read from the store, as Authority states. Front-matter values are never restated or maintained as body lines; each place that holds a Change keeps each field in its one home, as Persistence states. Provider conversations, transcripts, cost estimates, resource accounting, and routine local commands are not record content.

## Final format

- final-format-only: Skills write, judge, and execute only a Change record in the final format. A record in another form receives no migration, alias, or inferred field, and its next revision authors the record anew from the proposal it carries.
- record-sections: The record body opens with `## Intent`. Proposed adds `## Governance`, `## Governance mutations`, and `## Spec mutations`, whose blocks name each affected Node by its opening line; Framed states each Node's assertions and adds `## Assumptions` when the Frame settled a question; Sliced adds `## Slice`; Executable adds no section. The order is Intent, Governance, Governance mutations, Spec mutations, Assumptions, Slice, and a Proposed record may end with `## Open questions`, which a Framed record leaves empty.
- record-intent: The Intent runs at most 60 words including its labels. It holds What, Why, an optional Observation, and Evidence, and a list inside a part stands in parentheses.
- record-governance: `## Governance` lists every record the Output touches or that governs it, by its path from `spx/`, each with the verdict `in line`, `amended`, or `new`.
- record-governance-mutations: `## Governance mutations` holds one block for each amended or new record. The block opens with `<path> states:`, lists its decisions in exact text, each opening with a slug and a colon.
- record-spec-mutations: `## Spec mutations` holds one block for each Node in execution order. The block opens with `<path>: <malleability before> -> <malleability after>`. The block continues with `<file> states:` and the Node's assertions as bare bullets.
- record-slice: `## Slice` holds `- Repository:` and `- Check:`, one repository and one observable check, which is one trigger and its result.
- no-execution-status: The record carries no execution status: no Node state, no link to produced content, and no progress. Execution records its progress only in its Handoff.
- draft-predecessors: The local draft names the Changes this Change absorbed by a merge in the key `predecessors`, and the store field `Predecessors` holds the same value.
- change-type: A Change whose record carries a Governance mutations or Spec mutations block is a Leaf, a Change that another Change names in `parent` is a Parent, and a Change with neither is a root.
- parent-product: A Change carries the Product that owns its Output, and a Parent and its children may carry different Products.
- execution-order: Execution takes the Governance mutations blocks, then the Spec mutations blocks, each in record order. The merge composition for the Node's malleability after, and the decision-record audit of a record, select each block's results and Verifiers.
- applied-leaf: A Leaf closes Applied when the merge commit of the pull request or branch its newest Handoff names is an ancestor of the default branch, every Node holds every result the merge composition for its malleability after selects, every amended or new record holds an approving decision-record audit, and the Intent's Evidence is met.
- handoff-blocks: A Handoff names the branch or pull request with its head commit, the completed Governance mutations and Spec mutations blocks by path, and the next block, or `refinement: <Maturity> → <next level>` below Executable.

## Definitions of Ready

Each Definition of Ready is an independently loadable criterion set, and the sets are cumulative: a level's Definition of Ready includes every criterion of the preceding level's. No criterion is an audit verdict, and no criterion requires a body authority line.

### Proposed

- proposed-ready: A Proposed Change is ready when its Intent states What, Why, and Evidence, `## Governance mutations` holds the exact text of every decision the Output adds or amends, `## Governance` lists every record the Output touches or that governs it, and `## Spec mutations` names every Node the Output touches.

Readiness at Proposed requires no operator review statement in the record.

### Framed

- framed-ready: A Framed Change is ready when the Proposed Definition of Ready holds, every affected or intended Node has a Spec mutations block stating its assertions, and no question stays open: each question the Frame settled stands under `## Assumptions` as its answer and one sentence of reason.

### Sliced

A Sliced Change is ready when:

- the Framed Definition of Ready holds;
- a Leaf's `## Slice` names the one repository and the one observable check of one coherent, independently integrable unit whose dependencies and sequence are resolved; and
- a Parent is Sliced when every child exists naming it in `parent` and its record carries neither a Governance mutations nor a Spec mutations block; a Parent never reaches Executable.

### Executable

An Executable Change is ready when:

- the Sliced Definition of Ready holds;
- `## Slice` is complete and the Governance mutations and Spec mutations blocks state every consequential decision for the changeset; Executable adds no section.

The merge composition is the one the `Merge` section of the 4.0 Projection chapter states — `versions/4.0/methodology/product-tree/verification/projection.md` inside the declared `methodology.source` — which defines when a changeset touches a node, the predicates a changeset selects by its least malleable touched node and by a product spec or outcome-record change, when a result is produced again before merge, the dependency protection that fails a changeset raising a malleability or ending `Passing` in the closure of an effectively `Passing` consumer, and the decision-record audit as an authoring check that produces no node-local result.

## Review bar

- review-bar: A Change record is held only to what its review needs. A failed Definition of Ready criterion is a blocking finding; a finding against any other record rule, among them the title and Intent word limits, section order, heading form, verdict wording, and malleability notation, is non-blocking and is returned `filed`.
- one-audit: Each revision of a Change record receives at most one change audit, and its findings never withhold publication, claiming, or execution; the Author repairs what takes a minute and publishes. A blocking finding refuses only the Maturity it judges: the record publishes at the highest Maturity whose blocking criteria it meets, and at Proposed when it meets none.
- unsettled-question: A question no assumption can defend goes, with the Refiner's best answer, to the superior that assigned the refinement — the agent that gave the task, or the operator when no agent did — and refinement continues on every part that does not depend on the answer.

## Authority

Maturity advances past Proposed, Framed, and Sliced only when the store shows the Product's Maintainer's move of the Change out of `Submitted` at that Maturity. At Proposed that move is the priority decision; at Framed it attests that the Change captures the operator's intent; at Sliced it confirms the slice. The Refiner advances Sliced to Executable inside the authority of the confirmed slice, with no further move.

- authority-move: The authority for leaving a Maturity is the Product's Maintainer's Lifecycle move of the Change out of `Submitted` to `Available` while the Change held that Maturity; the store's field-change event gives its actor and time, and no confirmation comment is posted or read. A rejection is an instruction naming what to fix, sent to the Director or the Product's Maintainer or written as a plain comment on the Change; no rejection record exists, and the holder repairs the record and submits it again.
- frame-next: A Change the Product's Maintainer confirms at Proposed is framed next, ahead of the Product's other Proposed Changes.
- rejection-lowering: A rejection at Framed or Sliced lowers Maturity one level in the same move that takes the Change out of `Submitted`, written by whoever rejects, so that move authorizes leaving only the lowered Maturity, the one the Change held before the rejected stage; whoever rejects writes the lowered Maturity before the Lifecycle move out of `Submitted`; `author-change` writes no rejection lowering; a rejection at Proposed leaves the Change `Submitted`, and it means not now. `change-standards`, `author-change`, and `release-change` state one order: the holder's release comes first, the rejecting lowering of Maturity second, the rejecting move out of `Submitted` third, and further refinement only after a session claims the Change again.

## Lifecycle

- lifecycle-transitions: Lifecycle records who holds the Change, whether it waits for the Product's Maintainer, or how it ended: `Available` means no holder; `Claimed` means one holder; `Submitted` means a published stage waits for the Product's Maintainer, with no holder; `Applied` and `Abandoned` are terminal. One skill moves each transition and moves nothing else: `claim-change` moves `Available` to `Claimed`; `release-change` moves `Claimed` to `Available`, or to `Submitted` for its `submit` result; `confirm-change` moves `Submitted` to `Available`; and `close-change` moves `Claimed` to the terminal value its one argument names. None of the four writes Maturity or a body section; `claim-change`, `release-change`, and `close-change` each post only their own comment — the Claim, the Handoff, or the terminal record — and `confirm-change` posts none. Maturity moves only through `author-change`, except that a rejection lowers it one level, written before the move out of `Submitted`. Author, Fixer, and Verifier roles hold no claim.
- submitted-not-ready: Lifecycle `Submitted` means the record waits for the Product's Maintainer's review and is not ready for work at the next Maturity; no session claims, refines, or executes it until the Maintainer moves it out of `Submitted`.

A claim requires an open record whose Product is the configured Product, or that is a root carrying no Product, whose Maturity is one declared value, whose Lifecycle is `Available`, and whose holder is empty; any other state, `Submitted` included, is reported without mutation. The claim adds the holder, records the Claim — the claiming agent session and the worktree root the Change is claimed for, which is the session's own assigned root or a root it names — and writes `Claimed`. When two sessions claim at once, the earliest Claim after the latest Handoff wins, and the losing session withdraws its own holder record and reports the winner. The Change's holder is the session whose assigned worktree root equals the root the winning Claim names; a release or a close runs only for that session.

A release requires the Handoff: branch or changeset, the completed Governance mutations and Spec mutations blocks and the next one, blockers, and the hazards the next holder cannot derive quickly — never a secret and never content that belongs in the body. What the holder learned about the Output is refined into the body through `author-change` before the release. The release writes the Handoff, removes the holder, and writes `Available`; with the `submit` result, the holder publishes the record at the Maturity it reached and the release writes `Submitted` in place of `Available`. Maturity stays as it is, and an `Available` Change may be claimed by any agent session next.

- lifecycle-confirmation: A confirmation acts for the Product's Maintainer on a `Submitted` Change only, and reports any other Lifecycle without mutation. It writes `Available` and posts no comment.

A close requires its terminal precondition from current state, not from the holder's account. A Leaf's `Applied` follows the decision applied-leaf of `## Final format`; a merged pull request alone is not `Applied`. A Parent that has a Parent closes `Applied` when every child has closed and its last child closed `Applied`. A root closes `Applied` when the operator judges its Intent met, and `Abandoned` when the operator drops it. `Abandoned` requires the operator's explicit direction and records the operator's stated reason. The close writes the terminal record, removes the holder, writes the terminal Lifecycle, and closes the record with the matching reason. A terminal Change receives no Handoff and never returns to `Available`.

A split creates children that name the source in `parent`, and the source drops its Governance mutations and Spec mutations blocks. A merge closes the absorbed Change `Abandoned` and adds it to the survivor's `predecessors`. A reframe edits the Change in place and lowers its Maturity to `Proposed`. Execution begins only on a Claimed, Executable Leaf whose every predecessor is closed and whose blockers are resolved.

Every transition is an ordered write with a complete readback: each write lands in its declared order, the transition reads Product, Maturity, Lifecycle, the holder, and the newest Claim, Handoff, or terminal record back from the store, and it completes only when every value equals the intended state. When a write fails or a readback differs, the transition stops before every later mutation and reports the completed writes in order, the failed operation, and the observed state; no later write is guessed to make a partial transition look complete.

## Persistence

Each of the seven fields has exactly one home in each place that holds the Change, and no place writes a field twice. A local draft carries all seven as its front matter above the body; authoring imports a published Change into a draft and publishes the draft back. A coordination store holds each field in the one native feature the plugin assigns it, and its body holds the Intent and the sections the Maturity adds, with no front matter and no lineage line. Persistence writes each field to its home and the body to the store body, reads each back unchanged, and reports success only then. A coordination-store limit never shapes the record.

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

`audit-change` accepts only records whose front matter carries this contract's closed key set. A record whose front matter does not carry that closed key set is outside the contract: it receives no migration, alias, inferred front matter, body-line lineage interpretation, or audit verdict, and the Auditor reports it as outside the contract.

A record whose body opens with `# Output` is outside the contract. It takes the Intent form at its next revision through `author-change`; no other workflow rewrites it.

A record that carries `## Nodes`, `## Assertion operations`, `## Decisions`, `## Mutations`, or `## Activities` is outside the final format and takes its Maturity's sections at its next revision through `author-change`, before its next execution.

## Rationale

One self-contained record preserves Change meaning across local drafting and coordination stores, and one home per field in each place leaves no second copy to drift from the first, while cumulative, independently loadable Definitions of Ready let authoring and audit judge exactly the Maturity a record declares. The Intent opens every record so that what a Change achieves and how anyone checks it are settled before refinement starts.

- authority-rationale: Authority lives in the store because any writer of the body can type an attestation line, while the store's field-change event carries an actor and a time no body writer controls. Proposed readiness is the Proposed Definition of Ready, and the audit verdict stays outside every criterion set it judges, so each Definition of Ready is decidable and a higher level inherits the preceding level's criteria, never a verdict about another level.

Excluding records without the closed front-matter key set keeps the contract closed and avoids treating inference as product truth, and authoring a record in another form anew from its proposal leaves no inferred field to disagree with the final format. The holder is keyed on the worktree the Claim names, because one account runs several sessions and a session that claims for another — one that starts the Executor's session in a worktree of its own — is not the session that later releases or closes; the worktree separates the holder from every other session of the account while letting the session started in it hold what was claimed for it. Execution derives each block's results and Verifiers from the merge composition, because an obligation the composition does not select sends an Executor through Verifier rounds no gate requires, and an omitted one lets a Change reach `Applied` short of the results its Nodes' merge compositions select. A Change's type derives from what its record and the store name, so no stored type can disagree with them, and a Parent hands its Governance mutations and Spec mutations blocks to its children, so no Change both coordinates children and carries a changeset.

## Product properties

1. A Change's record carries content only — its Intent and the sections its Maturity adds — and remains portable across coordination stores; who holds the Change, who authorized each Maturity, and where its work continues are read from the store's field-change events and Lifecycle comments under the Lifecycle rules.
2. Maturity advances only when the declared level's cumulative Definition of Ready holds and, past Proposed, Framed, and Sliced, the store shows the Product's Maintainer's move out of `Submitted` at that Maturity.
3. Lifecycle moves through one skill per transition — claim, release with a Handoff or submission, confirmation, close to a named terminal value — each an ordered write with a complete readback that never touches Maturity; persistence preserves field equality, while audit accepts only records whose front matter carries the contract's closed key set.

## Verification

- ALWAYS: a Change record contains exactly the seven required front-matter keys, and its body opens with `## Intent` carrying What, Why, and Evidence, followed by the sections its declared Maturity adds in their declared order.
- ALWAYS: Proposed, Framed, Sliced, and Executable each have one independently loadable, cumulative Definition of Ready, and no Definition of Ready requires a body authority line.
- ALWAYS: Maturity advances past Proposed, Framed, and Sliced only when the target level's Definition of Ready holds and the store shows the Product's Maintainer's move of the Change out of `Submitted` at the Maturity it leaves, read from the store's field-change event with its actor and time.
- NEVER: a Change body carries attestation, accountable-person, priority or overrule text.
- ALWAYS: the change audit counts the title's words and the Intent's words and reports a record over a limit as a non-blocking finding naming the section, the limit, and the count.
- ALWAYS: persistence writes each field to its one home in the configured coordination store and the body to the store body, and reads each back unchanged before reporting success; a coordination-store limit never shapes the record.
- NEVER: a place holds a Change field in two homes, a store body carries front matter or a lineage line, or a project field holds a Change field.
- NEVER: `audit-change` judges or migrates a record whose front matter does not carry the contract's closed key set; the Auditor reports it as outside the contract.
- ALWAYS: a record whose body opens with `# Output` is outside the contract and takes the Intent form at its next revision through `author-change`.
- ALWAYS: `claim-change` claims only an open record whose Product — the configured Product, or none for a root — Maturity, `Available` Lifecycle, and empty holder verify from current state, and reports any other Lifecycle, `Submitted` included, without mutation; it adds the holder, records the Claim naming the claiming session and the worktree root the Change is claimed for, writes `Claimed`, and reads the complete state back before execution begins, and a losing concurrent claim withdraws its own holder record and reports the winner.
- ALWAYS: `release-change` and `close-change` run only for the session whose assigned worktree root equals the root the winning Claim names, and report any other caller without mutation.
- ALWAYS: `release-change` writes a Handoff carrying branch or changeset, the completed Governance mutations and Spec mutations blocks and the next one, blockers, and hazards, then removes the holder, writes `Available` — or `Submitted` for its `submit` result — and reads the complete state back, leaving Maturity unchanged.
- ALWAYS: `confirm-change` moves only a `Submitted` Change, writing `Available` with no comment, and reads the complete state back; it reports any other Lifecycle without mutation.
- ALWAYS: `close-change` verifies the named terminal precondition from current state, writes the terminal record, removes the holder, writes the terminal Lifecycle, closes the record with the matching reason, and reads the complete terminal state back; it refuses an argument outside `Applied` and `Abandoned`, refuses `Applied` for a Leaf while the merge commit of the pull request or branch its newest Handoff names is not an ancestor of the default branch, a Node lacks a result the merge composition for its malleability after selects, an amended or new record lacks an approving decision-record audit, or the Intent's Evidence is unmet, refuses `Applied` for a Parent while a child is open or its last child closed other than `Applied`, and closes a root only on the operator's direction.
- NEVER: a Lifecycle skill writes Maturity or a body section, or posts a comment other than its Claim, Handoff, or terminal record.
- NEVER: a Lifecycle transition performs a later mutation after a required write fails or a readback differs from the intended state; its diagnostic names every completed write, the failed operation, and the observed state.
- NEVER: a Handoff, Claim, terminal record, or rejection instruction carries a secret value or credential payload.
- ALWAYS: a Change that another Change names in `parent` carries no Governance mutations or Spec mutations block and never reaches Executable; the change audit rejects a record that breaks the rule.
