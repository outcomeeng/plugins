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
