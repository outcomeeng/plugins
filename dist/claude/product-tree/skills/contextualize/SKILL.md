---
name: contextualize
description: ALWAYS invoke this skill when asking about status, progress, or what exists in the Product Tree. NEVER work on any part of the Product Tree without loading context through this skill first.
argument-hint: "<spx-root-or-full-node-path> [routine|authoring]"
arguments: target mode
allowed-tools: Read, Glob, Grep, Bash(spx config show --json), Bash(spx spec context show:*), Skill
---

<objective>

A `<PRODUCT_TREE_CONTEXT target="...">` marker carrying a structured context manifest for a product-root or node target: the target's Work Context in the mode its caller names, each member read at the view that mode gives it, in one total read order, with the instruction files and the lifecycle overlay read beside it and no heuristic selection.

</objective>

<essential_principles>

**COMPLETE CONTEXT OR ABORT. NO EXCEPTIONS.**

- Every node along the path must have its spec file (`{slug}.spec.md`, or the prior `{slug}.md` a 3.x-authored tree still carries). A missing spec file aborts with remediation guidance.
- The Work Context is a deterministic set derived from containment, Index order, and explicit links. No title, keyword, or judged relevance adds or drops a member.
- Each member enters at one view: Opening, Declaration, or Complete, as `<views>` defines them.
- Every governing Decision Record enters at Complete, never filtered by title. An ancestor Decision Record indexed at or above the child the path continues through stays out unless a member file cites it.
- Explicit full-path Decision Record citations in member files enter the Work Context; notes never add a member.
- A context-grounded answer requires the matching `<PRODUCT_TREE_CONTEXT target="...">` marker. Loading this skill or reading a pre-compaction summary supplies no context.
- Context loading reads the checkout as it stands. It never runs `/sync-base`, fetches, rebases, or otherwise moves the checkout, so the context it reports describes the head it found.
- No test, eval, or probe file is read here. Test-body inspection belongs to `/test`, `/audit-tests`, or `/apply`.
- **Always use canonical full paths** from `spx/` for targets and references. The product-root target is exactly `spx/`; a node target begins with `spx/` and contains only node-directory segments. Never refer to nodes, ADRs, or PDRs by bare name or numeric prefix; sibling numbers repeat under different parents and decision files cannot be found without their parent path.
  - Wrong: `/contextualize 32-parser.capability`
  - Right: `/contextualize spx/{path-to-node}`

**BOOTSTRAP MODE**: Bootstrap is derived from the documented target and tree state, never from an undeclared operation. When `$target` is exactly `spx/`, one product document exists, and no node directories exist, emit the product-root manifest with `bootstrap=true`. A missing node target always aborts; a node that does not yet exist takes its context from its existing parent (`spx/` for a top-level node or the canonical full parent node path for a nested node).

</essential_principles>

<modes>

The caller names the mode as `$mode`:

| Mode        | The caller's work                                                       |
| ----------- | ----------------------------------------------------------------------- |
| `routine`   | Specify, Implement, and a code, test, or evidence Audit                 |
| `authoring` | Declare, Refinement, decomposition, and a spec or Decision Record Audit |

A call that names no mode loads Authoring mode, whose members hold every member of Routine mode, and the manifest names Authoring as the mode taken. Any other value aborts: "Unknown mode: $mode. Supply `routine` or `authoring`, or name none for Authoring."

Both modes load:

- the Product spec and every ancestor spec at Complete;
- for the target and each ancestor, each lower-Index sibling spec at Declaration;
- every governing Decision Record at Complete: the target's own, each ancestor record indexed below the child the path continues through, and each cross-subtree and transitive citation;
- every `ISSUES.md` of the Product, the target, and its ancestors;
- the target spec at Complete, with its Outcome record `{slug}.outcome.md` and its Knowledge `knowledge/index.md` when they exist;
- every contract file a member spec links, and every implementation file the target or its Variants pin.

The modes differ only on peers and children:

- **Routine**: list same-Index and higher-Index siblings by directory entry and read no file of theirs. Load no immediate child, deeper descendant, test, eval, or probe file, and no other Node's Outcome record or Knowledge.
- **Authoring**: add the target's immediate children, Variants included, at Declaration, and its same-Index and higher-Index siblings at Opening. Read a sibling at Declaration instead when the work scopes a provider's mandate against its direct consumers. Load no deeper descendant, test, eval, or probe file, and no other Node's Outcome record or Knowledge.

For the product-root target `spx/`, the Work Context holds the Product spec, every product-level Decision Record, and `spx/ISSUES.md`. Authoring mode adds every top-level node at Declaration.

</modes>

<views>

Present each member at its view:

- **Opening**: the title and role Opening for an output Node spec (`PROVIDES`, `SO THAT`, `CAN`, or the Opening its kind declares), the title and optional identity paragraph for a `.product` spec, and the title and Opening for a Decision Record. Front matter stays out.
- **Declaration**: the Opening plus every heading and every shortened Assertion or rule. Scenarios keep bare slugs without Given, When, or Then lines. Probes keep their sentence. Test, eval, and probe links unwrap to bare slugs while contract links stay intact. Mapping and Evaluate subsections keep their sentence and case slugs without table bodies. For a `.product` spec, Declaration is the full body without front matter.
- **Complete**: the whole file verbatim, including YAML front matter, artifact links, Scenario steps, and full tables.

Read each member file with the file-read tool, then carry only its view into the manifest's member list. An `ISSUES.md`, an Outcome record, a Knowledge `index.md`, a contract file, and an implementation file enter at Complete.

</views>

<read_order>

The read order is total and byte-identical for the same tree contents, target, and mode:

1. The Product spec, then each ancestor top-down, then the target.
2. Within a level, the spec precedes its governing Decision Records, which precede its `ISSUES.md`, which precedes its lower-Index sibling specs.
3. At the target, its lower-Index sibling specs precede its Outcome record and its Knowledge `index.md`. In Authoring mode those precede its immediate children, which precede its same-Index and higher-Index siblings.
4. Members that share an Index follow in slug order.
5. Each cited Decision Record follows in the order of its first citation in the order so far, then each linked contract file in the order of its first link, then each pinned implementation file in path order.

The active root harness instruction file `CLAUDE.md`, each on-path subdirectory `CLAUDE.md` in path order from the root, and the local overlays under `spx/local/` are enumerated as sets apart from the read order. A `CLAUDE.md` directly inside the `spx/` directory is no instruction input.

</read_order>

<workflow>

<step name="gate">

**Step GATE: Check foundation**

Check the live conversation for the `<PRODUCT_TREE_FOUNDATION>` marker.
A marker mentioned only in a compaction summary, Handoff, prior run description, or statement that `/understand` ran does not count. Reading the `/understand` SKILL.md file alone does not count.
If absent → STOP. Use skill `product-tree:understand`. Then continue with Step 0. Do not inspect git, session state, product files, or product-tree content before the live marker is present.

</step>

<step name="locate">

**Step 0: Locate target, mode, and methodology**

If the invocation supplies no target path, ABORT: "A canonical target is required. Invoke `/contextualize spx/` for the product root or `/contextualize spx/{path-to-node}` for a node."

Before the first filesystem lookup, accept `$target` only when it is the exact product-root target `spx/` or a repository-relative node target beginning with `spx/` whose non-empty segments after `spx/` each match `{index}-{slug}.{kind}` — one of the seven kinds, or the prior `enabler` and `outcome` forms a tree authored under a 3.x version still carries. Reject absolute paths, empty targets, repeated separators, `.` or `..` segments, trailing separators on node targets, and malformed node segments. Otherwise ABORT: "Invalid target path: $target. Supply `spx/` or one canonical full `spx/...` node path."

Resolve the mode per `<modes>`.

Read the methodology declaration from the SPX CLI's structured output:

```bash
spx config show --json
```

Take `methodology.source` and `methodology.version` from that output, never from a plugin distribution version, a changelog, or prose. When the declared version is before 4.0, follow `<pre_4_context>` in place of Steps 1 to 4, and the manifest names the declared version whose context it loaded.

Then locate the product file and the target:

```bash
Glob: "spx/*.spec.md"      # the root product document carries kind: product
Glob: "spx/*.product.md"   # the prior form a 3.x-authored tree still carries
Glob: "$target/*.md"       # node targets only
```

If the product file is missing, ABORT: "No product file found in spx/. Create one with `/bootstrap` first."

If a node target path doesn't exist, ABORT: "Target path not found: $target. Check the path, or target its existing parent while the node does not yet exist."

For the exact product-root target `spx/`, list top-level node directories. Set `bootstrap=true` when none exist and `bootstrap=false` otherwise. For every node target, set `bootstrap=false`.

</step>

<step name="derive">

**Step 1: Derive the Work Context**

Ask the SPX CLI for the target's context:

```bash
spx spec context show $target --json
```

When its output gives the Work Context in the resolved mode, each member with its view, derive the member list from that output and enumerate no member by globbing.

Otherwise derive the same members, views, and order from the tree itself, and the manifest names the fallback. Walk each level from `spx/` to the target:

```bash
# At each directory on the path, and at the target
Glob: "{dir}/*-*.adr.md"
Glob: "{dir}/*-*.pdr.md"
Glob: "{dir}/ISSUES.md"
Glob: "{dir}/*-*.*/"          # child node directories, which give the next level's siblings
# At the target only
Glob: "$target/{slug}.outcome.md"
Glob: "$target/knowledge/index.md"
Glob: "$target/spx.status.json"
```

- At an ancestor level, keep each Decision Record whose Index is below the Index of the child the path continues through.
- At the target, keep every Decision Record.
- A sibling is a node directory with the same parent. Compare its Index with the Index of the node on the path at that level: a lower Index is a member at Declaration; a same or higher Index is a peer per `<modes>`.
- The pinned implementation files are the read paths outside `spx/` that the `test` and `eval` entries of the target's `spx.status.json`, and of each Variant's, name. A tree with no status claim pins none.

</step>

<step name="read">

**Step 2: Read the members in read order**

Read every member in the order `<read_order>` gives, at the view `<views>` gives it. Read every Decision Record a level keeps, without filtering by title.

ABORT when the spec of an ancestor or the target is missing.

Read `CLAUDE.md` at the root and on the path when present, and `spx/local/merging.md` when present, outside the read order. List the other `spx/local/*.md` overlays without reading them; the skills they configure read them.

</step>

<step name="cited_governance">

**Step 3: Read cited Decision Records**

Scan the member spec and Decision Record files for full-path decision citations:

```bash
Grep: "spx/[^[:space:])]+\\.(adr|pdr)\\.md" in the member spec and decision files
```

Each cited `spx/.../*.adr.md` or `spx/.../*.pdr.md` enters once, at Complete, with provenance that names the citing file. Scan each newly read cited record for further citations, repeating until no unread cited record remains. Read each contract file a member spec links. Never scan `ISSUES.md`, `PLAN.md`, or any other note for citations; a note adds no member.

If a member cites a missing Decision Record path, ABORT with the missing citation path, the citing file, and remediation guidance to fix the stale citation or restore the decision file.

</step>

<step name="summary">

**Step 4: Emit context marker and manifest**

Emit the `<PRODUCT_TREE_CONTEXT>` marker:

```text
<PRODUCT_TREE_CONTEXT target="{full-target-path}">

Product: {product-name}
Target: $target ({kind}|product root)
Mode: {Routine|Authoring}{ (no mode named)}
Bootstrap: {true|false}
Methodology: {methodology.source} {methodology.version}
Derivation: spx spec context show | fallback tree walk

Read order:
  1. {path} — {Opening|Declaration|Complete}
  2. {path} — {view}
  ...
Cited Decision Records: {path} cited by {citing path}, ... | none
Contract files: {list} | none
Pinned implementation files: {list} | none

Hierarchy (node target):
  {product-name}
  └── {ancestor-1} ({kind})
      └── {ancestor-2} ({kind})
          └── {target} ({kind}) ← TARGET

Hierarchy (product-root target):
  {product-name} ← TARGET

Same-Index and higher-Index siblings: {list} (listed, not read | at Opening | at Declaration)
Immediate children: {list} (not loaded | at Declaration)
Instruction files: {list} | none
Local skill overlays: {comma-separated list from spx/local/} | none
Lifecycle overlays read: spx/local/merging.md | none
Implementation: unknown unless already established by a prior workflow
Default-branch completion boundary: delivered value is value merged to the default branch on origin through /merge; local verification, review, audit, and commits are progress, not completion, while the branch carries changes ahead of its resolved base
Governed next workflow: /merge after local verification when the work changes files and is destined for the default branch, unless explicitly scoped to proposal, analysis, review, or local-only work, or stopped at an explicit lifecycle gate with no independent local action remaining
Progress verdict rule: status and progress answers must classify the lifecycle as complete, continuing, or blocked; a clean worktree, committed branch, or passing local gate cannot classify default-branch work as complete while changes remain ahead of the resolved base
Continuation action: if the lifecycle is continuing, proceed to the governed next workflow instead of ending the turn; if blocked, report the exact gate, evidence, and operator decision required

</PRODUCT_TREE_CONTEXT>
```

</step>

</workflow>

<pre_4_context>

Where the repository declares a methodology version before 4.0, load the 3.x walk in place of the Work Context, and the manifest names that version:

- the product document, every product-level ADR and PDR, and the product-level `ISSUES.md` and `PLAN.md`;
- for each directory from the root to the target: its spec, every ADR and PDR in it, its `ISSUES.md` and `PLAN.md`, and each lower-index sibling spec whole; same-index and higher-index siblings are listed, not read;
- the target spec, every target ADR and PDR, its notes, and its immediate children listed;
- every full-path ADR or PDR cited by a loaded spec or decision, once, with its citing file.

</pre_4_context>

<abort_protocol>

When a required document is missing, ABORT immediately with:

1. **What's missing** — exact file path expected
2. **Why it's needed** — what context it provides
3. **How to fix** — specific remediation action

| Missing       | Remediation                                                                                |
| ------------- | ------------------------------------------------------------------------------------------ |
| Product file  | "Create with `/bootstrap` — every tree needs a product document"                           |
| Ancestor spec | "Node directory exists but spec file is missing. Create `{slug}.spec.md`"                  |
| Target spec   | "Target directory exists but spec file is missing. Create `{slug}.spec.md` with `/author`" |

Do NOT proceed with partial context. The whole point of deterministic context is completeness.

</abort_protocol>

<failure_modes>

**Failure 1: Skipped Decision Records based on title relevance**

Claude globbed 12 decision records but only read 3 whose titles seemed relevant. The answer to the user's question was in one of the 9 skipped documents. Every Decision Record a level keeps enters at Complete, whatever its title.

**Failure 2: Loaded an ancestor record that does not govern the path**

Claude read every Decision Record at each ancestor level. A record indexed above the child the path continues through governs only the higher-Index siblings, so it filled the context with rules that do not reach the target. Keep only the ancestor records indexed below that child, plus records a member cites.

**Failure 3: Read lower-index sibling specs whole**

Claude read each lower-Index sibling spec verbatim. The target needs a sibling's declared contract, so the sibling enters at Declaration and a reader opens Complete on demand.

**Failure 4: Read peers in Routine mode**

Claude read the same-Index and higher-Index siblings while specifying a node. Routine mode lists them by directory entry and reads no file of theirs.

**Failure 5: Read test bodies during context loading**

Claude read test file imports during context loading and reported implementation state from those imports. Context loading reads no test, eval, or probe file; `/test`, `/audit-tests`, and `/apply` inspect them.

**Failure 6: Reported a bare node or decision name**

Claude wrote "see 15-build.adr.md" or "continue in 32-parser.capability" without the full path. Those references are ambiguous because numeric prefixes are sibling-local. Always report the complete path from `spx/`.

**Failure 7: Treated status reporting as permission to stop**

Claude answered a progress question by reporting the clean worktree and local verification, then ended the turn while the branch still carried changes destined for the default branch. The manifest carries the progress verdict and the continuation action: complete only after the change reaches the default branch on origin.

**Failure 8: Moved the checkout while loading context**

Claude ran a base sync before reading the tree, and the rebase replaced the head under inspection with a different commit. Context loading reads the checkout as it stands.

**Failure 9: Missed a cited Decision Record**

Claude saw full-path citations to Decision Records under an independent sibling subtree and did not read them because they were outside the structural path. Scan member specs and Decision Records for full-path citations, including citations from newly read cited records, before emitting the marker.

**Failure 10: Took the methodology version from prose**

Claude read the methodology version from a changelog line. The manifest states the version from the `methodology` block of `spx config show --json` alone.

</failure_modes>

<success_criteria>

The emitted `<PRODUCT_TREE_CONTEXT target="...">` marker is sound when:

- [ ] A live `<PRODUCT_TREE_FOUNDATION>` marker precedes it in the conversation
- [ ] Its target is exact `spx/` or a canonical full `spx/...` node path, accepted before any filesystem lookup
- [ ] It names the mode taken, and Authoring when the caller named none
- [ ] It names the methodology source and version from the SPX CLI's structured output, and the derivation it used
- [ ] Its read order lists every member of that mode with its view, in the order `<read_order>` gives, and no member the mode leaves out
- [ ] Every cited Decision Record appears once with its citing file, and no member comes from a note
- [ ] Instruction files and local overlays are listed apart from the read order
- [ ] No test, eval, or probe file was read, and implementation state reads `unknown` unless a prior workflow established it
- [ ] Every node, Decision Record, and note reference is a full path from `spx/`
- [ ] Bootstrap is `true` only for exact `spx/` with a product document and no nodes, and `false` for every node target
- [ ] The checkout's head is the same before and after context loading
- [ ] An ABORT emits no marker and names the missing path with its remediation

</success_criteria>
