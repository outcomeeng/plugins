# ISSUES — context loading

## Notes load with no age, so a stale note reads as current truth

`/contextualize` loads every `ISSUES.md` of the Product, the target, and its ancestors at Complete, and lists each in the read order of `<PRODUCT_TREE_CONTEXT>` with its view and no other field. A note committed days before the branch arrives in the same shape as one committed at `HEAD`. The manifest carries no last-commit date, no age, and no discard threshold, so a reader has no input for judging whether an entry still holds.

**Resolution shape**: emit each note's last-commit time beside its read-order entry and apply a discard threshold, reporting a note past it as discarded rather than loading it. This is one `git log -1 --format=%cI` per note. Fix the threshold in the skill rather than leaving it to per-session judgment.

## The manifest proves files were read, never that their rules were applied

The `<PRODUCT_TREE_CONTEXT>` manifest lists each member path with its view: Opening, Declaration, or Complete. A Decision Record can therefore be loaded at Complete and listed by path while the rule it carries goes unapplied to the surface under work, and the manifest reports that outcome as complete context.

The path list is the wrong unit. What binds is each decision's rules, which are already one-line rows under typed group headings and can be extracted without judgment.

**Resolution shape**: emit the rules themselves, grouped under their decision path, beside the read order. Extraction stays mechanical, so selection remains a pure function of the tree and nothing is summarized. The rules are the shortest part of a decision and the only part that binds, while the rationale is what a reader opens on demand when a rule's application is contested.

## The unread implementation surface is formatted as a manifest field, not a gap

`<PRODUCT_TREE_CONTEXT>` prints `Implementation: unknown unless already established by a prior workflow` in the same list as `Read order:`, `Cited Decision Records:`, and `Pinned implementation files:`, fields that report what was read. It is the only entry that reports an absence, and it is typeset as a value. In a tree whose Nodes carry no status claim, `Pinned implementation files:` reads `none`, so a packet that read no implementation still reads as complete.

**Resolution shape**: report the unread implementation surface as a named gap distinct from the read order: what the target's specs point at, what context loading did not read, and which workflow reads it. Consider whether the marker should state that a claim about implementation is unbacked until that surface is read.

## DEBT [conciseness]: the context loader restates lifecycle policy and its own steps

Defect class: `conciseness`.

Finding: the typed skill audit of `contextualize` on the Change Lifecycle changeset (head `a28a5be91fc2ea04151c283059caa9cb9a11fd12`) found the marker template hardcoding lifecycle-policy sentences that `/merging-standards` owns, success-criteria items that echo workflow steps, and `bash` fences holding tool pseudo-syntax. At the Work Context rewrite of outcomeeng/changes#435, the marker still carries four lifecycle lines (`Default-branch completion boundary`, `Governed next workflow`, `Progress verdict rule`, `Continuation action`), and three `bash` fences still hold `Glob:` and `Grep:` pseudo-syntax beside two that hold real `spx` commands.

Evidence: `instructions:skill-auditor` findings f-009 to f-012 on `src/plugins/product-tree/skills/contextualize/SKILL.md`.

Impact: the manifest's lifecycle lines drift from the merge policy they copy, and the criteria block duplicates the workflow on every load.

Successor: a Proposed Change filed after outcomeeng/changes#91 merges.

Revisit and settlement condition: the four lifecycle fields derived from the read overlay or the merge policy, criteria reduced to falsifiable marker properties, fences labelled `text` where they hold no shell command, and one typed skill audit approving with no `conciseness` finding.

## The skill derives the Work Context by a local tree walk

[`spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md) has `/contextualize` derive the Work Context from `spx spec context show --json` where the consuming floor's output gives it, and derive the same members, views, and order from the tree itself otherwise. On spx 0.11.0, `spx spec context show <target> --json` emits only `entries`, each with `type`, `path`, `metadata`, and `content`. It names no mode, no view, and no `methodology` block. For spx/21-product-tree.enabler/18-context-loading.enabler it returns 75 `document` entries, higher-Index top-level siblings among them read whole, and 3 `reference` entries. So `/contextualize` takes the fallback: it globs each level's Decision Records, siblings, and notes, and selects members and views itself.

**Impact.** The agent selects members and derives views itself, so a skipped Decision Record or a peer read at the wrong view is possible, and the Work Context is judged by Audit where a deterministic grader could judge CLI output.

**Settlement condition.** A published SPX release's `spx spec context show --json` gives a target's Work Context in Routine and Authoring mode, each member with its view, and the repository's floor and pin sit at that release. `/contextualize` derives the Work Context from that output, and the read-order, member, and determinism assertions in `context-loading.md` carry Test evidence against the CLI output.

**Related.** `outcomeeng/changes#346` makes the decision name the capability by the command the CLI ships, and `outcomeeng/changes#320` carries complete Product Tree context through `list` and `show`.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_foundation_manifest.compliance.l1.py`: write a file

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
