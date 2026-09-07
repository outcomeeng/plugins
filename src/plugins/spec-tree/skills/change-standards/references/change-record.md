<purpose>

A Change is mutable coordination for one intended Output in one Product. Build refines the Output and produces it through Activities. Discovery owns prioritization and resource estimates. Decisions and Assertions own product and architecture truth.

</purpose>

<record_rules>

<rule id="output">

ALWAYS open the body with `# Output`: state the observable result in language a fresh holder can understand. The title names that same Output. An Output can evolve Decisions or specs, reconcile lower layers, or combine those concerns.

Place observable details under `## Behavior`. Add `### Surface: CLI`, `### Surface: Web`, or another named surface only when multiple surfaces need disambiguation. Omit redundant surface headings. State consequential exclusions and operator-approved prototype constraints where they affect Behavior.

ALWAYS retain why the Output is worth producing under `# Value`. Use `## Outcome` for the intended change for its users and `## Impact` for the broader benefit when those claims are established. A reconciliation can name the governing truth it restores; a prototype can name the question it answers. NEVER invent measurements, business benefits, or settled answers to fill the format.

</rule>

<rule id="identity-and-input">

ALWAYS identify the title, exactly one Product, Maturity, and Lifecycle. The local working file carries these as metadata above the body so the complete candidate can be inspected and audited locally. An existing Change also carries its canonical reference; its Lifecycle and holder come from the configured store's confirmed state. A new local draft grants no claim or integration authority.

Publication maps the approved metadata to the configured store's native fields and publishes the body without duplicate metadata sections. The local candidate and published record are successive versions of the same Change; the workflow checks for intervening remote edits before publishing.

At Proposed maturity, the received input remains available through the Change infrastructure; an Input section may present it. From Framed maturity onward, NEVER include an Input section, reproduced prompt, or conversation transcript in the Change body. The Change infrastructure owns preservation of the original input and edit history. NEVER manufacture a local history file or audit comment to replace that responsibility.

</rule>

<rule id="maturity">

ALWAYS judge the record at its declared maturity:

| Maturity   | Required content and authority                                                                                                                                                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Proposed   | A prioritized intended Output and why it is worth refinement; unresolved questions remain explicit.                                                                                                               |
| Framed     | Operator-attested Output; affected or intended Nodes; Assertion operations; every Decision needed to preserve product intent; target malleability for each affected node. Output-affecting questions are settled. |
| Sliced     | The Framed content describes one coherent, independently integrable unit in one repository, with dependencies and sequence resolved.                                                                              |
| Executable | Consequential Decisions are settled; the Frame states required node states and evidence obligations; ordered Activities permit execution without reopening product or architecture judgment.                      |

NEVER require implementation commits, a branch, or a changeset merely to refine or audit a Change. NEVER treat a filled template or an audit approval as operator attestation. Questions that affect the Output prevent Framed maturity; unresolved consequential architecture prevents Executable maturity.

Maturity can move backward when its requirements become false. A Claimed holder writes a Handoff and releases the Change before lowering Maturity. Advancing it again requires the same authority and content as the original advancement.

</rule>

<rule id="frame">

ALWAYS organize the Frame under `## Nodes`, `## Assertions`, and `## Decisions`.

- Nodes: identify each existing or intended node by its full product-relative path, Product and repository when ambiguous, target malleability, and required node state at Executable maturity.
- Assertions: identify the affected node and exact assertion heading or identifier; state each addition, amendment, or removal and its intended declaration. At Executable maturity, include the evidence obligations needed to produce the required node state.
- Decisions: identify each governing Decision by its exact repository reference and capture the choice that must remain settled. Mark intended Decision changes explicitly. A reference whose contents leave a consequential choice open does not settle it.

Existing references must resolve. Intended paths must be labeled as intended. A prototype exception explicitly authorized by the operator remains visible with its scope; NEVER invent specs or evidence artifacts to make an exception look like normal coverage.

NEVER treat the Change as authority to contradict a Decision or Assertion. Activities that evolve product truth name the corresponding authoring work before dependent implementation.

</rule>

<rule id="lifecycle">

Lifecycle is independent of Maturity:

| Lifecycle | Meaning                                                                                                                            |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Available | No current holder; open to refinement or execution.                                                                                |
| Claimed   | Exactly one holder owns refinement or execution.                                                                                   |
| Applied   | An Executable leaf's changeset has integrated and produced its Output under the Frame's requirements.                              |
| Refined   | More precise successor Changes continue the source's Output, and an authorized Refiner has confirmed every known successor exists. |
| Abandoned | Work ended without producing or refining the Output.                                                                               |

Applied, Refined, and Abandoned are terminal. NEVER confuse the Refined Lifecycle with reaching Framed maturity. An auditor holds no claim and changes no Lifecycle. Only the current holder has integration authority.

Execution requires an Executable, Claimed lineage leaf with no unresolved blockers and every predecessor Refined. Refinement may continue while blockers remain unresolved.

</rule>

<rule id="relationships">

ALWAYS author lineage only through the successor's immutable `refined_from` set. A root has no predecessors. Successors, roots, leaves, and reverse changeset views are derived; NEVER maintain authoritative successor or changeset lists in the Change.

Record mutable blockers by exact Change reference. A cycle prevents Sliced or Executable maturity. Follow a Refined blocker's successors: Applied leaves satisfy the dependency; active leaves remain blockers; an Abandoned leaf requires renewed refinement.

Splitting and combining Changes are outside this prototype's authoring operations. Existing lineage remains readable and must be preserved.

</rule>

<rule id="activities">

ALWAYS describe meaningful work in execution order under `# Activities`. Each Activity names the result it produces and the target needed to continue. Include exact repository coordinates and non-obvious commands only when another holder needs them. Routine command logs remain execution context.

NEVER use Activities to hide an unresolved product or architecture choice inside an Executable Change. Keep completion marks current, and distinguish completed work from remaining work without appending a session narrative.

</rule>

<rule id="verification-separation">

ALWAYS draft, revise, audit, and repair the Change in a local working file. Publish the approved candidate only after independent verification passes. NEVER publish draft iterations or rejected candidates to an issue, comment, or other remote Change store. Store configuration and publication are authoring concerns; SPX audits the local file through its file-scoped verification contract.

Evidence obligations in the Frame describe what execution must establish. Verification runs, tokens, verdicts, findings, digests, command results, and verification history remain outside the Change. NEVER add a Verification status section or a verifier-result archive to the body. Findings can cause revisions to Output, Frame, or Activities; the finding record remains in the verification system.

</rule>

<rule id="continuation">

An Executable Change and its repository references supply every settled specification needed to choose and perform the next Activity. A fresh holder must not need the original conversation, provider transcript, private scratch path, or an unavailable attachment.

The latest Handoff holds transient continuation: active branch or changeset, completed Activities, next Activity, blockers, and hazards that cannot be reconstructed quickly. Secret values never enter either record. The changeset references the Change; the Change infrastructure derives the reverse view.

ALWAYS repair missing durable intent in the Change itself. Use a Handoff for transient facts, and owning Node notes for defects with evidence, impact, and a settlement condition. NEVER use either to substitute for a complete Frame or ordered Activities.

</rule>

</record_rules>
