<authority>

The governing methodology is the Change chapter selected by the consumer repository's `spx.config.yaml`: require `methodology.version: "4.0"`, resolve `methodology.source`, and read `versions/4.0/methodology/change/changes.md` inside that declared source. This reference operationalizes that chapter without replacing it. A Change is mutable coordination for one intended Output in one Product; it declares no product, architecture, or methodology truth.

</authority>

<record_rules>

<rule id="record-shape">

Every Change begins with YAML front matter containing exactly these required keys:

| Key            | Contract                                                                    |
| -------------- | --------------------------------------------------------------------------- |
| `title`        | Non-empty string naming the intended Output.                                |
| `product`      | Non-empty string naming exactly one owning Product.                         |
| `maturity`     | `Proposed`, `Framed`, `Sliced`, or `Executable`.                            |
| `lifecycle`    | `Available`, `Claimed`, `Applied`, `Refined`, or `Abandoned`.               |
| `refined_from` | Immutable list of canonical predecessor Change identities; `[]` for a root. |
| `blocked_by`   | Mutable list of canonical blocker Change identities; `[]` when unblocked.   |

Each required key appears exactly once. The `compatibility-boundary` rule governs a candidate whose front matter omits, repeats, or adds a key. For a candidate inside the contract, an invalid value type or value is a defect. Store coordinates, issue identities, holder data, timestamps, and verification data stay outside front matter.

The body contains exactly these top-level sections in this order:

1. `# Output`
2. `# Value`
3. `# Frame`
4. `# Activities`

Missing, reordered, duplicated, or unknown top-level sections are defects. Subsections may refine the four sections. Front-matter fields are never stripped, restated, or maintained as authoritative body lines.

</rule>

<rule id="output-and-value">

`# Output` states the decision or spec evolution, lower-layer reconciliation, or combination the Change produces. The title names the same Output. Preserve observable behavior, consequential exclusions, and operator-approved prototype constraints when they shape the Output.

`# Value` states why the operator conditionally prioritizes the Output for Build refinement using one established form: truth brought to a lower layer, operator judgment, a prototype question, or an Output and the condition it moves. Keep detail proportional to consequences. NEVER invent beneficiaries, measurements, business benefits, research, or rejected alternatives to lengthen the record.

</rule>

<rule id="received-input-boundary">

Preserve the proposal in the proposer's terms while excluding provider conversations, transcripts, prompt copies, and received conversation input from the Change record. The coordination system owns native issue history. Reusable learning belongs in the owning Product's knowledge root when separately authored.

</rule>

<rule id="lineage">

A root carries `refined_from: []`. A successor carries every predecessor whose remaining Output it continues. The successor's set is immutable after creation, contains canonical Change identities, and contains no duplicate or self reference.

The predecessor relation is the only authored lineage direction. Derive roots, leaves, successors, and reverse changeset views. NEVER restate lineage in the body or maintain an authoritative successor list. Create every known successor before an authorized Refiner marks a source `Refined`.

</rule>

<rule id="blockers">

`blocked_by` names every known Change whose current lineage leaves must reach `Applied` before this Change is unblocked. The list is mutable, contains canonical Change identities, and contains no duplicate or self reference. A blocker cycle prevents Sliced and Executable Maturity.

When a blocker becomes `Refined`, follow its successors. Applied leaves satisfy the dependency; active leaves remain blockers; an Abandoned leaf returns the dependent Change to refinement. Refinement may continue while blockers remain unresolved. Execution requires an Executable, Claimed lineage leaf with no unresolved blocker and every predecessor Refined.

</rule>

<rule id="frame">

`# Frame` carries only facts established at the declared Maturity. From Framed onward it identifies every affected or intended Node, each Assertion operation, every Decision needed to preserve product intent, and each affected node's target malleability as `spec`, `verification`, or `implementation`. Target malleability is a per-node fact; the record carries no Change-wide target. Existing references resolve; intended references are labeled as intended. The Frame carries `Intent attestation: attested by the operator on <date>.` from Framed onward.

From Sliced onward the Frame identifies one repository, resolved dependencies and sequence, and the named accountable person. At Executable it also states the required node state and evidence obligations for every affected node. An operator-approved prototype exception remains explicit with its scope. The Change never overrides a Decision or Assertion; Activities author truth changes before dependent implementation.

</rule>

<rule id="maturity-and-authority">

Maturity records refinement readiness and may move backward when its Definition of Ready becomes false. Lifecycle records ownership or termination and changes independently. Applied, Refined, and Abandoned are terminal Lifecycle values.

Advancement requires the target level's complete Definition of Ready and authority. At Proposed, `# Frame` carries `Proposal review: reviewed by the operator on <date>.` after operator review. From Framed onward, the in-Frame Intent attestation records the operator's approval of the complete Frame. Sliced additionally names the accountable person, and Executable remains inside that attested Frame. Claude may advance Sliced to Executable by resolving implementation detail inside the Frame. A reopened product or architecture judgment blocks Executable advancement.

A Claimed holder writes a Handoff and releases the Change before lowering Maturity. Author, Fixer, and Verifier roles hold no claim and gain no integration authority from editing or auditing the record.

</rule>

<rule id="activities">

`# Activities` contains the mutable ordered execution plan another holder needs to coordinate. Each Activity names the result it produces and the target needed to continue. Executable Activities are sufficient to proceed without reopening product or architecture judgment.

Routine command logs, run tokens, verdicts, findings, verification history, cost estimates, resource accounting, and session narrative stay outside the Change. A Handoff carries transient continuation: branch or changeset, completed and next Activities, blockers, and non-obvious hazards.

</rule>

<rule id="store-independence">

The complete record remains authoritative without any store-specific field, label, relationship, or rendering. Store-native metadata is a projection. Persistence writes the complete record without stripping front matter, maps every front-matter field through the configured store, and reads every persisted value back equal before reporting success.

Store commands, provider identifiers, project item identifiers, revision selectors, concurrency observations, and holder observations are workflow state outside the record.

</rule>

<rule id="compatibility-boundary">

Before interpreting the body, `audit-change` inventories the front-matter key occurrences. It accepts only a candidate that carries each of the six closed-set keys exactly once and no other key. Stripped front matter, a missing or repeated required key, and any extra key — including `change_ref` — place the candidate outside the contract.

Return `OUTSIDE_CONTRACT` with the expected and observed key inventories and no audit verdict, migration, alias, inferred front matter, or body-line lineage interpretation. Body shape never establishes compatibility. A candidate carrying the exact closed key set remains auditable when a value, top-level section, body line, or Maturity-specific requirement violates the record contract or selected Definition of Ready.

</rule>

</record_rules>
