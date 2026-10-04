<contents>

- `<authority>` — the governing Change chapter and the record's boundary
- `<record_rules>` — `record-shape`, `intent`, `received-input-boundary`, `lineage`, `blockers`, `nodes`, `assertion-operations`, `decisions`, `slice`, `activities`, `body-authority`, `maturity-and-authority`, `store-independence`, `compatibility-boundary`

</contents>

<authority>

The governing methodology is the Change chapter selected by the consumer repository's `spx.config.yaml`. An accepted `methodology.version` is exactly `4.0`, or exactly `4.0.N` with `N` one or more decimal digits representing a non-negative integer. Both accepted forms select `versions/4.0/methodology/change/changes.md` inside the declared `methodology.source`. An absent configuration, absent `methodology` block, the sentinel `installed`, another major or minor line, a non-integer patch component, an extra version component, and a prerelease suffix are invalid selections. The invalid-selection diagnostic contains the observed value — `absent` when no value exists — and the accepted forms `4.0` and `4.0.N`, where `N` is a non-negative integer. This reference operationalizes the selected chapter without replacing it. A Change is mutable coordination for one intended Output in one Product; it declares no product, architecture, or methodology truth. Its body carries content only; every state and every authority event is read from the store.

</authority>

<record_rules>

<rule id="record-shape">

Every Change begins with YAML front matter containing exactly these required keys:

| Key            | Contract                                                                    |
| -------------- | --------------------------------------------------------------------------- |
| `title`        | Non-empty string naming the intended Output.                                |
| `product`      | Non-empty string naming exactly one owning Product.                         |
| `maturity`     | `Proposed`, `Framed`, `Sliced`, or `Executable`.                            |
| `lifecycle`    | `Available`, `Claimed`, `Submitted`, `Applied`, `Refined`, or `Abandoned`.  |
| `refined_from` | Immutable list of canonical predecessor Change identities; `[]` for a root. |
| `blocked_by`   | Mutable list of canonical blocker Change identities; `[]` when unblocked.   |

Each required key appears exactly once. The `compatibility-boundary` rule governs a candidate whose front matter omits, repeats, or adds a key. For a candidate inside the contract, an invalid value type or value is a defect. Store coordinates, issue identities, holder data, timestamps, and verification data stay outside front matter.

The body opens with `## Intent`. Each Maturity adds its sections after the Intent, in this order:

| Section                   | First required at | Rule                   |
| ------------------------- | ----------------- | ---------------------- |
| `## Intent`               | Proposed          | `intent`               |
| `## Nodes`                | Framed            | `nodes`                |
| `## Assertion operations` | Framed            | `assertion-operations` |
| `## Decisions`            | Framed            | `decisions`            |
| `## Slice`                | Sliced            | `slice`                |
| `## Activities`           | Executable        | `activities`           |

A Proposed record may also carry `## Decisions` holding its open questions. Every section present stands in this order, appears once, and is a level-two heading; a missing required section, a reordered or duplicated section, and an unknown level-two section are defects. Subsections may refine a section. Front-matter values are never restated or maintained as body lines.

</rule>

<rule id="intent">

`## Intent` carries four parts, each a labeled line or paragraph:

- **What** — the Output the Change achieves: a decision or spec evolution, a lower-layer reconciliation, or both. The title names the same Output.
- **Why** — what makes the work worth doing, in one established form: truth brought to a lower layer, an operator judgment, a prototype question, or an Output and the condition it moves.
- **Observation** — optional: the observed state that gives rise to the Change. It is present only where such an observation exists.
- **Evidence** — the observable result by which anyone checks that the Output is achieved.

What, Why, and Evidence are required. Preserve observable behavior, consequential exclusions, and operator-approved prototype constraints when they shape the Output. Keep detail proportional to consequences. NEVER invent beneficiaries, measurements, business benefits, research, or rejected alternatives to lengthen the record.

When the Change derives from a raw submission, the Intent restates that submission in the proposer's terms as What, Why, Observation, and Evidence; an unclear part is recorded as an open question under `## Decisions`, never answered by invention.

</rule>

<rule id="received-input-boundary">

Preserve the proposal in the proposer's terms while excluding provider conversations, transcripts, prompt copies, cost estimates, resource accounting, routine local commands, and received conversation input from the record. The coordination store owns native issue history. Reusable learning belongs in the owning Product's knowledge root when separately authored.

</rule>

<rule id="lineage">

A root carries `refined_from: []`. A successor carries every predecessor whose remaining Output it continues. The successor's set is immutable after creation, contains canonical Change identities, and contains no duplicate or self reference.

The predecessor relation is the only authored lineage direction. Derive roots, leaves, successors, and reverse changeset views. NEVER restate lineage in the body or maintain an authoritative successor list. Create every known successor before an authorized Refiner marks a source `Refined`.

</rule>

<rule id="blockers">

`blocked_by` names every known Change whose current lineage leaves must reach `Applied` before this Change is unblocked. The list is mutable, contains canonical Change identities, and contains no duplicate or self reference. A blocker cycle prevents Sliced and Executable Maturity.

When a blocker becomes `Refined`, follow its successors. Applied leaves satisfy the dependency; active leaves remain blockers; an Abandoned leaf returns the dependent Change to refinement. Refinement may continue while blockers remain unresolved. Execution requires an Executable, Claimed lineage leaf with no unresolved blocker and every predecessor Refined.

</rule>

<rule id="nodes">

`## Nodes` is a table with one row per affected or intended Node, carrying its full `spx/...` path, its target malleability, and, from Executable, its required state. A Node's target malleability is the value the Node declares once the Change is applied: `spec`, `verification`, or `implementation`, an absent field meaning `implementation`. A row whose target malleability differs from the Node's declared malleability also names the declared value. The malleability order from most to least malleable is `spec`, `verification`, `implementation`; the least malleable target is the row value latest in that order. Target malleability is a per-Node fact; the record carries no Change-wide target. Existing paths resolve; an intended Node is labeled as intended.

</rule>

<rule id="assertion-operations">

`## Assertion operations` names each addition, amendment, or removal of an assertion or decision rule by its owning Node or decision record and its exact target. A Change never overrides a Decision or Assertion; Activities author truth changes before dependent implementation.

</rule>

<rule id="decisions">

`## Decisions` holds each question that can change the intended Output or that preserves product intent, with its answer once settled. At Proposed it holds the known open questions unanswered; from Framed every such question carries its answer, and an operator-approved prototype exception stands as an answered Decision with its scope.

</rule>

<rule id="slice">

`## Slice` names the one repository, the one vertical slice — one coherent, independently integrable unit whose dependencies and sequence are resolved — and its observable check.

</rule>

<rule id="activities">

`## Activities` contains the mutable ordered execution plan another holder needs to coordinate. Each Activity names one result on one Node and the round that produces it.

Routine command logs, run tokens, verdicts, findings, verification history, and session narrative stay outside the Change. A Handoff carries transient continuation: branch or changeset, completed and next Activities, blockers, and non-obvious hazards.

</rule>

<rule id="body-authority">

The body carries no attestation, accountable-person, priority, or overrule text. A line that records who approved, attested, prioritized, confirmed, or is accountable for the Change, or that overrides a rule, is a defect wherever it stands in the body.

</rule>

<rule id="maturity-and-authority">

Maturity records refinement readiness and may move backward when its Definition of Ready becomes false. Lifecycle records holding, submission, or termination and changes independently. Applied, Refined, and Abandoned are terminal Lifecycle values.

Maturity advances past Proposed, Framed, and Sliced only when the target level's complete Definition of Ready holds and the store shows the Product's Maintainer's move of the Change out of `Submitted` at the Maturity it leaves. At Proposed that move is the priority decision; at Framed it attests that the Change captures the operator's intent; at Sliced it confirms the slice. The Refiner advances Sliced to Executable inside the authority of the confirmed slice, with no further move, by resolving implementation detail; a reopened product or architecture judgment blocks Executable advancement.

Authority is read from the store and never from the body. The store's field-change event for the Lifecycle move out of `Submitted` gives the actor and the time; the confirmation comment posted with that move names the delegate that performed it, the operator it acts for, its agent harness, and its agent session. A move out of `Submitted` that posts a rejection comment grants no authority, and `author-change` lowers Maturity after it. The Lifecycle reference's `authority-read` rule names the store reads.

A Claimed holder writes a Handoff and releases the Change before lowering Maturity. Author, Fixer, and Verifier roles hold no claim and gain no integration authority from editing or auditing the record.

</rule>

<rule id="store-independence">

Each of the six fields has exactly one home in each place that holds the Change, and no place writes a field twice. The local draft carries all six as its front matter above the body. A coordination store holds each field in the one native feature the Lifecycle reference's `canonical-state` rule assigns it for that store, and its body holds the Intent and the sections the Maturity adds, with no front matter and no lineage line. Persistence writes each field to its home and the body to the store body, reads each back unchanged, and reports success only then; importing a published Change into a draft reads each field from its home. A coordination-store limit never shapes the record.

Store commands, provider identifiers, issue and field identifiers, revision selectors, concurrency observations, holder observations, field-change events, and Lifecycle comments are store state outside the record.

</rule>

<rule id="compatibility-boundary">

Inventory the front-matter key occurrences before interpreting the body. A candidate is inside the contract only when it carries each of the six closed-set keys exactly once and no other key, and its body does not open with `# Output`. Stripped front matter, a missing or repeated required key, and any extra key — including `change_ref` — place the candidate outside the contract, and so does a body that opens with `# Output`.

A candidate outside the contract receives no judgment, migration, alias, inferred front matter, or body-line lineage interpretation; report it as outside the contract with the expected and observed key inventories, or with the observed opening heading. A record in the `# Output` form takes the Intent form at its next revision through `author-change`; no other workflow rewrites it. A candidate inside the contract remains judgeable when a value, section, body line, or Maturity-specific requirement violates the record contract or the selected Definition of Ready.

</rule>

</record_rules>
