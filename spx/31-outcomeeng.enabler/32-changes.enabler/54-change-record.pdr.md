# Change Record Contract

A Change is a self-contained, store-neutral coordination record for one intended Output. Its body carries content only and opens with an Intent; every state and every authority event is read from the coordination store. Its record shape, Maturity-specific Definitions of Ready, authority, Lifecycle transitions, persistence behavior, and compatibility boundary are fixed by this decision; `audit-change` produces its Agentic verdict under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).

## Record

Every Change begins with YAML front matter containing exactly these required keys:

| Key            | Contract                                                                                                                                                                                                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | The intended Output, stated as a title.                                                                                                                                                                                                                                           |
| `product`      | The one Product that owns the Change; a root whose work spans Products carries none.                                                                                                                                                                                              |
| `maturity`     | Exactly one of `Proposed`, `Framed`, `Sliced`, or `Executable`.                                                                                                                                                                                                                   |
| `lifecycle`    | Exactly one of `Available`, `Submitted`, `Applied`, or `Abandoned`; Lifecycle changes independently of Maturity.                                                                                                                                                                  |
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
- handoff-blocks: A Handoff names the branch with its head commit, the completed Governance mutations and Spec mutations blocks by path, and the next block, or `refinement: <Maturity> → <next level>` below Executable.

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

- frame-next: A Change the Product's Maintainer confirms at Proposed is framed next, ahead of the Product's other Proposed Changes.

The decisions `authority-move`, `field-authority`, and `rejection-lowering` of `## Lifecycle` state how the store records the move and how a rejection lowers Maturity.

## Lifecycle

- lifecycle-values: Lifecycle is exactly one of `Available`, `Submitted`, `Applied`, or `Abandoned`, and has no `Claimed` value; `Available` means the Change waits for no confirmation, `Submitted` means a finished stage waits for the Product's Maintainer, and `Applied` and `Abandoned` are terminal.
- holder-assignee: The holder is the assignee in every Lifecycle, and a Change names at most one; a submit keeps the assignee, a confirmation or a rejection returns the Change to `Available` under the same holder, and only a release removes the assignee.
- transitions: A transition is one of seven moves: claim, release, submit, confirm, reject, applied, and abandoned. `claim-change` performs claim; `release-change` performs release, and submit with its `submit` result; `confirm-change` performs confirm and reject; `close-change` performs applied and abandoned.
- transition-comment: Every transition posts exactly one comment, and that comment is one fenced YAML block and nothing else, in exactly this form:

  ```yaml
  transition: claim
  maturity: Framed
  harness: claude
  session: 1eac3860-9961-4a52-b8cf-5172095e5f04
  machine: shz@sibook
  worktree: /Users/shz/Code/outcomeeng/methodology/worktrees/director
  position: Methodology Director
  ```

  `transition` is one of `claim`, `release`, `submit`, `confirm`, `reject`, `applied`, and `abandoned`. `maturity` is the Maturity at the move, spelled as the store spells it. `harness` is the agent-harness token the coding-agents plugin owns as `AgentType`: `claude`, `codex`, or `pi`. `session` is the harness session id. `machine` is `$USER@$(hostname -s)`, such as `shz@sibook`. `worktree` is the absolute path of the worktree the session works in. `position` is optional and the only optional key. A reject adds `reason`, and a release adds `handoff`, naming the branch, its head commit, and the next block. The comment's timestamp gives the time. The block carries no Delegate line, no For line, no prose, and no other key.

- comment-reads: No skill reads a comment, except the claim exception.
- claim-exception: The claim exception reads only the YAML block of each comment whose block carries `transition: claim` and that was posted after the newest unassign event; the earliest live one wins, liveness being `spx worktree status` on this machine, and a claim whose `machine` names another machine is never voided on age. The session the winning claim names holds the Change, and a release or a close runs only for that session.
- claim-own-worktree: A session claims only for itself and the worktree it works in; an Orchestrator that starts an Executor posts no claim, and the Executor claims the Change when it starts.
- release-event: A release removes the assignee, that unassign event is the release, and no comment is read for it; the release of a `Submitted` Change also writes `Available`, and its pending confirmation lapses.
- field-authority: Authority comes from field-change events only. A Lifecycle move out of `Submitted` whose Maturity at the move equals the Maturity at the move into `Submitted` is a confirmation at that Maturity; a move out of `Submitted` that lowers Maturity one level is a rejection and grants nothing.
- proposed-no-reject: A Proposed Change takes no reject: the Maintainer confirms it, leaves it `Submitted` for "not now", or closes it `Abandoned` on the operator's direction, and `confirm-change` refuses a reject at Proposed.
- rejection-maturity: `confirm-change` performs a rejection by writing the Maturity one level lower before it writes `Available`; `author-change` writes Maturity only for a new record, to advance it under `field-authority`, or to lower it for a reframe or a reopened judgment, and no other Lifecycle skill writes Maturity.
- branch-name: A Change's branch is `change/<N>`, such as `change/586`, and the next holder finds it from the Change number; a work branch that carries another name keeps it until it merges, and every branch created for a Change takes `change/<N>`.
- handoff-branch: Every Handoff lives on the Change's branch `change/<N>` on origin, where the next holder checks out, as an empty commit whose message is the Handoff, pushed before the release; the Executor's progress Handoff after each block is such a commit. No Handoff is a comment, nothing lands as a file on the default branch, and the release comment carries its transition block only.
- transition-readback: Every transition is an ordered write whose readback reads Product, Maturity, Lifecycle, and the assignee from the store, and for a claim the winning claim under `claim-exception`; it completes only when every value equals the intended state, and it reads no other comment.
- applied-leaf: A Leaf closes Applied when its integration commit — the merge commit of the merged pull request whose head is the Change's branch, or that branch's tip where the transport opens no pull request — is an ancestor of the default branch, every Node holds every result the merge composition for its malleability after selects, every amended or new record holds an approving decision-record audit, and the Intent's Evidence is met.
- execution-start: Execution begins only on an Executable Leaf whose winning claim names the executing session, whose every predecessor is closed, and whose blockers are resolved.
- authority-move: The authority for leaving a Maturity is the Product's Maintainer's Lifecycle move of the Change out of `Submitted` to `Available` while the Change held that Maturity, the confirmation `field-authority` defines; the store's field-change event gives its actor and time, and no skill reads the confirm or reject block for it. A rejection's instruction naming what to fix is the `reason` of its reject block, and the holder, still the assignee, repairs the record and submits it again.
- rejection-lowering: A rejection at Framed or Sliced lowers Maturity one level, so the move out of `Submitted` authorizes leaving only the lowered Maturity, the one the Change held before the rejected stage. `confirm-change` posts the reject block, writes the lowered Maturity, and then writes `Available`; `author-change` writes no rejection lowering. The holder keeps the assignee through the rejection and refines the Change again with no release and no new claim. A Proposed Change takes no reject, as `proposed-no-reject` states. `change-standards`, `author-change`, and `confirm-change` state this one order.
- lifecycle-transitions: Lifecycle records whether the Change waits for the Product's Maintainer or how it ended, and the assignee records who holds it, as `lifecycle-values` and `holder-assignee` state. One skill performs each transition and moves nothing else: `claim-change` performs claim and writes no Lifecycle; `release-change` performs release, which removes the assignee and writes `Available` only for a `Submitted` Change, and submit, which writes `Submitted` and keeps the assignee; `confirm-change` performs confirm, which writes `Available`, and reject, which writes the Maturity one level lower and then `Available`, each keeping the assignee; and `close-change` performs applied and abandoned, which write the terminal value its one argument names and keep the assignee. Each transition posts exactly one transition block and no other comment, and none writes a body section. Only a reject writes Maturity; Maturity otherwise moves only through `author-change`. Author, Fixer, and Verifier roles hold no claim.
- submitted-not-ready: Lifecycle `Submitted` means the record waits for the Product's Maintainer's review and is not ready for work at the next Maturity. Its assignee stays its holder, and no session claims, refines, or executes it until the Maintainer confirms or rejects it, or until its holder releases it, which writes `Available` and lapses the pending confirmation.
- lifecycle-confirmation: A confirmation or a rejection acts for the Product's Maintainer on a `Submitted` Change only, and reports any other Lifecycle without mutation. A confirmation posts one confirm block and writes `Available` with Maturity unchanged; a rejection at Framed or Sliced posts one reject block carrying `reason`, writes the Maturity one level lower, and then writes `Available`; each keeps the assignee.

A claim requires an open record whose Product is the configured Product, or that is a root carrying no Product, whose Maturity is one declared value, whose Lifecycle is `Available`, and whose winning claim, if any, is not live; any other state, `Submitted` included, is reported without mutation.

A release requires the Handoff: branch or changeset, the completed Governance mutations and Spec mutations blocks and the next one, blockers, and the hazards the next holder cannot derive quickly — never a secret and never content that belongs in the body. What the holder learned about the Output is refined into the body through `author-change` before the release. With the `submit` result, the holder publishes the record at the Maturity it reached and the transition writes `Submitted` and keeps the assignee. Maturity stays as it is, and an `Available` Change without an assignee may be claimed by any agent session next.

A close requires its terminal precondition from current state, not from the holder's account. A Leaf's `Applied` follows the decision `applied-leaf`; a merged pull request alone is not `Applied`. A Parent that has a Parent closes `Applied` when every child has closed and its last child closed `Applied`. A root closes `Applied` when the operator judges its Intent met, and `Abandoned` when the operator drops it. `Abandoned` requires the operator's explicit direction and records the operator's stated reason in the abandoned block's context. The close posts its applied or abandoned block, writes the terminal Lifecycle, and closes the record with the matching reason. A terminal Change receives no Handoff and never returns to `Available`.

A split creates children that name the source in `parent`, and the source drops its Governance mutations and Spec mutations blocks. A merge closes the absorbed Change `Abandoned` and adds it to the survivor's `predecessors`. A reframe edits the Change in place and lowers its Maturity to `Proposed`.

When a write fails or a readback differs, the transition stops before every later mutation and reports the completed writes in order, the failed operation, and the observed state; no later write is guessed to make a partial transition look complete.

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

- persistence-authority: The GitHub store records each change of an issue field as an `IssueFieldChangedEvent` carrying its actor, its time, and the previous and new value; the event for a Lifecycle move out of `Submitted` is the store's record of authority. The transition blocks are the store's record of each transition, and the assignee and its unassign events are its record of holding; the Handoff commits on the Change's branch carry its continuation, and none of them is the Change's content.

The persistence skill instruction selects the client for the configured store; the record embeds no store commands or provider identifiers.

## Compatibility

`audit-change` accepts only records whose front matter carries this contract's closed key set. A record whose front matter does not carry that closed key set is outside the contract: it receives no migration, alias, inferred front matter, body-line lineage interpretation, or audit verdict, and the Auditor reports it as outside the contract.

A record whose body opens with `# Output` is outside the contract. It takes the Intent form at its next revision through `author-change`; no other workflow rewrites it.

A record that carries `## Nodes`, `## Assertion operations`, `## Decisions`, `## Mutations`, or `## Activities` is outside the final format and takes its Maturity's sections at its next revision through `author-change`, before its next execution.

A record the store holds at the Lifecycle `Claimed` is outside the Lifecycle values; every Change skill reports it without mutation until the Product's Maintainer writes `Available`.

## Rationale

One self-contained record preserves Change meaning across local drafting and coordination stores, and one home per field in each place leaves no second copy to drift from the first, while cumulative, independently loadable Definitions of Ready let authoring and audit judge exactly the Maturity a record declares. The Intent opens every record so that what a Change achieves and how anyone checks it are settled before refinement starts.

- authority-rationale: Authority lives in the store because any writer of the body can type an attestation line, while the store's field-change event carries an actor and a time no body writer controls. Proposed readiness is the Proposed Definition of Ready, and the audit verdict stays outside every criterion set it judges, so each Definition of Ready is decidable and a higher level inherits the preceding level's criteria, never a verdict about another level.

Excluding records without the closed front-matter key set keeps the contract closed and avoids treating inference as product truth, and authoring a record in another form anew from its proposal leaves no inferred field to disagree with the final format. The holder is the assignee in every Lifecycle, because one assignee survives submission, confirmation, and rejection and needs no second state to say who holds the Change, while the winning claim names the session and the worktree that act for it; one account runs several sessions, so the claim, not the assignee alone, separates the holding session from every other session of the account. A transition is one fenced YAML block and nothing else, because a block of fixed keys is read by one skill under the claim exception and by no other, and prose in a comment would invite a second reader. Execution derives each block's results and Verifiers from the merge composition, because an obligation the composition does not select sends an Executor through Verifier rounds no gate requires, and an omitted one lets a Change reach `Applied` short of the results its Nodes' merge compositions select. A Change's type derives from what its record and the store name, so no stored type can disagree with them, and a Parent hands its Governance mutations and Spec mutations blocks to its children, so no Change both coordinates children and carries a changeset.

## Product properties

1. A Change's record carries content only — its Intent and the sections its Maturity adds — and remains portable across coordination stores; who holds the Change, who authorized each Maturity, and where its work continues are read from the store's assignee, its field-change events, and the Handoff commits under the Lifecycle rules.
2. Maturity advances only when the declared level's cumulative Definition of Ready holds and, past Proposed, Framed, and Sliced, the store shows the Product's Maintainer's move out of `Submitted` at that Maturity.
3. Lifecycle moves through one skill per transition — claim, release with a Handoff or submission, confirmation or rejection, close to a named terminal value — each an ordered write with a complete readback that posts one transition block and never touches Maturity except a rejection's one-level lowering; persistence preserves field equality, while audit accepts only records whose front matter carries the contract's closed key set.

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
- ALWAYS: every comment that `claim-change`, `release-change`, `confirm-change`, or `close-change` posts is one fenced YAML block and nothing else, carrying exactly `transition`, `maturity`, `harness`, `session`, `machine`, and `worktree`, optionally `position`, `reason` on a reject, and `handoff` on a release.
- ALWAYS: `claim-change` claims only an open record whose Product — the configured Product, or none for a root — Maturity, and `Available` Lifecycle verify from current state and whose winning claim, if any, is not live; it adds the session's account as assignee when the assignee list is empty, posts one claim block naming its own session and the worktree it works in, reads the winning claim back under the claim exception, writes no Lifecycle, and reports any other state, `Submitted` included, without mutation.
- ALWAYS: `release-change` and `close-change` run only for the session whose claim wins under the claim exception, and report any other caller without mutation.
- ALWAYS: `release-change` pushes the Handoff as an empty commit whose message is the Handoff on the Change's branch `change/<N>`, posts one release block whose `handoff` names that branch, its head commit, and the next block, removes the assignee, writes `Available` only for a `Submitted` Change, and leaves Maturity unchanged; with its `submit` result it runs only at Proposed, Framed, or Sliced, posts one submit block, writes `Submitted`, and keeps the assignee.
- ALWAYS: `confirm-change` moves only a `Submitted` Change: a confirmation posts one confirm block and writes `Available`, and a rejection posts one reject block carrying `reason`, writes the Maturity one level lower, and then writes `Available`; each keeps the assignee, refuses a reject at Proposed, and reports any other Lifecycle without mutation.
- ALWAYS: `close-change` verifies the named terminal precondition from current state, posts its applied or abandoned block, writes the terminal Lifecycle, and closes the record with the matching reason, keeping the assignee; it refuses an argument outside `Applied` and `Abandoned`, refuses `Applied` for a Leaf while its integration commit is not an ancestor of the default branch, a Node lacks a result the merge composition for its malleability after selects, an amended or new record lacks an approving decision-record audit, or the Intent's Evidence is unmet, refuses `Applied` for a Parent while a child is open or its last child closed other than `Applied`, and closes a root only on the operator's direction.
- NEVER: a Lifecycle skill writes a body section, writes Maturity other than the rejection lowering of `confirm-change`, writes the Lifecycle value `Claimed`, posts a comment other than its one transition block, or reads a comment other than under the claim exception.
- NEVER: a Lifecycle transition performs a later mutation after a required write fails or a readback differs from the intended state; its diagnostic names every completed write, the failed operation, and the observed state.
- NEVER: a Handoff, transition block, or rejection instruction carries a secret value or credential payload.
- ALWAYS: a Change that another Change names in `parent` carries no Governance mutations or Spec mutations block and never reaches Executable; the change audit rejects a record that breaks the rule.
