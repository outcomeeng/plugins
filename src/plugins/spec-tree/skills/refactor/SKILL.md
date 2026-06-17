---
name: refactor
description: ALWAYS invoke this skill when moving nodes, re-scoping content, or extracting shared enablers. NEVER restructure the spec tree without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

<objective>

Apply structural changes to the Spec Tree: move nodes between parents, re-scope content across nodes, extract shared enablers, and consolidate nodes. Analyzes impact, applies changes, and reports what was modified.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understand` first.

References and workflows:

- `${CLAUDE_SKILL_DIR}/../understand/references/what-goes-where.md` — content taxonomy (what belongs where)
- `${CLAUDE_SKILL_DIR}/../understand/references/node-types.md` — enabler vs outcome
- `/decompose` — structural composition, shared enabler extraction, consolidation boundaries, ordering evidence, and index assignment

</quick_start>

<operations>

This skill handles four structural operations:

| Operation           | Input                             | Output                                                                     |
| ------------------- | --------------------------------- | -------------------------------------------------------------------------- |
| **Move**            | Node + new parent                 | Node relocated, paths updated                                              |
| **Re-scope**        | Two+ nodes + assertions to move   | Assertions redistributed, specs updated                                    |
| **Extract enabler** | Two+ nodes sharing infrastructure | `/decompose` defines the enabler and indices, refactoring applies the move |
| **Consolidate**     | Two+ nodes to merge               | Single node with combined content, old nodes removed                       |

</operations>

<workflow>

<step name="intake">

**Step 1: Identify the operation**

Determine which operation from the user's request:

- "Move X under Y" → **Move**
- "These assertions belong in the other node" / "The boundary is wrong" → **Re-scope**
- "Both nodes need the same thing" / "Extract shared X" → **Extract enabler**
- "These two nodes are really the same thing" → **Consolidate**

Normalize every referenced node, ADR, and PDR to its full path from `spx/` before analyzing impact. A bare node name, decision filename, or numeric prefix is not enough to identify a file.

If the request is ambiguous, ask.

</step>

<step name="context">

**Step 2: Load context**

Invoke `/contextualize` for each node involved in the operation. This loads:

- The affected nodes' specs and assertions
- Parent and ancestor specs
- ADRs/PDRs in scope
- Sibling nodes (for index calculations)

</step>

<step name="impact">

**Step 3: Analyze impact**

Before applying changes, determine what will be affected:

**For Move:**

- Does the target parent exist?
- Will the node's existing index conflict with children at the target?
- Does the move require choosing a new sibling index? If yes, invoke `/decompose` for the target parent before applying.
- Do any ADRs/PDRs at the source location govern this node? Will it leave their scope?
- Do any ancestor specs have cross-cutting assertions that reference this node?
- Are there test links in other specs that point into this node's `tests/` directory?

**For Re-scope:**

- Which assertions move from which node to which?
- Do the assertions' test links need updating (different `tests/` directory)?
- After redistribution, does any node end up with zero assertions? (If so, it should be removed or consolidated.)
- Do the remaining assertions in each node still form a coherent concern?

**For Extract enabler:**

- What exactly is shared? (Infrastructure, utility, foundation)
- Which siblings need it? (Must be 2+)
- Has `/decompose` defined the shared enabler, ordering evidence, and index placement?
- Which assertions describe what the enabler provides?
- Do dependent specs need updating to remove the shared content?

**For Consolidate:**

- Are the nodes truly the same concern, or just similar?
- Which node's hypothesis/enables statement survives?
- How do the combined assertions fit together?
- Which node's directory survives based on durable scope identity and evidence links?
- Does consolidation alter sibling ordering or child composition? If yes, invoke `/decompose` before applying.
- What happens to the removed node's test files?

</step>

<step name="apply_move">

**Step 4a: Apply — Move**

1. Create the node directory at the new location with an appropriate index.
2. Move the spec file, renaming if the slug stays the same.
3. Move the `tests/` directory and all test files.
4. If PLAN.md or ISSUES.md exist in the source directory, move them to the new location — they are node-local coordination notes.
5. Move any child nodes recursively.
6. Update cross-cutting assertion links in ancestor specs that pointed to the old path.
7. Remove the old directory.

**Index assignment**: Preserve the node's existing index when possible. If insertion or reindexing is needed, invoke `/decompose` for the target parent before moving files.

</step>

<step name="apply_rescope">

**Step 4b: Apply — Re-scope**

1. Remove the assertions from the source node's spec.
2. Add the assertions to the target node's spec under the correct assertion type heading.
3. If test files exist for the moved assertions:
   - Move the test files from source `tests/` to target `tests/`.
   - Update the test links in the assertions.
4. If the source node now has zero assertions, flag it for consolidation or removal.
5. Verify both specs still have coherent concerns.

</step>

<step name="apply_extract">

**Step 4c: Apply — Extract enabler**

1. Invoke `/decompose` on the parent containing the affected siblings, with the shared concern recorded in the parent `PLAN.md` or `ISSUES.md` if needed.
2. Apply the resulting structure: create the enabler directory and spec from the decomposition result.
3. Move assertions and test files for the shared concern into the enabler.
4. Remove the shared content from each dependent node's spec.
5. Update evidence links that moved with the assertions.

</step>

<step name="apply_consolidate">

**Step 4d: Apply — Consolidate**

1. Choose the surviving node by durable scope identity, evidence links, and governing decisions.
2. Merge assertions from the removed node into the surviving node:
   - Group by assertion type
   - Deduplicate identical assertions
   - Resolve conflicting assertions (ask user if unclear)
3. Merge test files from the removed node's `tests/` into the surviving node's `tests/`.
4. Update the surviving node's hypothesis or enables statement to cover the merged scope.
5. Update any cross-cutting assertion links in ancestor specs that pointed to the removed node.
6. Remove the old node's directory.
7. If the surviving node now exceeds ~7 assertions or mixes independent concerns, invoke `/decompose` for the surviving node.

</step>

<step name="validate">

**Step 5: Validate**

After applying any operation:

- [ ] No broken evidence links — every `([test](...))` in affected specs resolves to an existing file
- [ ] No orphaned test files — every test file in affected `tests/` directories is linked from an assertion
- [ ] Coordination-note files (PLAN.md, ISSUES.md) moved with their node — they are node-local, not shared (do not need evidence links)
- [ ] No empty nodes — every node has at least one assertion
- [ ] Any new or changed index assignment came from `/decompose`
- [ ] ADR/PDR scope correct — nodes are governed by the decisions in their ancestry
- [ ] Cross-cutting assertions in ancestors still reference valid paths
- [ ] Every node, ADR, and PDR reference uses a full path from `spx/`
- [ ] Atemporal voice maintained — no temporal language introduced
- [ ] No content misplacement (per `${CLAUDE_SKILL_DIR}/../understand/references/what-goes-where.md`)

</step>

<step name="report">

**Step 6: Report**

Summarize what changed:

```text
Refactoring: {operation type}

Files created:
  - {path}

Files modified:
  - {path}: {what changed}

Files moved:
  - {old path} → {new path}

Files removed:
  - {path}

Assertions redistributed: {count}
Test files moved: {count}
Cross-cutting links updated: {count}
```

If the refactoring revealed further issues (nodes with too many assertions, orphaned enablers, scope ambiguity), note them as recommended follow-ups.

</step>

</workflow>

<failure_modes>

**Failure 1: ADR scope silently lost after move**

Claude moved a node from directory A to directory B. Directory A contained an ADR at index 15 that governed the moved node. After the move, the node was no longer a descendant of that ADR's scope — the architectural constraint silently disappeared. Tests continued to pass because they tested behavior, not ADR compliance.

How to avoid: In the impact analysis step, glob for all ADRs/PDRs in the source ancestry. For each one, check whether the constraint still applies at the destination. If it does, either the ADR needs to move too or a new ADR must be created at the destination's scope.

**Failure 2: Test links broken after move, not caught**

Claude moved a node and its `tests/` directory but didn't update the assertion evidence links in ancestor specs that referenced `([test](old-path/tests/...))`. The assertions still claimed coverage, but the links pointed to nonexistent files.

How to avoid: After any move, grep the entire `spx/` tree for the old path. Every match is a broken reference that must be updated. The validation step checks "every `([test](...))` resolves to an existing file" — run it.

**Failure 3: Bare decision reference survived the move**

Claude reported that the moved node still followed `15-build.adr.md`, but another directory also contained `15-build.adr.md`. The reference was impossible to resolve from the report.

How to avoid: Use full paths from `spx/` for every node, ADR, and PDR before and after the move. A correct report says `spx/.../15-build.adr.md`, never just `15-build.adr.md`.

**Failure 4: Consolidated nodes with different hypotheses**

Claude merged two "parsing" outcomes because they sounded similar. One parsed user input for validation; the other parsed API responses for data extraction. Different hypotheses, different users, different failure modes. The merged node's hypothesis became a vague compromise that fit neither concern well.

How to avoid: Before consolidating, compare the hypotheses (for outcomes) or enables statements (for enablers). If they serve different users or have different "outcome" components in the three-part hypothesis, they are distinct nodes regardless of implementation similarity.

**Failure 5: Used `mv` instead of `git mv` for tracked files**

Claude used Bash `mv` to relocate a node directory. Git saw this as a deletion plus an unrelated new file. The file's history was lost, and `git blame` showed the move as the original author of all lines.

How to avoid: Always use `git mv` for files tracked by git. This preserves rename detection and history. Check `git status` first — if the file shows as tracked, use `git mv`.

**Failure 6: Temporal language introduced during re-scope**

Claude moved assertions between nodes and rewrote the source node's hypothesis to explain what happened: "After extracting the validation concerns into the sibling node, this outcome focuses on data transformation." This narrates a refactoring history — it's temporal. The atemporal version: "This outcome transforms raw input into normalized records."

How to avoid: When rewriting specs after structural changes, treat the rewrite as if the spec was always this way. The spec tree is a durable map — it states product truth, not a changelog. Apply the read-aloud test: if the sentence would sound strange to someone who never saw the old structure, it's temporal.

**Failure 7: Blanket-re-pointed cited assertions to a generalized parent**

Claude generalized a node into a new parent enabler with multiple children and re-pointed every assertion that cited an ADR/PDR onto the new parent. Some of those assertions held only for the original child's surface or capability, not for every child. An agentic review then surfaced them one per round — each as "the new sibling does not realize this now-universal invariant" — producing a long fix cascade (~10 rounds in one generalization: plan-level approval, per-integration behaviors, persistence, structural discovery, back-link suppression, mount mode), each round correcting one over-universalized assertion.

How to avoid: Before re-pointing, classify each citing assertion. Universal — holds for every child of the generalized parent — cites the parent. Node-specific — holds only for the child with that surface or capability — cites the realizing child. Route each citation to parent or child by that classification; never blanket-re-point every citation to the new parent.

</failure_modes>

<anti_patterns>

**Moving without checking ADR/PDR scope.** A node governed by an ADR at index 15 in directory A is no longer governed by that ADR if moved to directory B. The constraint silently disappears.

**Using bare node or decision names.** A refactor report or PLAN.md entry that names `32-parser.enabler` or `15-build.adr.md` cannot be resolved reliably. Use full paths from `spx/`.

**Consolidating similar but distinct nodes.** Two nodes about "parsing" may parse different things for different reasons. If they have different hypotheses, they're different outcomes — similarity in implementation doesn't mean similarity in purpose.

**Extracting enablers directly.** Refactoring applies tree surgery; `/decompose` owns shared-enabler boundaries, ordering evidence, and indices.

**Leaving empty nodes after re-scope.** If all assertions move out of a node, the node is now empty. Either remove it or consolidate it — don't leave a spec with no assertions.

**Treating `spx/local/` as a node directory.** `spx/local/` holds skill overlays, not spec nodes. It has no enabler or outcome suffix and its files have no spec structure. Do not move, archive, or validate it as part of tree surgery.

**Blanket-re-pointing cited assertions to a generalized parent.** When generalizing a node into a new parent enabler, an assertion that held only for the original child does not automatically hold for every child. Classify each citation universal vs node-specific and re-point it to the parent or the realizing child accordingly.

</anti_patterns>

<success_criteria>

Refactoring is complete when:

- [ ] Operation identified and context loaded
- [ ] Impact analyzed before applying
- [ ] Structural composition decisions delegated to `/decompose` when needed
- [ ] Changes applied (move/re-scope/extract/consolidate)
- [ ] Validation checklist passes (no broken links, no orphans, no empty nodes)
- [ ] Summary report with all files created/modified/moved/removed
- [ ] Follow-up issues noted if any

</success_criteria>
