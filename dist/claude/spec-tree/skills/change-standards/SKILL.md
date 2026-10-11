---
name: change-standards
user-invocable: false
description: >-
  Change record standards for Intent, maturity, lifecycle, authority,
  refinement, and continuation. Loaded by other skills, not invoked directly.
argument-hint: "<Proposed|Framed|Sliced|Executable|Lifecycle>"
arguments: selection
allowed-tools: Read
---

<objective>
The complete Change record contract, accompanied by exactly one selected reference: the cumulative Definition of Ready for one Maturity, or the Lifecycle transition rules for the declared store.
</objective>

<loading_contract>

Require `$selection` to equal `Proposed`, `Framed`, `Sliced`, `Executable`, or `Lifecycle` exactly. A missing or unsupported value is a blocked standards load and names the accepted values.

Apply `<authority>` and `<record_rules>` below for every selection. Then read exactly one selected reference:

| `$selection` | Reference                                          |
| ------------ | -------------------------------------------------- |
| `Proposed`   | `${CLAUDE_SKILL_DIR}/references/dor-proposed.md`   |
| `Framed`     | `${CLAUDE_SKILL_DIR}/references/dor-framed.md`     |
| `Sliced`     | `${CLAUDE_SKILL_DIR}/references/dor-sliced.md`     |
| `Executable` | `${CLAUDE_SKILL_DIR}/references/dor-executable.md` |
| `Lifecycle`  | `${CLAUDE_SKILL_DIR}/references/lifecycle.md`      |

NEVER load another Maturity's Definition of Ready in the same invocation. Each Definition of Ready is cumulative and complete for its level.

`<record_rules>` states the record rules, and each Definition of Ready states criteria that judge a record against those rules by identifier, and the Executable Definition of Ready also against its own `<merge_composition>`; neither carries a store command. `lifecycle.md` carries the store-binding, canonical-state, authority-read, ordered-write, complete-readback, write-inspection, inert-stdin, claim-record, handoff-record, confirmation-record, and terminal-record rules, together with the store commands those rules name; it alone assigns each field's home in the declared store and names the store reads — fields, lineage, blockers, and authority. A criterion whose evidence is store state, such as the blocker graph of `*-relationships`, is judged from those reads, which a separate `Lifecycle` load supplies; a Maturity selection never infers that state from the record alone.

</loading_contract>

<authority>

The governing methodology is the Change chapter selected by the consumer repository's `spx.config.yaml`. An accepted `methodology.version` is exactly `4.0`, or exactly `4.0.N` with `N` one or more decimal digits representing a non-negative integer. Both accepted forms select `versions/4.0/methodology/change/changes.md` inside the declared `methodology.source`. An absent configuration, absent `methodology` block, the sentinel `installed`, another major or minor line, a non-integer patch component, an extra version component, and a prerelease suffix are invalid selections. The invalid-selection diagnostic contains the observed value — `absent` when no value exists — and the accepted forms `4.0` and `4.0.N`, where `N` is a non-negative integer. These standards operationalize the selected chapter without replacing it. A Change is mutable coordination for one intended Output in one Product, or in a root that spans Products; it declares no product, architecture, or methodology truth. Its body carries content only; every state and every authority event is read from the store.

</authority>

<record_rules>

<rule id="record-shape">

Every Change begins with YAML front matter containing exactly these required keys:

| Key            | Contract                                                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`        | Non-empty string naming the intended Output.                                                                                                                                          |
| `product`      | Non-empty string naming the one Product that owns the Change; a root whose work spans Products carries none, and every child of a Parent that carries a Product carries that Product. |
| `maturity`     | `Proposed`, `Framed`, `Sliced`, or `Executable`.                                                                                                                                      |
| `lifecycle`    | `Available`, `Claimed`, `Submitted`, `Applied`, or `Abandoned`.                                                                                                                       |
| `refined_from` | Append-only list of canonical identities of the Changes this Change absorbed by a merge; `[]` for a Change that absorbed none.                                                        |
| `blocked_by`   | Mutable list of canonical blocker Change identities; `[]` when unblocked.                                                                                                             |
| `parent`       | The canonical identity of the Parent Change in the same store; `null` for a Change with no Parent.                                                                                    |

Each required key appears exactly once. The `compatibility-boundary` rule governs a candidate whose front matter omits, repeats, or adds a key. For a candidate inside the contract, an invalid value type or value is a defect. Store coordinates, issue identities, holder data, timestamps, and verification data stay outside front matter.

The body opens with `## Intent`. Each Maturity adds its sections after the Intent, in this order:

| Section                   | First required at | Rule                   |
| ------------------------- | ----------------- | ---------------------- |
| `## Intent`               | Proposed          | `intent`               |
| `## Nodes`                | Framed            | `nodes`                |
| `## Assertion operations` | Framed            | `assertion-operations` |
| `## Decisions`            | Framed            | `decisions`            |
| `## Mutations`            | Sliced            | `mutations`            |
| `## Artifacts`            | Executable        | `artifacts`            |

A known section may stand before the Maturity that first requires it — `## Decisions` holding a Proposed record's open questions, or the sections a higher Maturity added before the Change's Maturity was lowered — and the declared Maturity's Definition of Ready judges such a section only where one of its criteria names it. Every section present stands in this order, appears once, and is a level-two heading; a missing required section, a reordered or duplicated section, and an unknown level-two section are defects. Subsections may refine a section. Front-matter values are never restated or maintained as body lines.

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

<rule id="record-limits">

The title has at most 15 words, each Intent part one to three sentences, `## Decisions` at most 12 rows, and each answer at most two sentences. A record over a limit is a defect that names the section, the limit, and the count.

</rule>

<rule id="change-type">

A Change that names Nodes in `## Nodes` is a Leaf, a Change that another Change names in `parent` is a Parent, and a Change with neither a Parent nor Nodes is a root. A Change never names Nodes while it has a child. The type derives from what the record and the store name and is never stored. A Parent carries neither `## Nodes` nor `## Assertion operations` and never reaches Executable.

</rule>

<rule id="received-input-boundary">

Preserve the proposal in the proposer's terms while excluding provider conversations, transcripts, prompt copies, cost estimates, resource accounting, routine local commands, and received conversation input from the record. The coordination store owns native issue history. Reusable learning belongs in the owning Product's knowledge root when separately authored.

</rule>

<rule id="lineage">

`refined_from` is `[]` or the complete append-only set of Changes this Change absorbed by a merge; it contains canonical Change identities and no duplicate or self reference. `parent` is `null` or the canonical identity of the one Parent Change in the same store, and is no self reference.

The `refined_from` set and the `parent` value are the only authored lineage directions. Derive roots, Leaves, Parents, children, and reverse changeset views. NEVER restate lineage in the body or maintain an authoritative child list. A split creates every child naming the source in `parent`, and the source drops its `## Nodes` and `## Assertion operations`. A merge closes the absorbed Change `Abandoned` and adds it to the survivor's `refined_from`. A reframe edits the Change in place and lowers its Maturity to `Proposed`. No skill writes or accepts `Refined`.

</rule>

<rule id="blockers">

`blocked_by` names every known Change that must close `Applied`, or resolve through the Change that absorbed it, before this Change is unblocked. The list is mutable, contains canonical Change identities, and contains no duplicate or self reference. A blocker cycle prevents Sliced and Executable Maturity.

A blocker closed `Applied` satisfies the dependency; an open blocker remains a blocker; a blocker closed `Abandoned` that another Change absorbed resolves through the Change that absorbed it, which satisfies the dependency once it closes `Applied`; a blocker closed `Abandoned` that no Change absorbed returns the dependent Change to refinement. Refinement may continue while blockers remain unresolved. Execution requires a Claimed, Executable Leaf whose every predecessor is closed and whose blockers are resolved.

</rule>

<rule id="nodes">

`## Nodes` is a table with one row per affected or intended Node, carrying its full `spx/...` path, its Malleability before, its Malleability after, and, from Executable, its Required state. Malleability before is the value the Node declares before the Change, empty for a Node the Change creates. Malleability after is the value the Node declares once the Change is applied: `spec`, `verification`, or `implementation`, an absent field meaning `implementation`. The malleability order from most to least malleable is `spec`, `verification`, `implementation`; the least malleable target is the Malleability after value latest in that order. Malleability is a per-Node fact; the record carries no Change-wide target. Existing paths resolve; an intended Node is labeled as intended.

</rule>

<rule id="assertion-operations">

`## Assertion operations` names each addition, amendment, or removal of an assertion or decision rule by its owning Node or decision record and its exact target. A Change never overrides a Decision or Assertion; `## Mutations` rows author truth changes before dependent implementation.

</rule>

<rule id="decisions">

`## Decisions` holds each question that can change the intended Output or that preserves product intent, with its answer once settled. At Proposed it holds the known open questions unanswered; from Framed every such question carries its answer, and an operator-approved prototype exception stands as an answered Decision with its scope.

</rule>

<rule id="mutations">

`## Mutations` is a table with one row per Node, in execution order, carrying the transition the Node undergoes — add, modify, or implement. It names the one repository and the one observable check of the slice: one coherent, independently integrable unit whose dependencies and sequence are resolved. From Executable, each row also names the results the merge composition selects for its Node with the producer of each, and the row of a Node that owns an added or changed decision record names that record's audit.

</rule>

<rule id="artifacts">

`## Artifacts` links the audited content of every Node the Change adds, modifies, or implements. Each link is held where it resolves in every execution environment.

Routine command logs, run tokens, verdicts, findings, verification history, and session narrative stay outside the Change. A Handoff carries transient continuation: branch or changeset, the completed Mutation rows and the next one, blockers, and non-obvious hazards.

</rule>

<rule id="body-authority">

The body carries no attestation, accountable-person, priority, or overrule text. A line that records who approved, attested, prioritized, confirmed, or is accountable for the Change, or that overrides a rule, is a defect wherever it stands in the body.

</rule>

<rule id="maturity-and-authority">

Maturity records refinement readiness and may move backward when its Definition of Ready becomes false. Lifecycle records holding, submission, or termination and changes independently. Applied and Abandoned are terminal Lifecycle values.

Maturity advances past Proposed, Framed, and Sliced only when the target level's complete Definition of Ready holds and the store shows the Product's Maintainer's move of the Change out of `Submitted` at the Maturity it leaves. At Proposed that move is the priority decision; at Framed it attests that the Change captures the operator's intent; at Sliced it confirms the slice. The Refiner advances Sliced to Executable inside the authority of the confirmed slice, with no further move, by resolving implementation detail; a reopened product or architecture judgment blocks Executable advancement.

Authority is read from the store and never from the body. The store's field-change event for the Lifecycle move out of `Submitted` gives the actor and the time; the confirmation comment posted before that move names the delegate that performed it, the operator it acts for, its agent harness, and its agent session.

A Change is submitted only at Proposed, Framed, or Sliced; an Executable Change is never submitted, because no authority follows Executable. The move out of `Submitted` changes Lifecycle only and writes no Maturity, whether its comment confirms or rejects. A rejection grants no authority. After a rejection at Framed or Sliced, the Change's next Maturity write lowers it to Proposed or Framed respectively, before any further refinement; after a rejection at Proposed, the Change stays Proposed without the priority decision.

A Claimed holder writes a Handoff and releases the Change before lowering Maturity. Author, Fixer, and Verifier roles hold no claim and gain no integration authority from editing or auditing the record.

</rule>

<rule id="store-independence">

Each of the seven fields has exactly one home in each place that holds the Change, and no place writes a field twice. The local draft carries all seven as its front matter above the body. A coordination store holds each field in one native feature assigned to that field for that store, and its body holds the Intent and the sections the Maturity adds, with no front matter and no lineage line. Persistence writes each field to its home and the body to the store body, reads each back unchanged, and reports success only then; importing a published Change into a draft reads each field from its home. A coordination-store limit never shapes the record.

Store commands, provider identifiers, issue and field identifiers, revision selectors, concurrency observations, holder observations, field-change events, and Lifecycle comments are store state outside the record.

</rule>

<rule id="compatibility-boundary">

Inventory the front-matter key occurrences before interpreting the body. A candidate is inside the contract only when it carries each of the seven closed-set keys exactly once and no other key, and its body does not open with `# Output`. Stripped front matter, a missing or repeated required key, and any extra key — including `change_ref` — place the candidate outside the contract, and so does a body that opens with `# Output`.

A candidate outside the contract receives no judgment, migration, alias, inferred front matter, or body-line lineage interpretation; report it as outside the contract with the expected and observed key inventories, or with the observed opening heading. A record in the `# Output` form is never converted in place: its next revision authors the record anew in the Intent form from the proposal it carries, and only that newly authored record is judged against the contract. No revision preserves the `# Output` form. A candidate inside the contract remains judgeable when a value, section, body line, or Maturity-specific requirement violates the record contract or the selected Definition of Ready. A record that carries `## Slice` or `## Activities` takes its Maturity's sections at its next revision, before its next execution.

</rule>

</record_rules>

<success_criteria>

- Each record rule is stated once, in `<record_rules>`; a Definition of Ready criterion cites the record rule or, at Executable, the `<merge_composition>` it applies, and adds only the level's own condition.
- Every loaded criterion has a stable identifier and can be judged from the complete record, the store state the `Lifecycle` reads return, and necessary repository references.
- The authority for each Maturity advance is read from the store's field-change events and confirmation comments under `authority-read`, and no rule or criterion requires body authority text.
- The four Maturity values, the five Lifecycle values, lineage, the Leaf, Parent, and root types, blockers, authority, product truth, and continuation remain distinct.

</success_criteria>
