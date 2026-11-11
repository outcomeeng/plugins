---
name: refactor
description: ALWAYS invoke this skill when moving nodes, re-scoping content, or extracting shared providers. NEVER restructure the Product Tree without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(git status:*), Bash(git mv:*), Bash(git rm -r:*), Bash(spx validation markdown:*), Bash(spx spec status:*), {{! tool('use_skill') !}}
---

<objective>

A restructured Product Tree — nodes moved between parents, content re-scoped, shared providers extracted, nodes consolidated — with impact analyzed and modifications reported.

</objective>

<context>

**PREREQUISITE**: Check for a live `<PRODUCT_TREE_FOUNDATION>` marker. When it is absent, load the foundation first. Use skill `product-tree:understand`.

</context>

<reference_guides>

- Live `/understand` `<artifact_placement>` — content taxonomy and placement rules
- Live `/understand` `<identity_and_kinds>` — the seven kinds, their order, and containment
- `product-tree:decompose` — structural composition, shared provider extraction, consolidation boundaries, ordering evidence, and index assignment

</reference_guides>

<operations>

This skill handles four structural operations:

| Operation            | Input                           | Output                                                                                      |
| -------------------- | ------------------------------- | ------------------------------------------------------------------------------------------- |
| **Move**             | Node + new parent               | Node relocated, paths updated                                                               |
| **Re-scope**         | Two+ nodes + assertions to move | Assertions redistributed, specs updated                                                     |
| **Extract provider** | Two+ nodes sharing a behavior   | `/decompose` defines the provider node, its kind, and indices, refactoring applies the move |
| **Consolidate**      | Two+ nodes to merge             | Single node with combined content, old nodes removed                                        |

</operations>

<workflow>

<step name="intake">

**Step 1: Identify the operation**

Determine which operation from the user's request:

- "Move X under Y" → **Move**
- "These assertions belong in the other node" / "The boundary is wrong" → **Re-scope**
- "Both nodes need the same thing" / "Extract shared X" → **Extract provider**
- "These two nodes are really the same thing" → **Consolidate**

Normalize every referenced node, ADR, and PDR to its full path from `spx/` before analyzing impact. A bare node name, decision filename, or numeric prefix is not enough to identify a file.

If the request is ambiguous, ask.

</step>

<step name="context">

**Step 2: Load context**

A live `<PRODUCT_TREE_CONTEXT target="...">` marker for the exact path of every node the operation touches — the moved, re-scoped, extracted, or consolidated nodes and every parent that gains or loses a child, `spx/` when the root is that parent — is Step 3's input. Use skill `product-tree:contextualize` once per such node whose marker the live conversation lacks. Each invocation loads:

- The node's spec and assertions
- Parent and ancestor specs
- ADRs/PDRs in scope
- Sibling nodes, with the index each carries

</step>

<step name="impact">

**Step 3: Analyze impact**

Before applying changes, determine what will be affected:

**For Move:**

- Does the target parent exist?
- Will the node's existing index conflict with children at the target?
- Does the move change the node's parent or its index? If yes, the index comes from `/decompose` on the target parent, and Step 4a does not start until the matrix file at the path its result names exists. Use skill `product-tree:decompose` with the target parent as its only argument.
- Do any ADRs/PDRs at the source location govern this node? Will it leave their scope?
- Do any ancestor specs have cross-cutting assertions that reference this node?
- Are there test links in other specs that point into this node's `tests/` directory?

**For Re-scope:**

- Which assertions move from which node to which?
- Do the assertions' test links need updating (different `tests/` directory)?
- After redistribution, does any node end up with zero assertions? (If so, Step 4b consolidates or removes it.)
- Do the remaining assertions in each node still form a coherent concern?

**For Extract provider:**

- What exactly is shared? (Infrastructure, utility, foundation)
- Which siblings need it? (Must be 2+)
- Has `product-tree:decompose` defined the shared provider, ordering evidence, and index placement?
- Which assertions describe what the provider provides?
- Do dependent specs need updating to remove the shared content?

**For Consolidate:**

- Are the nodes truly the same concern, or just similar?
- Which node's opening survives?
- How do the combined assertions fit together?
- Which node's directory survives based on durable scope identity and evidence links?
- Does consolidation alter sibling ordering or child composition? If yes, compose the parent before applying. Use skill `product-tree:decompose` with the parent as its only argument.
- What happens to the removed node's test files?

</step>

<step name="apply_move">

**Step 4a: Apply — Move**

A move that changes the node's parent or its index starts only when the matrix file at the path `/decompose` named in its result for the target parent exists and names the moved node's disposition against every existing sibling there; read the new index from that file. A `git mv` with no such file does not run. A slug rename that keeps parent and index needs no matrix.

1. Move the node directory to the new location with the index the matrix file names, using `git mv <old-node-directory> <new-node-directory>`. The spec, the `tests/` directory, any ISSUES.md or prior-form PLAN.md, and every child node move with it, and no old directory remains.
2. When the slug changes, rename the spec file with `git mv` so it repeats the new slug.
3. Update cross-cutting assertion links in ancestor specs that pointed to the old path.

</step>

<step name="apply_rescope">

**Step 4b: Apply — Re-scope**

1. Remove the assertions from the source node's spec.
2. Add the assertions to the target node's spec under the correct assertion type heading.
3. If test files exist for the moved assertions:
   - Move each test file from source `tests/` to target `tests/` with `git mv <old> <new>`.
   - Update the test links in the assertions.
4. If the source node now has zero assertions, consolidate it into the node that owns its remaining concern (Step 4d), or, when no concern remains, remove its directory with `git rm -r <node-directory>`.
5. Verify both specs still have coherent concerns.

</step>

<step name="apply_extract">

**Step 4c: Apply — Extract provider**

1. Compose the parent containing the affected siblings. Use skill `product-tree:decompose` with that parent as its only argument.
2. Apply the resulting structure: the decomposition wrote the provider directory and spec, so this step creates neither again.
3. Move assertions for the shared concern into the provider, and move their test files with `git mv <old> <new>`.
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
3. Move each test file from the removed node's `tests/` into the surviving node's `tests/` with `git mv <old> <new>`, before Step 6 removes the emptied node.
4. Update the surviving node's opening to cover the merged scope.
5. Update any cross-cutting assertion links in ancestor specs that pointed to the removed node.
6. Remove the old node's directory with `git rm -r <old-node-directory>` once its assertions and tests live in the surviving node, so Git records the removal in the changeset.
7. If the surviving node now exceeds ~7 assertions or mixes independent concerns, decompose the surviving node. Use skill `product-tree:decompose` with the surviving node as its only argument.

</step>

<step name="validate">

**Step 5: Validate**

After applying any operation, run the product's verify command for the spec lane against the restructured tree: `spx validation markdown` and `spx spec status --format json`, and every further command the root guide names for a spec-only change, which runs through per-call approval where the grants above omit it. A nonzero exit stops the run with the command, its exit code, and its failing output. Then check each criterion:

- [ ] No broken evidence links — every `([test](...))` in affected specs resolves to an existing file
- [ ] No orphaned test files — every test file in affected `tests/` directories is linked from an assertion
- [ ] Notes (ISSUES.md, and a prior-form PLAN.md) moved with their node — they are node-local, not shared (do not need evidence links)
- [ ] No empty nodes — every node has at least one assertion
- [ ] Any new or changed index came from the matrix file at the path `product-tree:decompose` named in its result for the target parent
- [ ] ADR/PDR scope correct — nodes are governed by the decisions in their ancestry
- [ ] Cross-cutting assertions in ancestors still reference valid paths
- [ ] Every node, ADR, and PDR reference uses a full path from `spx/`
- [ ] Atemporal voice maintained — no temporal language introduced
- [ ] No content misplacement (per the live `/understand` `<artifact_placement>` and the placements it rules out)
- [ ] The product's verify command for the spec lane passed on the restructured tree

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

If the refactoring revealed further issues (nodes with too many assertions, orphaned providers, scope ambiguity), note them as recommended follow-ups.

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

**Failure 4: Consolidated nodes with different contracts**

Claude merged two "parsing" outcomes because they sounded similar. One parsed user input for validation; the other parsed API responses for data extraction. Different contracts, different users, different failure modes. The merged node's opening became a vague compromise that fit neither concern well.

How to avoid: Before consolidating, compare the openings — the contract each node states and the consumption context or audience it serves. If they own different contracts or serve different contexts, they are distinct nodes regardless of implementation similarity.

**Failure 5: Used `mv` instead of `git mv` for tracked files**

Claude used Bash `mv` to relocate a node directory. Git saw this as a deletion plus an unrelated new file. The file's history was lost, and `git blame` showed the move as the original author of all lines.

How to avoid: Always use `git mv` for files tracked by git. This preserves rename detection and history. Check `git status` first — if the file shows as tracked, use `git mv`.

**Failure 6: Temporal language introduced during re-scope**

Claude moved assertions between nodes and rewrote the source node's opening to explain what happened: "After extracting the validation concerns into the sibling node, this outcome focuses on data transformation." This narrates a refactoring history — it's temporal. The atemporal version: "This outcome transforms raw input into normalized records."

How to avoid: When rewriting specs after structural changes, treat the rewrite as if the spec was always this way. The Product Tree is a durable map — it states product truth, not a changelog. Apply the read-aloud test: if the sentence would sound strange to someone who never saw the old structure, it's temporal.

**Failure 7: Blanket-re-pointed cited assertions to a generalized parent**

Claude generalized a node into a new parent node with multiple children and re-pointed every assertion that cited an ADR/PDR onto the new parent. Some of those assertions held only for the original child's surface or capability, not for every child. An agentic review then surfaced them one per round — each as "the new sibling does not realize this now-universal invariant" — producing a long fix cascade (~10 rounds in one generalization: plan-level approval, per-integration behaviors, persistence, structural discovery, back-link suppression, mount mode), each round correcting one over-universalized assertion.

How to avoid: Before re-pointing, classify each citing assertion. Universal — holds for every child of the generalized parent — cites the parent. Node-specific — holds only for the child with that surface or capability — cites the realizing child. Route each citation to parent or child by that classification; never blanket-re-point every citation to the new parent.

**Failure 8: Moved the node before the matrix existed**

Claude moved a top-level node to the next free index above the node it consumes, then did it again one index higher when the first number was rejected. No ordering-evidence matrix existed for the root either time, and the operator reset both moves.

How to avoid: Step 4a reads the index from the matrix file at the path `/decompose` named in its result for the target parent, and a `git mv` with no such file does not run.

</failure_modes>

<anti_patterns>

**Leaving empty nodes after re-scope.** If all assertions move out of a node, the node is now empty. Either remove it or consolidate it — don't leave a spec with no assertions.

**Treating `spx/local/` as a node directory.** `spx/local/` holds skill overlays, not spec nodes. It has no kind suffix and its files have no spec structure. Do not move, archive, or validate it as part of tree surgery.

</anti_patterns>

<success_criteria>

Refactoring is complete when the restructured tree shows:

- [ ] Every node the operation touched, the parent that gained or lost a child included, had a live `<PRODUCT_TREE_CONTEXT>` marker before the first read
- [ ] Every evidence link in an affected spec resolves to an existing file, and every test file in an affected `tests/` directory is linked from an assertion
- [ ] Every affected node carries at least one assertion, and no empty node directory remains
- [ ] Every moved or surviving node is governed by the decisions in its new ancestry
- [ ] Every new or changed index came from the matrix file at the path `product-tree:decompose` named in its result, and no `git mv` ran before that file existed
- [ ] Every moved tracked file kept its history through `git mv`
- [ ] The product's verify command for the spec lane passed on the restructured tree
- [ ] The report names every file created, modified, moved, and removed, and every follow-up issue

</success_criteria>
