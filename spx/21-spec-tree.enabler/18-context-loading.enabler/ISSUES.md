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

`context-loading.md` declares that the `/contextualize` manifest states the methodology source and version the repository follows, taken from the `methodology` block of the SPX CLI's context bundle. The bundle exists: `spx spec context show --json` on the installed `@outcomeeng/spx` 0.6.26 emits `methodology.source` `outcomeeng/methodology` and `methodology.version` `4.0.0` for this repository. The skill does not consume it. Consumption of the bundle is blocked on the published contract and the floor, recorded in this node's `PLAN.md`: `REQUIRED_SPX_VERSION` and the CI pin sit at 0.6.15, below the 0.6.16 release that introduced the subcommand. The `<SPEC_TREE_CONTEXT>` marker therefore names no methodology version, and a session learns it only by reading the spx configuration file by hand.

Two further readings show the same gap from the CLI side. `spx diagnose` reports `methodology-context` as `unavailable` with `observedSource` and `observedVersion` absent, because no installed methodology package is configured. `spx spec context show --understand`, which serves the foundation payload from that package, fails for the same reason: `methodology.packageDir` is unset. Whether the `/understand` foundation is delivered through that payload is a separate decision the context-enumeration ADR does not yet make.

**Interim**: the managed instruction block instructs Claude to read the methodology source and version from `spx.config.yaml` at the repository root, to read it again whenever `/understand` runs, and to treat an absent file or one without a `methodology` block as no declared methodology version, never inferring one from a plugin's distribution version, a changelog, or prose. The instruction reads the same declaration the SPX CLI resolves, so it is consistent with the `NEVER` assertion above; the value spx's `version: installed` default would resolve to stays undeclared until the spec-tree plugin declares the methodology it provides, the gap `spx/15-validation.enabler/32-plugin-manifest.enabler/ISSUES.md` records; it stands in for the manifest until the consumption slice lands and is removed in that change.

**Resolution shape**: land the consumption slice in `PLAN.md` (floor and pin advanced to a release whose bundle satisfies the contract, `/contextualize` reading the bundle), emit the `methodology` block in the manifest, retag the assertion's evidence against the CLI output, and delete the interim instruction-block line in the same change.

**Evidence**: `spx spec context show --json spx/21-spec-tree.enabler/18-context-loading.enabler` on 0.6.26; `spx diagnose --format json` `methodology-context` record; `outcomeeng/validation/spx_version.py` line 87 and `.github/workflows/check.yml` line 31.
