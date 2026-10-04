# ISSUES — context loading

## Coordination notes load with no age, so a stale note reads as current truth

`/contextualize` reads every `PLAN.md` and `ISSUES.md` at the product root, each ancestor, and the target, then lists them in `<SPEC_TREE_CONTEXT>` under one undifferentiated `Coordination notes:` line. A note committed days before the branch arrives in the same shape as one committed at `HEAD`. The skill's only staleness handling is an instruction to reconcile each note against current truth — a judgment with no input, since the manifest carries no last-commit date, no age, and no discard threshold.

**Resolution shape**: emit each note's last-commit time in the manifest and apply a discard threshold, reporting a note past it as discarded rather than loading it. The skill already runs git and already reads the notes, so this is one `git log -1 --format=%cI` per note. Fix the threshold in the skill rather than leaving it to per-session judgment.

## The manifest proves files were read, never that their rules were applied

Context loading verifies itself by counting: glob count must equal read count, and the `<SPEC_TREE_CONTEXT>` marker reports `ADRs: N found, N read`. A decision can therefore be loaded, counted, and listed by name in the marker while the rule it carries goes unapplied to the surface under work — and the manifest reports that outcome as complete context.

The count is the wrong unit. What binds is each decision's `### Audit` and `### Testing` rules, which are already one-line imperatives and extractable without judgment.

**Resolution shape**: emit the rules themselves, grouped under their decision path, in place of the found-and-read counts. Extraction stays mechanical, so selection remains a pure function of the tree and nothing is summarized. It also inverts the eager and conditional split correctly: the rules are the shortest part of a decision and the only part that binds, while the rationale is what should be read on demand when a rule's application is contested.

## The unread implementation surface is formatted as a manifest field, not a gap

`<SPEC_TREE_CONTEXT>` prints `Implementation: unknown unless already established by a prior workflow` in the same list as `Product spec:`, `ADRs:`, and `Test links:` — fields that report what was read. It is the only entry that reports an absence, and it is typeset as a value, so a packet carrying no implementation reads as complete. The surrounding design reinforces that: glob-count-equals-read-count verification for decisions, and a marker whose presence is the gate other skills check.

**Resolution shape**: report the unread implementation surface as a named gap distinct from the read-set — what the target's specs point at, what context loading did not read, and which workflow reads it. Consider whether the marker should state that a claim about implementation is unbacked until that surface is read.

## The context manifest carries no methodology declaration

`context-loading.md` declares that the `/contextualize` manifest states the methodology source and version the repository follows, taken from the `methodology` block of the SPX CLI's context bundle. The bundle exists: `spx spec context show --json` on the installed `@outcomeeng/spx` 0.6.26 emits `methodology.source` `outcomeeng/methodology` and `methodology.version` `4.0` for this repository. The skill does not consume it. The floor and the CI pin sit at 0.7.2, above the 0.6.16 release that introduced the subcommand, so consumption of the bundle waits only on the published contract. The `<SPEC_TREE_CONTEXT>` marker therefore names no methodology version, and a session learns it only by reading the spx configuration file by hand.

Two further readings show the same gap from the CLI side. `spx diagnose` reports `methodology-context` as `unavailable` with `observedSource` and `observedVersion` absent, because no installed methodology package is configured. `spx spec context show --understand`, which serves the foundation payload from that package, fails for the same reason: `methodology.packageDir` is unset. Whether the `/understand` foundation is delivered through that payload is a separate decision the context-enumeration ADR does not yet make.

**Interim**: the managed instruction block instructs Claude to read the methodology source and version from `spx.config.yaml` at the repository root, to read it again whenever `/understand` runs, and to treat an absent file, a missing `methodology` block, or a `methodology.version` of the sentinel `installed` as no declared methodology version, never inferring one from a plugin's distribution version, a changelog, or prose. The instruction reads the same declaration the SPX CLI resolves, so it is consistent with the `NEVER` assertion above; the `installed` sentinel is spx's default and resolves to the methodology the installed spec-tree plugin declares, which stays undeclared until the plugin declares what it provides, the gap `spx/15-validation.enabler/32-plugin-manifest.enabler/ISSUES.md` records; it stands in for the manifest until the consumption slice lands and is removed in that change.

**Resolution shape**: land the consumption slice described in "The skill enumerates the read-set locally" below (floor and pin advanced to a release whose bundle satisfies the contract, `/contextualize` reading the bundle), emit the `methodology` block in the manifest, retag the assertion's evidence against the CLI output, and delete the interim instruction-block line in the same change.

**Evidence**: `spx spec context show --json spx/21-spec-tree.enabler/18-context-loading.enabler` on 0.6.26; `spx diagnose --format json` `methodology-context` record; `outcomeeng/validation/spx_version.py` and `.github/workflows/check.yml`, which both place the floor and the pin at 0.7.2.

## The context walk reads fewer sibling contracts than the foundation declares

**Evidence:** The `/understand` foundation declares the methodology 4.0 walk, which reads every sibling's published contract at each level and treats only a named lower-index provider as a constraint. `/contextualize` reads lower-index sibling specs only and lists same-index and higher-index siblings without reading them; `context-loading.md` asserts that behavior, and `13-context-enumeration.adr.md` fixes it as an invariant of the read order.

**Impact:** A consumer's awareness of its peers and consumers is missing from the loaded context, and a provider scopes its mandate without the consumer contracts the walk is meant to supply.

**Settlement condition:** `13-context-enumeration.adr.md` states the 4.0 read order, `context-loading.md` asserts it, and `/contextualize` reads every sibling contract at each level with prerequisite and awareness distinguished in the manifest.

## DEBT [conciseness]: the context loader restates lifecycle policy and its own steps

Defect class: `conciseness`.

Finding: the typed skill audit of `contextualize` on the Change Lifecycle changeset (head `a28a5be91fc2ea04151c283059caa9cb9a11fd12`) found the marker template hardcoding four lifecycle-policy sentences that `/merging-standards` owns, 23 success-criteria items several of which echo workflow steps, seven `bash` fences holding tool pseudo-syntax, and a sentence fragment opening Step 2.

Evidence: `instructions:skill-auditor` findings f-009 to f-012 on `src/plugins/spec-tree/skills/contextualize/SKILL.md`.

Impact: the manifest's lifecycle lines drift from the merge policy they copy, and the criteria block duplicates the workflow on every load.

Successor: a Proposed Change filed after outcomeeng/changes#91 merges.

Revisit and settlement condition: the four lifecycle fields derived from the read overlay or the merge policy, criteria reduced to falsifiable marker properties, fences labelled `text`, and one typed skill audit approving with no `conciseness` finding.

## The skill enumerates the read-set locally

`13-context-enumeration.adr.md` decides that a target's complete read-set derives from the SPX CLI's context bundle, with the deterministic tree walk and the cited-governance resolver living in the CLI as a trusted third party per `spx/12-shipped-scripting.adr.md`. The shipped `/contextualize` skill keeps structural enumeration local: per level it globs the ADRs and PDRs, reads every one, and requires the glob count to equal the read count. It already reads explicit full-path ADR and PDR citations from the loaded specs and decisions.

The published CLI supplies the bundle as `spx spec context show --json`, whose schema-2 output carries `schemaVersion`, `methodology`, `productDir`, `targets`, `bootstrap`, `read`, `listed` and `coverage`. The earlier contract it replaced emitted `documents`, `methodology`, `productDir`, `siblings` and `target`, omitted a cited governance decision observed for this node, and exposed no citation provenance, guides, local overlays, bootstrap flag or schema version. Whether the schema-2 bundle satisfies the decision's contract (ordered and byte-identical for one tree and target, every decision at a level emitted, only lower-index siblings read, cited governance decisions with their citing file, coordination notes never adding citations, guides and the lifecycle overlay outside the read loop, bootstrap, and a non-zero exit naming a missing required spec) is established against the decision when the slice starts.

**Impact.** The agent counts files itself, so a skipped decision or a read higher-index sibling is possible; the structural enumeration is judged by `[audit]` where a deterministic grader could judge CLI output.

**Settlement condition.** The published bundle satisfies the decision's contract and the repository's floor and pin sit at a release carrying it. `/contextualize` enumerates exactly the paths in the bundle's `read` and reports the cited-governance provenance in the `<SPEC_TREE_CONTEXT>` manifest, reads the guides and the lifecycle overlay `spx/local/merging.md` outside that loop, and lists the remaining local overlays without reading them. The read-completeness, lower-index-sibling and determinism assertions in `context-loading.md` carry `[test]` evidence against the CLI output, and the foundation-manifest assertions keep their own `[test]` evidence.

**Related.** `outcomeeng/changes#346` makes the decision name the capability by the command the CLI ships, and `outcomeeng/changes#320` carries complete Product Tree context through `list` and `show`.

## A Verifier's context load rebases the branch it audits

`/contextualize` requires `/sync-base` before it reads product truth, and the test-evidence audit skill loads `/contextualize` for its target node. A Verifier's agent session therefore fetches, rebases the Author's branch onto its base and resolves conflicts on its own, while other Verifiers dispatched against the same committed head are still running. `spec-tree:audit-implementation` states that an audit never synchronizes, rebases or otherwise mutates the audited subject; the test-evidence path carries no such guard.

**Evidence.** Rollout `agent-a4cedd803fc1a5758.jsonl` of the test-evidence audit dispatched against head `f07db1bbaf225ec031d7a777f02c166daa588871` on 2026-09-16 invoked `spec-tree:sync-base`, ran `sync_base.py`, resolved two version and changelog conflicts with `git add` and `git rebase --continue`, and finished at `15d4309e69c26804cd1b04676248a529fd0235b9`. The concurrent implementation audit, run `2026-09-16_12-40-04-694-a2e206a2d753`, then found its sealed head superseded, and the Author's deterministic gate had run on the pre-rebase head only.

**Settlement condition.** A Verifier-mode context load reads the committed subject without `/sync-base`, or `/sync-base` reports behind-base without moving the checkout when its caller is a Verifier, and the audit skills that load context select it, so the clean committed head the dispatch-readiness record names stays the audited head.
