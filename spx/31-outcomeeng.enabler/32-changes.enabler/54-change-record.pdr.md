# Change Record Contract

A Change is a self-contained, store-neutral coordination record for one intended Output. Its record shape, Maturity-specific Definitions of Ready, authority requirements, Lifecycle transitions, persistence behavior, and compatibility boundary are fixed by this decision; `audit-change` produces its Agentic verdict under `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`.

## Record

Every Change begins with YAML front matter containing exactly these required keys:

| Key            | Contract                                                                                                                                                   |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | The intended Output, stated as a title.                                                                                                                    |
| `product`      | The one Product that owns the Change.                                                                                                                      |
| `maturity`     | Exactly one of `Proposed`, `Framed`, `Sliced`, or `Executable`.                                                                                            |
| `lifecycle`    | Exactly one of `Available`, `Claimed`, `Applied`, `Refined`, or `Abandoned`; Lifecycle changes independently of Maturity.                                  |
| `refined_from` | The immutable list of predecessor Change identities; a root carries `[]`, and a successor names every predecessor whose remaining Output it continues.     |
| `blocked_by`   | The mutable list of Change identities whose current lineage leaves must reach `Applied` before this Change is unblocked; an unblocked Change carries `[]`. |

No other front-matter key is valid. The body contains exactly these top-level sections in this order:

1. `# Output` — the decision or spec evolution, lower-layer reconciliation, or combination the Change produces.
2. `# Value` — what makes the work worth doing: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves.
3. `# Frame` — the affected or intended Nodes, Assertion operations, governing Decisions, target malleability, required node states, evidence obligations, dependencies, repository boundary, and accountable person known at the declared Maturity.
4. `# Activities` — the mutable, ordered execution plan, containing only steps another holder needs to coordinate.

Front-matter values are never stripped, restated, or maintained as authoritative body lines. Provider conversations, transcripts, cost estimates, resource accounting, and routine local commands are not record content.

## Definitions of Ready

Each Definition of Ready is independently loadable and cumulative: a level includes every requirement of the preceding level.

### Proposed

A Proposed Change is ready when:

- all six front-matter fields and all four body sections satisfy the record contract;
- `title`, `product`, `maturity`, and `lifecycle` identify one intended Output, one owning Product, `Proposed` Maturity, and a valid Lifecycle;
- `refined_from` is `[]` for a root or the complete immutable predecessor set for a successor, and `blocked_by` names every known blocker;
- `# Output` and `# Value` preserve the proposal in the proposer's terms and state why the operator conditionally prioritizes it for Build refinement; and
- the operator has reviewed the proposal.

### Framed

A Framed Change is ready when:

- the Proposed Definition of Ready holds;
- `# Frame` identifies every affected or intended Node, each Assertion operation, every Decision needed to preserve product intent, and the target malleability of each affected node;
- every question that can change the intended Output is settled; and
- the operator's attestation that the Frame captures their intent is present in the record.

### Sliced

A Sliced Change is ready when:

- the Framed Definition of Ready holds;
- the Change is one coherent, independently integrable unit in one repository;
- its dependencies and execution sequence are resolved; and
- `# Frame` names the person accountable for the slice.

### Executable

An Executable Change is ready when:

- the Sliced Definition of Ready holds;
- every consequential Decision for the changeset is settled;
- `# Frame` states the required state and evidence obligations for every affected node; and
- `# Activities` is ordered and sufficient for an agent to proceed without reopening product or architecture judgment.

Framed requires the operator's attestation. Sliced requires a named accountable person. An agent may advance Sliced to Executable only inside the authority of the attested Frame.

## Lifecycle

Lifecycle records who holds the Change or how it ended: `Available` means no holder; `Claimed` means one holder; `Applied`, `Refined`, and `Abandoned` are terminal. One skill moves each transition and moves nothing else: `claim-change` moves `Available` to `Claimed`, `release-change` moves `Claimed` to `Available`, and `close-change` moves `Claimed` to the terminal value its one argument names. None of the three writes Maturity, and none writes a body section other than the Handoff or the terminal record; Maturity moves only through `author-change`. Author, Fixer, and Verifier roles hold no claim.

A claim requires an open record whose Product is the configured Product, whose Maturity is one declared value, whose Lifecycle is `Available`, and whose holder is empty; any other state is reported without mutation. The claim adds the holder, records the Claim — the claiming agent session and its assigned worktree root — and writes `Claimed`. When two sessions claim at once, the earliest Claim after the latest Handoff wins, and the losing session withdraws its own holder record and reports the winner.

A release requires the Handoff: branch or changeset, completed and next Activities, blockers, and the hazards the next holder cannot derive quickly — never a secret and never content that belongs in the body. What the holder learned about the Output is refined into the body through `author-change` before the release. The release writes the Handoff, removes the holder, and writes `Available`; Maturity stays as it is, and any agent may claim the Change next.

A close requires its terminal precondition from current state, not from the holder's account. `Applied` requires the changeset integrated into the authoritative branch, the Assertions and evidence governing the Change's Nodes satisfied, and the Output delivered; a merged pull request alone is not `Applied`. `Refined` requires at least one successor in the store, and every known successor naming this Change in `refined_from`; a Change whose Output continues nowhere is not refined. `Abandoned` requires the operator's explicit direction and records the operator's stated reason. The close writes the terminal record, removes the holder, writes the terminal Lifecycle, and closes the record with the matching reason. A terminal Change receives no Handoff and never returns to `Available`.

Every transition is an ordered write with a complete readback: each write lands in its declared order, the transition reads Product, Maturity, Lifecycle, the holder, and the newest Claim, Handoff, or terminal record back from the store, and it completes only when every value equals the intended state. When a write fails or a readback differs, the transition stops before every later mutation and reports the completed writes in order, the failed operation, and the observed state; no later write is guessed to make a partial transition look complete.

## Persistence

Persistence maps every front-matter field to the configured coordination store's native features, writes the complete record without stripping its front matter, and reads every field back unchanged before reporting success. A coordination-store limit never shapes the record.

The record remains authoritative without any store-specific field, label, relationship, or rendering. Store-native metadata is a projection of the record rather than a second source of Change semantics. The persistence skill instruction selects the client for the configured store; the record embeds no store commands or provider identifiers.

## Compatibility

`audit-change` accepts only records whose front matter carries this contract's closed key set. A record whose front matter does not carry that closed key set is outside the contract: it receives no migration, alias, inferred front matter, body-line lineage interpretation, or audit verdict, and the auditor reports it as outside the contract.

## Rationale

One self-contained record preserves Change meaning across local drafting and coordination stores, while cumulative, independently loadable Definitions of Ready let authoring and audit judge exactly the Maturity a record declares. Excluding records without the closed front-matter key set keeps the contract closed and avoids treating inference as product truth.

## Product properties

1. A Change carries its complete coordination meaning in the record and remains portable across coordination stores.
2. Maturity advances only when the declared level's cumulative Definition of Ready holds and its human or Frame-derived authority is present.
3. Lifecycle moves through one skill per transition — claim, release with a Handoff, close to a named terminal value — each an ordered write with a complete readback that never touches Maturity; persistence preserves field equality, while audit accepts only records whose front matter carries the contract's closed key set.

## Verification

- ALWAYS: a Change record contains exactly the six required front-matter keys and the four fixed top-level body sections in their declared order.
- ALWAYS: Proposed, Framed, Sliced, and Executable each have one independently loadable, cumulative Definition of Ready.
- ALWAYS: Maturity advances only when the target level's Definition of Ready holds and the level's authority is present: operator attestation for Framed, a named accountable person for Sliced, and the attested Frame for Executable.
- ALWAYS: persistence maps every front-matter field to the configured coordination store's native features, writes the complete self-contained record, and reads each persisted field back unchanged before reporting success; a coordination-store limit never shapes the record.
- NEVER: store-native metadata replaces, strips, or restates authoritative Change content.
- NEVER: `audit-change` judges or migrates a record whose front matter does not carry the contract's closed key set; the auditor reports it as outside the contract.
- ALWAYS: `claim-change` claims only an open record whose Product, Maturity, `Available` Lifecycle, and empty holder verify from current state; it adds the holder, records the Claim, writes `Claimed`, and reads the complete state back before execution begins, and a losing concurrent claim withdraws its own holder record and reports the winner.
- ALWAYS: `release-change` writes a Handoff carrying branch or changeset, completed and next Activities, blockers, and hazards, then removes the holder, writes `Available`, and reads the complete state back, leaving Maturity unchanged.
- ALWAYS: `close-change` verifies the named terminal precondition from current state, writes the terminal record, removes the holder, writes the terminal Lifecycle, closes the record with the matching reason, and reads the complete terminal state back; it refuses an argument outside `Applied`, `Refined`, and `Abandoned`, and refuses `Refined` while no successor exists in the store or a known successor is absent from it.
- NEVER: a Lifecycle skill writes Maturity or a body section other than the Handoff or the terminal record.
- NEVER: a Lifecycle transition performs a later mutation after a required write fails or a readback differs from the intended state; its diagnostic names every completed write, the failed operation, and the observed state.
- NEVER: a Handoff, Claim, or terminal record carries a secret value or credential payload.
