---
name: refactoring
description: >-
  ALWAYS invoke this skill when moving nodes, re-scoping content, or extracting shared enablers.
  NEVER restructure the spec tree without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

<objective>

Apply structural changes to the Spec Tree: move nodes between parents, re-scope content across nodes, extract shared enablers, and consolidate nodes. Analyzes impact, applies changes, and reports what was modified.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understanding` first.

References from the understanding skill (`${CLAUDE_SKILL_DIR}/../understanding/`):

- `${CLAUDE_SKILL_DIR}/../understanding/references/decomposition-semantics.md` — enabler extraction, cross-cutting assertions
- `${CLAUDE_SKILL_DIR}/../understanding/references/ordering-rules.md` — index assignment, dependency encoding
- `${CLAUDE_SKILL_DIR}/../understanding/references/what-goes-where.md` — content taxonomy (what belongs where)
- `${CLAUDE_SKILL_DIR}/../understanding/references/node-types.md` — enabler vs outcome

</quick_start>

<operations>

This skill handles four structural operations:

| Operation           | Input                             | Output                                               |
| ------------------- | --------------------------------- | ---------------------------------------------------- |
| **Move**            | Node + new parent                 | Node relocated, paths updated                        |
| **Re-scope**        | Two+ nodes + assertions to move   | Assertions redistributed, specs updated              |
| **Extract enabler** | Two+ nodes sharing infrastructure | New enabler at lower index, dependents updated       |
| **Consolidate**     | Two+ nodes to merge               | Single node with combined content, old nodes removed |

</operations>

<workflow>

<step name="intake">

**Step 1: Identify the operation**

Determine which operation from the user's request:

- "Move X under Y" → **Move**
- "These assertions belong in the other node" / "The boundary is wrong" → **Re-scope**
- "Both nodes need the same thing" / "Extract shared X" → **Extract enabler**
- "These two nodes are really the same thing" → **Consolidate**

If the request is ambiguous, ask.

</step>

<step name="context">

**Step 2: Load context**

Invoke `/contextualizing` for each node involved in the operation. This loads:

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
- Will the node's index conflict with existing children at the target?
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
- Which siblings depend on it? (Must be 2+)
- What index should the enabler get? (Lower than all dependents)
- What assertions describe what the enabler provides?
- Do dependents' specs need updating to remove the shared content?

**For Consolidate:**

- Are the nodes truly the same concern, or just similar?
- Which node's hypothesis/enables statement survives?
- How do the combined assertions fit together?
- Which node's directory survives (lower index preferred)?
- What happens to the removed node's test files?

</step>

<step name="apply_move">

**Step 4a: Apply — Move**

1. Create the node directory at the new location with an appropriate index.
2. Move the spec file, renaming if the slug stays the same.
3. Move the `tests/` directory and all test files.
4. Move any child nodes recursively.
5. Update cross-cutting assertion links in ancestor specs that pointed to the old path.
6. Remove the old directory.

**Index assignment**: Use ordering rules from `${CLAUDE_SKILL_DIR}/../understanding/references/ordering-rules.md`. If inserting between existing siblings, use the midpoint.

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

1. Determine the enabler's index — must be lower than all dependent siblings.
2. Create the enabler directory: `{NN}-{slug}.enabler/`
3. Write the enabler spec using the template from `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/enabler-name.md`.
4. Write assertions that specify what the enabler provides.
5. Create the `tests/` directory.
6. Remove the shared content from each dependent node's spec.
7. If the shared content included test files, move them to the enabler's `tests/`.

</step>

<step name="apply_consolidate">

**Step 4d: Apply — Consolidate**

1. Choose the surviving node (prefer lower index, or the one whose scope is broader).
2. Merge assertions from the removed node into the surviving node:
   - Group by assertion type
   - Deduplicate identical assertions
   - Resolve conflicting assertions (ask user if unclear)
3. Merge test files from the removed node's `tests/` into the surviving node's `tests/`.
4. Update the surviving node's hypothesis or enables statement to cover the merged scope.
5. Update any cross-cutting assertion links in ancestor specs that pointed to the removed node.
6. Remove the old node's directory.
7. If the surviving node now exceeds ~7 assertions, flag for future decomposition.

</step>

<step name="validate">

**Step 5: Validate**

After applying any operation:

- [ ] No broken evidence links — every `([test](...))` in affected specs resolves to an existing file
- [ ] No orphaned test files — every test file in affected `tests/` directories is linked from an assertion
- [ ] No empty nodes — every node has at least one assertion
- [ ] Index ordering preserved — enablers at lower indices than dependents
- [ ] ADR/PDR scope correct — nodes are governed by the decisions in their ancestry
- [ ] Cross-cutting assertions in ancestors still reference valid paths
- [ ] Atemporal voice maintained — no temporal language introduced
- [ ] No content misplacement (per `${CLAUDE_SKILL_DIR}/../understanding/references/what-goes-where.md`)

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

Agent moved a node from directory A to directory B. Directory A contained an ADR at index 15 that governed the moved node. After the move, the node was no longer a descendant of that ADR's scope — the architectural constraint silently disappeared. Tests continued to pass because they tested behavior, not ADR compliance.

How to avoid: In the impact analysis step, glob for all ADRs/PDRs in the source ancestry. For each one, check whether the constraint still applies at the destination. If it does, either the ADR needs to move too or a new ADR must be created at the destination's scope.

**Failure 2: Test links broken after move, not caught**

Agent moved a node and its `tests/` directory but didn't update the assertion evidence links in ancestor specs that referenced `([test](old-path/tests/...))`. The assertions still claimed coverage, but the links pointed to nonexistent files.

How to avoid: After any move, grep the entire `spx/` tree for the old path. Every match is a broken reference that must be updated. The validation step checks "every `([test](...))` resolves to an existing file" — run it.

**Failure 3: Consolidated nodes with different hypotheses**

Agent merged two "parsing" outcomes because they sounded similar. One parsed user input for validation; the other parsed API responses for data extraction. Different hypotheses, different users, different failure modes. The merged node's hypothesis became a vague compromise that fit neither concern well.

How to avoid: Before consolidating, compare the hypotheses (for outcomes) or enables statements (for enablers). If they serve different users or have different "outcome" components in the three-part hypothesis, they are distinct nodes regardless of implementation similarity.

**Failure 4: Used `mv` instead of `git mv` for tracked files**

Agent used Bash `mv` to relocate a node directory. Git saw this as a deletion plus an unrelated new file. The file's history was lost, and `git blame` showed the move as the original author of all lines.

How to avoid: Always use `git mv` for files tracked by git. This preserves rename detection and history. Check `git status` first — if the file shows as tracked, use `git mv`.

**Failure 5: Temporal language introduced during re-scope**

Agent moved assertions between nodes and rewrote the source node's hypothesis to explain what happened: "After extracting the validation concerns into the sibling node, this outcome focuses on data transformation." This narrates a refactoring history — it's temporal. The atemporal version: "This outcome transforms raw input into normalized records."

How to avoid: When rewriting specs after structural changes, treat the rewrite as if the spec was always this way. The spec tree is a durable map — it states product truth, not a changelog. Apply the read-aloud test: if the sentence would sound strange to someone who never saw the old structure, it's temporal.

</failure_modes>

<anti_patterns>

**Moving without checking ADR/PDR scope.** A node governed by an ADR at index 15 in directory A is no longer governed by that ADR if moved to directory B. The constraint silently disappears.

**Consolidating similar but distinct nodes.** Two nodes about "parsing" may parse different things for different reasons. If they have different hypotheses, they're different outcomes — similarity in implementation doesn't mean similarity in purpose.

**Extracting enablers for single dependents.** An enabler with only one dependent is not an enabler — it's an internal concern of that dependent. Extract only when 2+ siblings share the need.

**Leaving empty nodes after re-scope.** If you move all assertions out of a node, the node is now empty. Either remove it or consolidate it — don't leave a spec with no assertions.

</anti_patterns>

<success_criteria>

Refactoring is complete when:

- [ ] Operation identified and context loaded
- [ ] Impact analyzed before applying
- [ ] Changes applied (move/re-scope/extract/consolidate)
- [ ] Validation checklist passes (no broken links, no orphans, no empty nodes)
- [ ] Summary report with all files created/modified/moved/removed
- [ ] Follow-up issues noted if any

</success_criteria>
