# Change Record Contract

A Change is a self-contained, store-neutral coordination record for one intended Output. Its record shape, Maturity-specific Definitions of Ready, authority requirements, persistence behavior, and compatibility boundary are fixed by this decision; `audit-change` produces its Agentic verdict under `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`.

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

## Persistence

Change authoring operates on the complete local draft maintained by `spx change draft`. A persistence workflow uses `gh` to map every front-matter field to the coordination store's native features, writes the complete record without stripping its front matter, and reads the persisted representation back before reporting success. The read-back value of every field equals the local draft.

The record remains authoritative without any store-specific field, label, relationship, or rendering. Store-native metadata is a projection of the record rather than a second source of Change semantics. Persistence is an authoring-skill instruction and never a requirement that the record format embeds store commands or provider identifiers.

## Compatibility

`audit-change` accepts only records authored under this contract. A record in an earlier form receives no migration, legacy alias, inferred front matter, body-line lineage interpretation, or audit verdict.

## Rationale

One self-contained record preserves Change meaning across local drafting and coordination stores, while cumulative, independently loadable Definitions of Ready let authoring and audit judge exactly the Maturity a record declares. Excluding earlier record forms keeps the contract closed and avoids treating inference as product truth.

## Product properties

1. A Change carries its complete coordination meaning in the record and remains portable across coordination stores.
2. Maturity advances only when the declared level's cumulative Definition of Ready holds and its human or Frame-derived authority is present.
3. Persistence preserves field equality, while audit accepts only records authored under this contract.

## Verification

- ALWAYS: a Change record contains exactly the six required front-matter keys and the four fixed top-level body sections in their declared order.
- ALWAYS: Proposed, Framed, Sliced, and Executable each have one independently loadable, cumulative Definition of Ready.
- ALWAYS: Maturity advances only when the target level's Definition of Ready holds and the level's authority is present: operator attestation for Framed, a named accountable person for Sliced, and the attested Frame for Executable.
- ALWAYS: persistence maps every front-matter field through `gh`, writes the complete self-contained record, and reads each persisted field back equal before reporting success.
- NEVER: store-native metadata replaces, strips, or restates authoritative Change content.
- NEVER: `audit-change` judges or migrates a record authored outside this contract.
