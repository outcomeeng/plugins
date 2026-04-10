---
name: authoring
description: >-
  ALWAYS invoke this skill when adding, defining, or creating specs, decisions, or nodes.
  NEVER author spec tree artifacts without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit
---

<objective>

Author Spec Tree artifacts — product specs, decision records (ADR/PDR), enabler nodes, and outcome nodes — using templates from the `understanding` foundation skill. Guides placement, index assignment, and content quality.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understanding` first.

Templates and examples live in the understanding skill's directory (`${CLAUDE_SKILL_DIR}/../understanding/`):

- `${CLAUDE_SKILL_DIR}/../understanding/templates/product/product-name.product.md`
- `${CLAUDE_SKILL_DIR}/../understanding/templates/decisions/decision-name.adr.md`
- `${CLAUDE_SKILL_DIR}/../understanding/templates/decisions/decision-name.pdr.md`
- `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/enabler-name.md`
- `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/outcome-name.md`
- `${CLAUDE_SKILL_DIR}/../understanding/examples/` — filled specs for reference

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

If unclear which type, apply the decision table from `${CLAUDE_SKILL_DIR}/../understanding/references/node-types.md`:

- Delivers user-facing value? → Outcome
- Exists only to serve other nodes? → Enabler
- Governs how things are built? → ADR
- Governs what the product does? → PDR

</step>

<step name="context">

**Step 2: Load context for placement**

Check for `<SPEC_TREE_CONTEXT>` marker. If absent or targeting a different path, invoke `/contextualizing` for the parent directory where the artifact will be placed.

This loads:

- Existing siblings (to avoid duplication and determine index)
- Ancestor ADRs/PDRs (to respect constraints)
- Parent spec (to understand scope)

**Bootstrap mode**: If `spx/` doesn't exist or has no product spec, invoke `/bootstrapping` first. It interviews the user and scaffolds the initial tree. Return here after bootstrapping to author individual artifacts.

</step>

<step name="placement">

**Step 3: Determine placement and index**

**For product specs:** Place at `spx/{product-name}.product.md`. No index.

**For ADRs/PDRs:** Place in the directory where the decision's scope applies. Assign an index using the ordering rules from `${CLAUDE_SKILL_DIR}/../understanding/references/ordering-rules.md`:

- The index encodes dependency: lower constrains higher
- An ADR/PDR at index N constrains all siblings at N+1 and above
- Use the distribution formula for new items: `i_k = 10 + floor(k * 89 / (N + 1))`
- Use midpoint insertion between existing indices

**For enabler/outcome nodes:** Place as a child of the parent where the concern belongs.

- Determine the index relative to siblings
- Enablers that others depend on get lower indices
- Independent outcomes can share the same index
- Derive the slug from the concern name (lowercase, hyphenated)

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
- What product invariants does this establish?

**Enabler:**

- What does this enabler provide?
- Which siblings depend on it?
- What assertions specify its output?

**Outcome (gate — answer the forcing question before proceeding):**

- Apply the forcing question from `${CLAUDE_SKILL_DIR}/../understanding/references/decomposition-semantics.md`: try to write it as an enabler first. Why can't this be PROVIDES X SO THAT Y CAN Z? What is uncertain about which output achieves the goal?
- Only if the forcing question confirms genuine uncertainty, gather hypothesis content:
  - Output: what the software does (testable)
  - Outcome: measurable change in user behavior
  - Impact: business value
- What assertions specify the output?

Use `AskUserQuestion` for genuine gaps. Do not ask about information already provided in the conversation.

</step>

<step name="draft">

**Step 5: Draft the artifact**

Read the appropriate template from `${CLAUDE_SKILL_DIR}/../understanding/templates/`. Fill it using the gathered content.

**Voice rules** (from `${CLAUDE_SKILL_DIR}/../understanding/references/durable-map.md`):

- **Atemporal**: State product truth. Never narrate history ("we discovered", "currently", "after investigating").
- **Permanent**: Write as if this will be true forever. If it wouldn't, it's temporal.
- **Test**: Read any sentence aloud. If it would sound wrong after the work is done, rewrite it.

**Assertion rules** (from `${CLAUDE_SKILL_DIR}/../understanding/references/assertion-types.md`):

- Every outcome must have at least one assertion
- Each assertion must link to evidence: `([test](tests/{slug}.{level}.test.{ext}))` for tests, `([enforce](path/to/config))` for lint rules, or `([review])` for human judgment
- Match assertion type to test strategy: Scenario → example-based, Property → property-based, etc.
- Test and enforce targets don't need to exist yet — the link is a contract for what will be created

**Enabler assertions**: Same rules apply. Enablers have assertions too — they specify what the infrastructure must do.

</step>

<step name="validate">

**Step 6: Validate the draft**

Before writing files, check:

- [ ] Correct artifact type for the content
- [ ] Placed in the right directory at the right index
- [ ] Nesting rules respected: outcomes CANNOT be children of enablers (see `${CLAUDE_SKILL_DIR}/../understanding/references/node-types.md` `<nesting_rules>` section)
- [ ] For outcomes: verify the forcing question from step 4 was answered — are the assertions a bet (majority could be swapped for different ones achieving the same goal)? If not, it should be an enabler (see `${CLAUDE_SKILL_DIR}/../understanding/references/decomposition-semantics.md`)
- [ ] Slug matches directory name convention (`{NN}-{slug}.{enabler|outcome}/` for nodes)
- [ ] Spec file named `{slug}.md` (no type suffix, no numeric prefix)
- [ ] Atemporal voice throughout — no temporal markers
- [ ] For outcomes: three-part hypothesis present (output → outcome → impact)
- [ ] For enablers: enables statement describes what it provides
- [ ] All assertions have evidence links: `[test]`, `[enforce]`, or `[review]` (targets don't need to exist yet)
- [ ] Assertion types match test strategy
- [ ] ADR/PDR compliance rules use MUST/NEVER format with `([review])` tags
- [ ] Spec compliance assertions use the correct evidence tag: `[test]` for behavioral tests, `[enforce]` for lint rules, `[review]` for human judgment
- [ ] No content misplacement (per `${CLAUDE_SKILL_DIR}/../understanding/references/what-goes-where.md`)

</step>

<step name="create">

**Step 7: Create files**

**For nodes (enabler/outcome):**

```text
spx/{parent-path}/{NN}-{slug}.{enabler|outcome}/
├── {slug}.md        # Spec file
└── tests/           # Empty directory for future tests
```

1. Create the directory
2. Write the spec file
3. Create the `tests/` directory
4. If the implementation doesn't exist yet: add the node path to `spx/EXCLUDE` and run the project's sync command. This excludes the node's tests from the quality gate until implementation begins. See `${CLAUDE_SKILL_DIR}/../understanding/references/excluded-nodes.md`.

**For decision records:**

```text
spx/{scope-path}/{NN}-{slug}.{adr|pdr}.md
```

Write the file directly.

**For product specs:**

```text
spx/{product-name}.product.md
```

Write the file. If `spx/CLAUDE.md` doesn't exist, note that one should be created as a project guide.

</step>

<step name="deliver">

**Step 8: Summarize and recommend next steps**

Report what was created:

- Artifact type and path
- Index and placement rationale
- Open decisions (if any were identified during drafting)

Recommend next steps based on artifact type:

| Created                      | Recommended next                                     |
| ---------------------------- | ---------------------------------------------------- |
| Product spec                 | Author top-level nodes with `/authoring`             |
| ADR/PDR                      | Verify compliance in affected nodes with `/aligning` |
| Enabler                      | Author dependent outcome nodes                       |
| Outcome with many assertions | Decompose with `/decomposing`                        |
| Outcome with few assertions  | Write tests with `/testing`                          |

</step>

</workflow>

<failure_modes>

**Failure 1: Temporal language survived into the spec**

Agent drafted an outcome spec from the user's description: "Users currently can't export data, so we need to add CSV export." The spec read: "The system currently lacks export functionality. CSV export addresses this gap." Both sentences are temporal — they narrate a problem being solved rather than stating product truth. The atemporal version: "The system exports query results as CSV files."

How to avoid: After drafting, apply the read-aloud test from `durable-map.md` to every sentence. If it would sound wrong after the feature ships, rewrite it.

**Failure 2: Assertions placed in ADRs**

Agent wrote an ADR that included: "Given a user uploads a file larger than 10MB, the system rejects it with a 413 error." This is a scenario assertion — it belongs in a spec, not in an ADR. The ADR should state the compliance rule: "ALWAYS: Uploaded files exceeding 10MB are rejected at the gateway. ([review])"

How to avoid: ADRs govern with MUST/NEVER compliance rules verified by review. If you're writing Given/When/Then, you're writing a spec assertion, not a decision record.

**Failure 3: Wrong template used for node type**

Agent created an enabler node using the outcome template. The spec had a three-part hypothesis (output → outcome → impact) but the node existed only to provide shared infrastructure for two siblings. The hypothesis was forced — "We believe that providing a database schema will cause developers to write queries faster" — because the node wasn't delivering user-facing value.

How to avoid: Apply the decision table from `node-types.md` before selecting a template. If you can't write a natural hypothesis, it's probably an enabler.

**Failure 4: Index collision with existing sibling**

Agent created a new outcome at index 32 without checking existing siblings. Another node already occupied index 32. The directory was created but overwrote the existing node's path.

How to avoid: Always invoke `/contextualizing` for the parent directory before creating any node. The sibling enumeration in the context manifest reveals all occupied indices.

**Failure 5: Rewrite pattern for temporal language**

Common temporal patterns from user input and their atemporal rewrites:

- TEMPORAL: "We need to support OAuth because users can't log in with SSO."
- ATEMPORAL: "Authentication uses OAuth 2.0. Users authenticate via SSO providers."

- TEMPORAL: "The API currently returns XML but we're switching to JSON."
- ATEMPORAL: "The API returns JSON responses conforming to the schema in ADR-15."

- TEMPORAL: "After investigating performance issues, we decided to add caching."
- ATEMPORAL: "Response caching reduces latency for repeated queries. Cache invalidation follows the policy in ADR-22."

**Failure 6: Junk-drawer container names**

Agent created a parent outcome named "advanced operations" that grouped prune, archive, and "future retention features." Six months later the same directory held archive, prune, dry-run, batch deletion, and a new hypothesis for session compaction — unrelated concerns glued together by a name that accepted anything.

A container name must describe what the container contains. If the name would accept arbitrary future scope ("advanced", "core", "misc", "utilities", "helpers", "operations"), it is wrong — the agent who added the next feature will find a plausible reason to drop it in.

How to avoid: read the proposed container name aloud and ask "what would I refuse to put in here?" If the honest answer is "nothing obvious," the name is junk-drawer. Rename it after the specific concern that justified creating the container (`session-retention`, not `advanced-operations`). When two concerns are independent, they get two containers — not a vague parent.

</failure_modes>

<anti_patterns>

**Writing implementation details in specs.** Specs describe *what*, not *how*. "How" belongs in ADRs (architecture) or code. If you're writing about function signatures, data structures, or algorithms, stop — that's an ADR or code.

**Copying temporal language from user input.** Users naturally say "we need to fix X" or "currently the system does Y." Translate to atemporal: "The system does Z" or "X handles Y correctly."

**Creating outcomes without hypotheses.** Every outcome must express: output → outcome → impact. If you can't write the hypothesis, the scope may be wrong — it might be an enabler or need further clarification.

**Placing assertions in ADRs/PDRs.** Decision records govern; they don't assert. Assertions belong in specs. ADRs/PDRs have compliance rules (MUST/NEVER) verified by review, not by tests.

**Numbering from 1.** Indices start at 10+ and use the sparse distribution formula. Never use single-digit indices.

**Listing children in the parent spec.** A parent spec describes the node's aggregate behavior — what the whole concern does from the outside. It does NOT enumerate or reference its children. Children describe their own concerns in their own specs. If your parent spec reads "X provides A, B, and C (these are the child nodes)", you have written a table of contents, not a declaration. Rewrite as a single coherent statement of what the node does; let `/contextualizing` walk the tree to surface children.

</anti_patterns>

<success_criteria>

Authoring is complete when:

- [ ] Artifact type determined (product, ADR, PDR, enabler, outcome)
- [ ] Context loaded for placement (or bootstrap mode for empty tree)
- [ ] Index and placement determined using ordering rules
- [ ] Content gathered from user (genuine gaps only)
- [ ] Template read and filled with atemporal voice
- [ ] Validation checklist passes
- [ ] Files created in correct location
- [ ] Next steps recommended

</success_criteria>
