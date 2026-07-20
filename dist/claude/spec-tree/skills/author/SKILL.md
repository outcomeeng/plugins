---
name: author
description: ALWAYS invoke this skill when adding, defining, or creating specs, decisions, or nodes. NEVER author spec tree artifacts without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, AskUserQuestion, Bash(spx validation markdown:*), Bash(spx spec status:*)
---

<objective>

A Spec Tree artifact — a product spec, decision record (ADR/PDR), enabler, or outcome node — placed, indexed, and authored from the `understand` foundation templates.

</objective>

<stop_triggers>

About to choose an assertion's verification type (`[test]` / `[eval]` / `[audit]`) or its assertion type (scenario / mapping / conformance / property / compliance); about to write or edit a test file; about to implement a work item -> STOP. That work belongs to `/apply`, which invokes `/verify` before the selected specialist. Write the assertion or decision-rule text without a tag or type subsection; never select which type it resolves to, and never write the test or implementation behind it. Tagging new text with a chosen type, authoring a test, or writing implementation code from inside this skill is the exact boundary breach this trigger exists to stop.

</stop_triggers>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understand` first.

Use the canonical templates and examples provided by `/understand`:

- product spec template
- ADR template
- PDR template
- enabler template
- outcome template
- filled ADR, PDR, enabler, and outcome examples

Read the appropriate template before drafting.

</quick_start>

<workflow>

<step name="intake">

**Step 1: Determine what to create**

Ask or infer from context:

| Artifact         | When to create                        | Template                                    |
| ---------------- | ------------------------------------- | ------------------------------------------- |
| **Product spec** | Bootstrapping a new tree              | `templates/product/product-name.product.md` |
| **ADR**          | Architecture decision needs recording | `templates/decisions/decision-name.adr.md`  |
| **PDR**          | Product decision needs recording      | `templates/decisions/decision-name.pdr.md`  |
| **Enabler node** | Shared infrastructure for 2+ siblings | `templates/nodes/enabler-name.md`           |
| **Outcome node** | User-facing behavior with hypothesis  | `templates/nodes/outcome-name.md`           |

If unclear which type, apply the decision table from live `/understand` `<node_model>`:

- Delivers user-facing value? → Outcome
- Exists only to serve other nodes? → Enabler
- Governs how the product is built (architecture, invisible to its users)? → ADR
- Governs what the product does (behavior its users observe)? → PDR

ADR vs PDR is decided by content only. A decision's reach — the nodes it constrains — is set by tree position and is identical for an ADR or a PDR at the same index, so "it holds tree-wide" or "it's foundational" never argues for PDR.

</step>

<step name="context">

**Step 2: Load context for placement**

Check for `<SPEC_TREE_CONTEXT>` marker. If absent or targeting a different path, invoke `/contextualize` for the parent directory where the artifact will be placed.

This loads:

- Existing siblings (to avoid duplication and determine index)
- Ancestor ADRs/PDRs (to respect constraints)
- Parent spec (to understand scope)

**Bootstrap mode**: If `spx/` doesn't exist or has no product spec, invoke `/bootstrap` first. It interviews the user and scaffolds the initial tree. Return here after bootstrapping to author individual artifacts.

</step>

<step name="placement">

**Step 3: Determine placement and index**

**For product specs:** Place at `spx/{product-name}.product.md`. No index.

**For ADRs/PDRs:** Place in the directory where the decision's scope applies. Assign the index from the decision's constraining scope:

- Lower-index decisions constrain higher-index siblings
- An ADR/PDR at index N constrains all siblings at N+1 and above
- Use the distribution formula for new items: `i_k = 10 + floor(k * 89 / (N + 1))`
- Use midpoint insertion between existing indices
- Refer to ADRs/PDRs by full path from `spx/`; never write a bare decision filename such as `15-build.adr.md`
- Place a decision record only when loaded context identifies exactly one owning directory. If multiple directories could own the concept, a node name may be stale, or the path depends on concept ownership, node renaming, node splitting, parent/child boundaries, or context-loading reach, record the placement question as intent in the target node's `PLAN.md` or `ISSUES.md`, then invoke `/decompose <node-address>` before proposing any ADR/PDR path. Pass only the target address; owning-directory selection belongs to decomposition.

**For enabler/outcome nodes:** Place as a child of the parent where the concern belongs.

- Create one node at a time only when the parent, node type, and index are already clear from loaded context
- If sibling ordering, shared enablers, vertical slices, or index placement need analysis, invoke `/decompose <parent-node-address>`
- Derive the slug from the concern name (lowercase, hyphenated)
- **When adding or restructuring 2+ sibling nodes in one pass, stop authoring child nodes and hand off structure to `/decompose`.** Record the user's decomposition intent, constraints, examples, known issues, and unresolved questions in the target node's `PLAN.md` or `ISSUES.md`, then invoke `/decompose <node-address>`. Pass only the node address; proposed children, proposed indices, and dependency order belong to the decomposition workflow.

Present the proposed placement to the user before creating files.

</step>

<step name="clarify">

**Step 4: Clarify content**

Before drafting, gather what's needed for the artifact type:

**Product spec:**

- Why does this product exist?
- What is the product hypothesis (output → outcome → impact)?
- What's included vs excluded?
- Any product-wide compliance rules?

**ADR:**

- What concern does this govern?
- What is the decision?
- What alternatives were considered?
- What trade-offs are accepted?
- What compliance rules follow from this decision?

**PDR:**

- What product behavior does this govern?
- What is the decision?
- What product properties does this establish?

**Enabler:**

- What does this enabler provide?
- Which siblings depend on it?
- What assertions specify its output?

**Outcome (gate — answer the forcing question before proceeding):**

- Apply the forcing question from live `/understand` `<outcome>`: write it as an enabler first. Why can't this be PROVIDES X SO THAT Y CAN Z? What is uncertain about which output achieves the goal?
- Only if the forcing question confirms material uncertainty, gather hypothesis content:
  - Output: what the software does (testable)
  - Outcome: measurable change in user behavior
  - Impact: business value
- What assertions specify the output?

Use `AskUserQuestion` for operator-owned gaps. Do not ask about information already provided in the conversation.

</step>

<step name="draft">

**Step 5: Draft the artifact**

Use the appropriate canonical template provided by `/understand` for the artifact shell and final target shape. Its typed assertion examples describe the post-`/verify` artifact and are not copied into an authoring draft. Draft new spec assertions directly under `## Assertions` and new decision rules directly under `## Verification`, without a type heading or tag; `/apply` invokes `/verify` and the selected specialist to materialize the final heading and tag.

**Voice rules** (from live `/understand` `<atemporal_voice>`):

- **Atemporal**: State product truth. Never narrate history ("we discovered", "currently", "after investigating").
- **Permanent**: Write as if this will be true forever. If it wouldn't, it's temporal.
- **Test**: Read any sentence aloud. If it would sound wrong after the work is done, rewrite it.

**Assertion rules** (from live `/understand` `<assertion_model>`):

- Every outcome must have at least one assertion
- Each new assertion remains untagged until `/apply` invokes `/verify`; an untagged authoring draft is the input to verification selection, not an invalid authoring result
- `/verify` selects each assertion's verification type; when it selects test, `/test` and `/test-{language}` select the assertion type and language expression. Authoring chooses neither.

**Enabler assertions**: Same rules apply. Enablers have assertions too — they specify what the infrastructure must do.

**Reference rules**:

- Every node, ADR, and PDR reference must use the full path from `spx/`.
- Never write a bare node name, bare decision filename, or numeric prefix by itself.
- Use `spx/55-example.enabler/21-parser.enabler/parser.md`, not `parser.md` or `54-parser.enabler`.

</step>

<step name="validate">

**Step 6: Validate the draft**

Before writing files, check:

- [ ] Correct artifact type for the content
- [ ] Placed in the right directory at the right index
- [ ] Nesting rules respected: outcomes CANNOT be children of enablers (see live `/understand` `<nesting_rules>`)
- [ ] For outcomes: verify the forcing question from step 4 was answered — are the assertions a bet (majority could be swapped for different ones achieving the same goal)? If not, it is an enabler (see live `/understand` `<outcome>`)
- [ ] Slug matches directory name convention (`{NN}-{slug}.{enabler|outcome}/` for nodes)
- [ ] Spec file named `{slug}.md` (no type suffix, no numeric prefix)
- [ ] Every node, ADR, and PDR reference uses a full path from `spx/`
- [ ] Atemporal voice throughout — no temporal markers
- [ ] For outcomes: three-part hypothesis present (output → outcome → impact)
- [ ] For enablers: enables statement describes what it provides
- [ ] New spec assertions sit directly under `## Assertions` without a verification tag or assertion-type heading; `/apply` invokes `/verify` to select both before evidence construction
- [ ] New ADR/PDR rules sit directly under `## Verification` in ALWAYS/NEVER form without a verification subsection or tag; `/verify` selects the subsection and tag before the selected specialist proceeds
- [ ] Authoring has not independently selected a verification type, test assertion type, evidence path, or language expression
- [ ] No content misplacement (per live `/understand` `<common_misplacements>`)

</step>

<step name="create">

**Step 7: Create files**

**For nodes (enabler/outcome):**

```text
spx/{parent-path}/{NN}-{slug}.{enabler|outcome}/
└── {slug}.md        # Spec file
```

1. Create the directory
2. Write the spec file
3. Leave `tests/` absent; the selected test specialist materializes it with the first test file.
4. If the implementation doesn't exist yet: add the node path to `spx/EXCLUDE`. The `spx` CLI skips excluded nodes when running `spx test passing`. Apply the excluded-node convention provided by `/understand`.
5. For spec-only authoring, validate the untagged declaration with `spx validation markdown` and `spx spec status --format json`; reserve `spx validation all` for changes that touch implementation code, authored tests, validation configuration, or the validation pipeline. `/apply` later invokes `/verify`, whose selected specialist owns any evidence path it adds.

**For decision records:**

```text
spx/{scope-path}/{NN}-{slug}.{adr|pdr}.md
```

Write the file directly.

**For product specs:**

```text
spx/{product-name}.product.md
```

Write the file. If `CLAUDE.md` doesn't exist, note that product guide creation remains required.

</step>

<step name="align">

**Step 8: Align downstream declarations**

When this authoring change creates or edits a product spec, ADR, PDR, or ancestor spec assertion, invoke `/align` over the changeset before summarizing. The same changeset must carry the first affected lower specs that receive the new truth. If downstream tests or implementation remain after the lower specs are aligned, record the next implementation step in the first affected node's `PLAN.md`.

If `/align` reports that a higher-level declaration has no aligned lower spec and no first-affected-node `PLAN.md`, fix the alignment before delivery. Do not leave new higher-level truth floating above the tree.

</step>

<step name="deliver">

**Step 9: Summarize and recommend next steps**

Report what was created:

- Artifact type and path
- Index and placement rationale
- Open decisions (if any were identified during drafting)

Recommend next steps based on artifact type:

| Created                      | Recommended next                                  |
| ---------------------------- | ------------------------------------------------- |
| Product spec                 | Author top-level nodes with `/author`             |
| ADR/PDR                      | Verify compliance in affected nodes with `/align` |
| Enabler                      | Author dependent outcome nodes                    |
| Outcome with many assertions | Decompose with `/decompose`                       |
| Outcome with few assertions  | Establish evidence with `/verify`                 |

</step>

</workflow>

<failure_modes>

**Failure 1: Temporal language survived into the spec**

Claude drafted an outcome spec from the user's description: "Users currently can't export data, so we need to add CSV export." The spec read: "The system currently lacks export functionality. CSV export addresses this gap." Both sentences are temporal — they narrate a problem being solved rather than stating product truth. The atemporal version: "The system exports query results as CSV files."

How to avoid: After drafting, apply the read-aloud test from live `/understand` `<atemporal_voice>` to every sentence. If it would sound wrong after the feature ships, rewrite it.

**Failure 2: Assertions placed in ADRs**

Claude wrote an ADR that included: "Given a user uploads a file larger than 10MB, the system rejects it with a 413 error." This is a scenario assertion — it belongs in a spec, not in an ADR. The authoring draft states the untagged rule directly under `## Verification`: "ALWAYS: uploaded files exceeding 10MB are rejected at the gateway"; `/apply` invokes `/verify` to select its verification subsection and tag.

How to avoid: ADRs govern with MUST/NEVER rules under `## Verification`, verified by audit, eval, or test per subsection. Given/When/Then text is a spec assertion, not a decision record.

**Failure 3: Wrong template used for node type**

Claude created an enabler node using the outcome template. The spec had a three-part hypothesis (output → outcome → impact) but the node existed only to provide shared infrastructure for two siblings. The hypothesis was forced — "We believe that providing a database schema will cause developers to write queries faster" — because the node wasn't delivering user-facing value.

How to avoid: Apply live `/understand` `<node_model>` before selecting a template. If a natural hypothesis can't be written, it's probably an enabler.

**Failure 4: Index collision with existing sibling**

Claude created a new outcome at index 32 without checking existing siblings. Another node already occupied index 32. The directory was created but overwrote the existing node's path.

How to avoid: Always invoke `/contextualize` for the parent directory before creating any node. The sibling enumeration in the context manifest reveals all occupied indices.

**Failure 5: Rewrite pattern for temporal language**

Common temporal patterns from user input and their atemporal rewrites:

- TEMPORAL: "We need to support OAuth because users can't log in with SSO."
- ATEMPORAL: "Authentication uses OAuth 2.0. Users authenticate via SSO providers."

- TEMPORAL: "The API currently returns XML but we're switching to JSON."
- ATEMPORAL: "The API returns JSON responses conforming to the schema in `spx/55-example.enabler/15-api-contract.adr.md`."

- TEMPORAL: "After investigating performance issues, we decided to add caching."
- ATEMPORAL: "Response caching reduces latency for repeated queries. Cache invalidation follows the policy in `spx/55-example.enabler/15-cache-policy.adr.md`."

**Failure 6: Junk-drawer container names**

Claude created a parent outcome named "advanced operations" that grouped prune, archive, and "future retention features." Six months later the same directory held archive, prune, dry-run, batch deletion, and a new hypothesis for session compaction — unrelated concerns glued together by a name that accepted anything.

A container name must describe what the container contains. If the name would accept arbitrary future scope ("advanced", "core", "misc", "utilities", "helpers", "operations"), it is wrong — Claude will always find a plausible reason to drop the next feature in.

How to avoid: read the proposed container name aloud and ask "what would I refuse to put in here?" If the answer is "nothing obvious," the name is junk-drawer. Rename it after the specific concern that justified creating the container (`session-retention`, not `advanced-operations`). When two concerns are independent, they get two containers — not a vague parent.

**Failure 7: Authoring preselected `### Audit` instead of leaving verification routing to `/verify`**

Claude placed PDR rules like "`install` performs an atomic write (write to temp + rename) so settings.json is never observed in a partial state ([audit])" and "Running `install` twice for the same rule is a no-op the second time ([audit])" under `### Audit`. Both rules describe behaviors a finite test can falsify, but authoring preselected audit before the verification router examined their real subjects.

How to avoid: write each new rule directly under `## Verification` without a subsection or tag. `/apply` invokes `/verify`, which classifies the real subject; `/test` selects the assertion type only after test is selected. Authoring never performs that classification itself.

**Failure 8: Over-multiplying decision records in small trees**

Claude authored four separate ADRs (binary packaging, Rust edition, shared-crate-vs-vendoring, panic-and-logging) plus two separate PDRs (rule-binding, install-tooling) for a pre-commit Rust product with five enablers/outcomes. The user pushed back: "way overcomplicated … 2. All ADRs can be just one: spx/55-example.enabler/15-build.adr.md." The four ADRs collapsed into one `spx/55-example.enabler/15-build.adr.md`, the two PDRs were absorbed into the product spec's compliance section, and the tree went from 6 decision records to 1. Index spacing was also wrong — nodes sat at 43, 65, 82, 98, 99 for a product with no commits yet.

How to avoid: before authoring a second decision record at the same directory level, ask whether it can be a section inside the first one, or a product-level compliance rule. Closely-related architectural choices (how we package, how we build, how we handle panics, how we log) are one ADR. Product-level guarantees that constrain every node are compliance rules in the product spec, not separate PDRs. Keep indices tight (under 55 in small or pre-commit trees) and let them spread only when nodes actually multiply. The spec tree's structure reflects the scope that exists, not the scope that might exist.

**Failure 9: Authoring pre-decided decomposition structure**

Claude received a broad request, drafted several child nodes with indices, and then treated `/decompose` as confirmation. The child list encoded unexamined dependencies and left no room for the decomposition workflow to build its own model from the durable node spec and coordination notes.

How to avoid: when a request needs multiple sibling nodes, capture the user's intent and constraints in the target node's `PLAN.md` or `ISSUES.md`, then invoke `/decompose <node-address>`. The decomposition workflow owns child boundaries, node types, dependency edges, and index assignment.

**Failure 10: Chose a decision path while ownership was unsettled**

Claude received a request to capture vocabulary in exactly one PDR and to find which PDR. The concept crossed plausible owners and raised node identity questions, but Claude used the ADR/PDR placement rule to propose a root-level path before invoking `/decompose`.

How to avoid: treat "which ADR/PDR?" as structural when the owning node, node name, split, parent/child boundary, or context-loading reach is unresolved. Record the placement question as intent, invoke `/decompose <node-address>` with only the target address, and let decomposition return the owning directory before authoring writes the decision.

</failure_modes>

<anti_patterns>

**Writing implementation details in specs.** Specs describe *what*, not *how*. "How" belongs in ADRs (architecture) or code. If the spec describes function signatures, data structures, or algorithms, stop — that's an ADR or code.

**Copying temporal language from user input.** Users naturally say "we need to fix X" or "currently the system does Y." Translate to atemporal: "The system does Z" or "X handles Y correctly."

**Creating outcomes without hypotheses.** Every outcome must express: output → outcome → impact. If the hypothesis can't be written, the scope may be wrong — it might be an enabler or need further clarification.

**Placing assertions in ADRs/PDRs.** Decision records govern; they don't assert. Assertions belong in specs. ADRs/PDRs carry MUST/NEVER rules under `## Verification`, verified by audit, eval, or test per subsection.

**Bare node or decision references.** Never write `32-parser.enabler`, `15-build.adr.md`, or `PDR-21` as a reference. Use the full path from `spx/` so the file can be found.

**Numbering from 1.** Indices start at 10+ and use the sparse distribution formula. Never use single-digit indices.

**Listing children in the parent spec.** A parent spec describes the node's aggregate behavior — what the whole concern does from the outside. It does NOT enumerate or reference its children. Children describe their own concerns in their own specs. A parent spec that reads "X provides A, B, and C (these are the child nodes)" is a table of contents, not a declaration. Rewrite as a single coherent statement of what the node does; let `/contextualize` walk the tree to surface children.

**Multiplying decision records before the tree justifies it.** Authoring a separate ADR for every architectural micro-choice (packaging, edition, panic handling, logging) in a pre-commit tree produces six decision records for a product with five nodes. Closely-related choices belong in one ADR with named subsections; product-level guarantees belong in the product spec's compliance section, not as independent PDRs. Keep indices packed (under 55 in small trees) until real node growth demands spreading. The tree reflects scope that exists, not scope that might.

**Preselecting a verification subsection or tag.** Write new rules directly under `## Verification` without a subsection or tag. `/apply` invokes `/verify` to choose test, evaluate, or audit from the real subject; authoring never makes that choice.

**Pre-shaping decomposition.** When a request needs multiple sibling nodes, authoring captures intent in the target node's coordination notes and delegates to `/decompose <node-address>`. Proposed child names, proposed indices, and proposed dependency chains do not belong in the handoff.

</anti_patterns>

<success_criteria>

Authoring is complete when:

- The artifact exists at its canonical path, its filename and node kind match that path, and its index preserves the loaded sibling ordering.
- The artifact contains its template-required declaration shape in atemporal voice, and every node or decision citation is a full path from `spx/`.
- New spec assertions sit directly under `## Assertions`, and new decision rules sit directly under `## Verification`; both remain untagged and untyped for `/apply` to route through `/verify`.
- A newly authored node has no empty `tests/` directory; that directory appears only when the selected test specialist writes the first test file.
- `spx validation markdown` exits zero and `spx spec status --format json` returns a valid projection for the authored tree.
- When product truth, a decision, or an ancestor assertion changes, `/align` reports no unaligned first affected lower spec; any remaining downstream work is recorded in that lower node's `PLAN.md`.

</success_criteria>
