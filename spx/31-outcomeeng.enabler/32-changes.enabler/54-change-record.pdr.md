# Change Record Contract

A Change is a self-contained, store-neutral coordination record for one intended Output. Its body carries content only and opens with an Intent; every state and every authority event is read from the coordination store. Its record shape, Maturity-specific Definitions of Ready, authority, Lifecycle transitions, persistence behavior, and compatibility boundary are fixed by this decision; `audit-change` produces its Agentic verdict under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).

## Record

Every Change begins with YAML front matter containing exactly these required keys:

| Key            | Contract                                                                                                                                                   |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | The intended Output, stated as a title.                                                                                                                    |
| `product`      | The one Product that owns the Change.                                                                                                                      |
| `maturity`     | Exactly one of `Proposed`, `Framed`, `Sliced`, or `Executable`.                                                                                            |
| `lifecycle`    | Exactly one of `Available`, `Claimed`, `Submitted`, `Applied`, `Refined`, or `Abandoned`; Lifecycle changes independently of Maturity.                     |
| `refined_from` | The immutable list of predecessor Change identities; a root carries `[]`, and a successor names every predecessor whose remaining Output it continues.     |
| `blocked_by`   | The mutable list of Change identities whose current lineage leaves must reach `Applied` before this Change is unblocked; an unblocked Change carries `[]`. |

No other front-matter key is valid. The body opens with `## Intent`, which carries these parts:

| Part        | Content                                                                                                                                               |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| What        | The Output the Change achieves: a decision or spec evolution, a lower-layer reconciliation, or both.                                                  |
| Why         | What makes the work worth doing: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves. |
| Observation | Optional: the observed state that gives rise to the Change.                                                                                           |
| Evidence    | The observable result by which anyone checks that the Output is achieved.                                                                             |

Each Maturity adds its sections after the Intent, in this order:

| Maturity   | Section                   | Content                                                                                                                                                                                                                                                                                                                       |
| ---------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Framed     | `## Nodes`                | A table with one row per affected or intended Node: its full path, its target malleability — the value the Node declares once the Change is applied, an absent field meaning `implementation` — and its required state; a row whose target malleability differs from the declared malleability also names the declared value. |
| Framed     | `## Assertion operations` | Each operation on an assertion or decision rule, by owning Node or decision record and exact target.                                                                                                                                                                                                                          |
| Framed     | `## Decisions`            | Each question that preserves product intent, with its answer.                                                                                                                                                                                                                                                                 |
| Sliced     | `## Slice`                | The one repository, the vertical slice, and its observable check.                                                                                                                                                                                                                                                             |
| Executable | `## Activities`           | The mutable, ordered execution plan, containing only steps another holder needs to coordinate.                                                                                                                                                                                                                                |

A Proposed record may carry `## Decisions` holding its open questions unanswered.

The body carries no attestation, accountable-person, priority, or overrule text; the authority for each Maturity is read from the store, as Authority states. Front-matter values are never restated or maintained as body lines; each place that holds a Change keeps each field in its one home, as Persistence states. Provider conversations, transcripts, cost estimates, resource accounting, and routine local commands are not record content.

## Definitions of Ready

Each Definition of Ready is an independently loadable criterion set, and the sets are cumulative: a level's Definition of Ready includes every criterion of the preceding level's. No criterion is an audit verdict, and no criterion requires a body authority line.

### Proposed

The Proposed Definition of Ready is:

- all six front-matter fields satisfy the record contract, and the body opens with `## Intent`;
- `title`, `product`, `maturity`, and `lifecycle` identify one intended Output, one owning Product, `Proposed` Maturity, and a valid Lifecycle;
- `refined_from` is `[]` for a root or the complete immutable predecessor set for a successor, and `blocked_by` names every known blocker;
- the Intent states What, Why, and Evidence, with Observation present only where an observation gives rise to the Change; and
- every known question that can change the intended Output stands unanswered under `## Decisions`.

A Proposed Change is ready when the record's audit against the Proposed Definition of Ready approves it; readiness at Proposed requires no operator review statement in the record.

### Framed

A Framed Change is ready when:

- the Proposed Definition of Ready holds;
- `## Nodes` names every affected or intended Node with its target malleability;
- `## Assertion operations` names every Assertion operation by its owning Node or decision record and its exact target; and
- `## Decisions` answers every question that can change the intended Output.

### Sliced

A Sliced Change is ready when:

- the Framed Definition of Ready holds; and
- `## Slice` names one vertical slice in one repository — one coherent, independently integrable unit whose dependencies and sequence are resolved — with an observable check.

### Executable

An Executable Change is ready when:

- the Sliced Definition of Ready holds;
- `## Decisions` answers every consequential Decision for the changeset;
- `## Nodes` states each Node's required state;
- `## Activities` is ordered, each Activity names one result on one Node and the round that produces it, and the sequence suffices for the Executor to proceed without reopening product or architecture judgment; and
- the results the Activities name are the evidence obligations the merge composition selects for the changeset: every predicate `VERIFICATION_READINESS` reads that the composition selects, from the least malleable target and from the changeset's files alike, the results each Node's tagged assertions need with the producer of each, and the decision-record audit each added or changed decision record receives; the Activities name no Verifier outside those three.

The merge composition is the one the `Merge` section of the 4.0 Projection chapter states — `versions/4.0/methodology/product-tree/verification/projection.md` inside the declared `methodology.source` — which defines when a changeset touches a node, the predicates a changeset selects by its least malleable touched node and by a product spec or outcome-record change, when a result is produced again before merge, the dependency protection that fails a changeset raising a malleability or ending `Passing` in the closure of an effectively `Passing` consumer, and the decision-record audit as an authoring check that produces no node-local result.

## Authority

Maturity advances past Proposed, Framed, and Sliced only when the store shows the Product's Maintainer's move of the Change out of `Submitted` at that Maturity. At Proposed that move is the priority decision; at Framed it attests that the Change captures the operator's intent; at Sliced it confirms the slice. The Refiner advances Sliced to Executable inside the authority of the confirmed slice, with no further move.

The authority is read from the store and never from the body. The store's field-change event for the Lifecycle move out of `Submitted` gives the actor and the time. The confirmation comment `confirm-change` posts names the delegate that performed the move, the operator it acts for, its agent harness, and its agent session, which an account the delegate shares with the operator cannot show. A move out of `Submitted` that posts a rejection comment grants no authority.

## Lifecycle

Lifecycle records who holds the Change, whether it waits for the Product's Maintainer, or how it ended: `Available` means no holder; `Claimed` means one holder; `Submitted` means a published stage waits for the Product's Maintainer, with no holder; `Applied`, `Refined`, and `Abandoned` are terminal. One skill moves each transition and moves nothing else: `claim-change` moves `Available` to `Claimed`; `release-change` moves `Claimed` to `Available`, or to `Submitted` for its `submit` result; `confirm-change` moves `Submitted` to `Available`; and `close-change` moves `Claimed` to the terminal value its one argument names. None of the four writes Maturity or a body section; each posts only its own comment — the Claim, the Handoff, the confirmation or rejection comment, or the terminal record. Maturity moves only through `author-change`, which lowers it after a rejection. Author, Fixer, and Verifier roles hold no claim.

A claim requires an open record whose Product is the configured Product, whose Maturity is one declared value, whose Lifecycle is `Available`, and whose holder is empty; any other state, `Submitted` included, is reported without mutation. The claim adds the holder, records the Claim — the claiming agent session and the worktree root the Change is claimed for, which is the session's own assigned root or a root it names — and writes `Claimed`. When two sessions claim at once, the earliest Claim after the latest Handoff wins, and the losing session withdraws its own holder record and reports the winner. The Change's holder is the session whose assigned worktree root equals the root the winning Claim names; a release or a close runs only for that session.

A release requires the Handoff: branch or changeset, completed and next Activities, blockers, and the hazards the next holder cannot derive quickly — never a secret and never content that belongs in the body. What the holder learned about the Output is refined into the body through `author-change` before the release. The release writes the Handoff, removes the holder, and writes `Available`; with the `submit` result, the holder publishes the record at the Maturity it reached and the release writes `Submitted` in place of `Available`. Maturity stays as it is, and an `Available` Change may be claimed by any agent session next.

A confirmation acts for the Product's Maintainer on a `Submitted` Change only, and reports any other Lifecycle without mutation. It posts one comment and writes `Available`. The comment records the confirmation, or the rejection with its reason, and names the delegate, the operator it acts for, its agent harness, and its agent session.

A close requires its terminal precondition from current state, not from the holder's account. `Applied` requires the changeset integrated into the default branch through its merge gates and every Node in `## Nodes` at the required state its row names; a merged pull request alone is not `Applied`. `Refined` requires at least one successor in the store, and every known successor naming this Change in `refined_from`; a Change whose Output continues nowhere is not refined. `Abandoned` requires the operator's explicit direction and records the operator's stated reason. The close writes the terminal record, removes the holder, writes the terminal Lifecycle, and closes the record with the matching reason. A terminal Change receives no Handoff and never returns to `Available`.

Every transition is an ordered write with a complete readback: each write lands in its declared order, the transition reads Product, Maturity, Lifecycle, the holder, and the newest Claim, Handoff, confirmation or rejection comment, or terminal record back from the store, and it completes only when every value equals the intended state. When a write fails or a readback differs, the transition stops before every later mutation and reports the completed writes in order, the failed operation, and the observed state; no later write is guessed to make a partial transition look complete.

## Persistence

Each of the six fields has exactly one home in each place that holds the Change, and no place writes a field twice. A local draft carries all six as its front matter above the body; authoring imports a published Change into a draft and publishes the draft back. A coordination store holds each field in the one native feature the plugin assigns it, and its body holds the Intent and the sections the Maturity adds, with no front matter and no lineage line. Persistence writes each field to its home and the body to the store body, reads each back unchanged, and reports success only then. A coordination-store limit never shapes the record.

In the GitHub store the homes are:

| Field          | Home                                                                                                                                                                  |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | The issue title                                                                                                                                                       |
| `product`      | The organization issue field `Product`                                                                                                                                |
| `maturity`     | The organization issue field `Maturity`                                                                                                                               |
| `lifecycle`    | The organization issue field `Lifecycle`                                                                                                                              |
| `refined_from` | The organization text issue field `Predecessors`: the canonical identities, such as `outcomeeng/changes#17`, separated by a comma and one space, and empty for a root |
| `blocked_by`   | GitHub's native issue dependencies                                                                                                                                    |

No project field holds a Change field. The GitHub store records each change of an issue field as an `IssueFieldChangedEvent` carrying its actor, its time, and the previous and new value; the event for a Lifecycle move out of `Submitted`, with the confirmation comment, is the store's record of authority. The Lifecycle comments — the Claim, the Handoff, the confirmation or rejection comment, and the terminal record — are the store's record of holding, confirmation, and continuation, not of the Change's content. The persistence skill instruction selects the client for the configured store; the record embeds no store commands or provider identifiers.

## Compatibility

`audit-change` accepts only records whose front matter carries this contract's closed key set. A record whose front matter does not carry that closed key set is outside the contract: it receives no migration, alias, inferred front matter, body-line lineage interpretation, or audit verdict, and the Auditor reports it as outside the contract.

A record whose body opens with `# Output` is outside the contract. It takes the Intent form at its next revision through `author-change`; no other workflow rewrites it.

## Rationale

One self-contained record preserves Change meaning across local drafting and coordination stores, and one home per field in each place leaves no second copy to drift from the first, while cumulative, independently loadable Definitions of Ready let authoring and audit judge exactly the Maturity a record declares. The Intent opens every record so that what a Change achieves and how anyone checks it are settled before refinement starts. Authority lives in the store because any writer of the body can type an attestation line, while the store's field-change event carries an actor and a time no body writer controls; every session acts through one account, so the confirmation comment names the delegate and the operator it acts for, which the event's actor cannot. Proposed readiness is the approving audit rather than an operator review, and the audit verdict stays outside every criterion set it judges, so each Definition of Ready is decidable and a higher level inherits the preceding level's criteria, never a verdict about another level. Excluding records without the closed front-matter key set keeps the contract closed and avoids treating inference as product truth, and converting a record in the Output form at its next revision avoids a mass rewrite of published records. The holder is keyed on the worktree the Claim names, because one account runs several sessions and a session that claims for another — one that starts the Executor's session in a worktree of its own — is not the session that later releases or closes; the worktree separates the holder from every other session of the account while letting the session started in it hold what was claimed for it. Executable Activities derive their evidence obligations from the merge composition, because an obligation the composition does not select sends an Executor through Verifier rounds no gate requires, and an omitted one lets a Change reach `Applied` short of the state its Nodes require.

## Product properties

1. A Change's record carries content only — its Intent and the sections its Maturity adds — and remains portable across coordination stores; who holds the Change, who authorized each Maturity, and where its work continues are read from the store's field-change events and Lifecycle comments under the Lifecycle rules.
2. Maturity advances only when the declared level's cumulative Definition of Ready holds and, past Proposed, Framed, and Sliced, the store shows the Product's Maintainer's move out of `Submitted` at that Maturity.
3. Lifecycle moves through one skill per transition — claim, release with a Handoff or submission, confirmation or rejection, close to a named terminal value — each an ordered write with a complete readback that never touches Maturity; persistence preserves field equality, while audit accepts only records whose front matter carries the contract's closed key set.

## Verification

- ALWAYS: a Change record contains exactly the six required front-matter keys, and its body opens with `## Intent` carrying What, Why, and Evidence, followed by the sections its declared Maturity adds in their declared order.
- ALWAYS: Proposed, Framed, Sliced, and Executable each have one independently loadable, cumulative Definition of Ready, and no Definition of Ready requires a body authority line.
- ALWAYS: Maturity advances past Proposed, Framed, and Sliced only when the target level's Definition of Ready holds and the store shows the Product's Maintainer's move of the Change out of `Submitted` at the Maturity it leaves, read from the store's field-change event with its actor and time and from the confirmation comment naming the delegate, the operator it acts for, its agent harness, and its agent session.
- NEVER: a Change body carries attestation, accountable-person, priority or overrule text.
- ALWAYS: `confirm-change` records the Product's Maintainer's move out of `Submitted` with a comment naming the delegate, the operator it acts for, the harness and the session.
- ALWAYS: an Executable `## Activities` names the predicates `VERIFICATION_READINESS` reads, the results with their producers, and the decision-record audits that the merge composition selects for the changeset, and names no Verifier outside them; `audit-change` rejects an Executable record whose named obligations disagree with that composition.
- ALWAYS: persistence writes each field to its one home in the configured coordination store and the body to the store body, and reads each back unchanged before reporting success; a coordination-store limit never shapes the record.
- NEVER: a place holds a Change field in two homes, a store body carries front matter or a lineage line, or a project field holds a Change field.
- NEVER: `audit-change` judges or migrates a record whose front matter does not carry the contract's closed key set; the Auditor reports it as outside the contract.
- ALWAYS: a record whose body opens with `# Output` is outside the contract and takes the Intent form at its next revision through `author-change`.
- ALWAYS: `claim-change` claims only an open record whose Product, Maturity, `Available` Lifecycle, and empty holder verify from current state, and reports any other Lifecycle, `Submitted` included, without mutation; it adds the holder, records the Claim naming the claiming session and the worktree root the Change is claimed for, writes `Claimed`, and reads the complete state back before execution begins, and a losing concurrent claim withdraws its own holder record and reports the winner.
- ALWAYS: `release-change` and `close-change` run only for the session whose assigned worktree root equals the root the winning Claim names, and report any other caller without mutation.
- ALWAYS: `release-change` writes a Handoff carrying branch or changeset, completed and next Activities, blockers, and hazards, then removes the holder, writes `Available` — or `Submitted` for its `submit` result — and reads the complete state back, leaving Maturity unchanged.
- ALWAYS: `confirm-change` moves only a `Submitted` Change, writing `Available` after posting exactly one comment that records the confirmation, or the rejection with its reason, and reads the complete state back; it reports any other Lifecycle without mutation.
- ALWAYS: `close-change` verifies the named terminal precondition from current state, writes the terminal record, removes the holder, writes the terminal Lifecycle, closes the record with the matching reason, and reads the complete terminal state back; it refuses an argument outside `Applied`, `Refined`, and `Abandoned`, and refuses `Refined` while no successor exists in the store, a known successor is absent from it, or a successor does not name this Change in `refined_from`.
- NEVER: a Lifecycle skill writes Maturity or a body section, or posts a comment other than its Claim, Handoff, confirmation or rejection comment, or terminal record.
- NEVER: a Lifecycle transition performs a later mutation after a required write fails or a readback differs from the intended state; its diagnostic names every completed write, the failed operation, and the observed state.
- NEVER: a Handoff, Claim, confirmation or rejection comment, or terminal record carries a secret value or credential payload.
