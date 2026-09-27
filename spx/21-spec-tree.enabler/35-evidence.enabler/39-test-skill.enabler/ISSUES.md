# Issues: Test Skill

## DEBT: the controlled-implementation exception depends on caller-loaded workflow authority

`src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` line 42 permits a controlled implementation only through the generic test workflow's exception cases, while this independently loadable reference does not identify that authority. A consumer loading the reference without its authoring or auditing caller cannot determine the permitted exception set, so controlled-implementation judgments can vary by invocation context.

The configured `skill-auditor` produced inconsistent verdicts on byte-identical skill bundles: it approved heads `86d778748a302217ef03e5e08e7f816bc30970fb` and `086db895f4204d393799b649d5e5e7d640e28f39`, then produced two rejecting verdicts at head `7ca59434d5f62a142fe690e2c00b97bc1f47d6d0`. Both rejections reported `f-002`, rule `caller_independence`, against line 42. The approval on the identical subject remains the Change #94 gate result; the finding is retained here as debt for independent settlement.

**Settlement condition**: a separate Change makes the controlled-implementation exception authority independently available from the shared reference, or amends the governing decision to establish why every valid consumer necessarily loads the named workflow authority, then obtains a consistent configured `skill-auditor` verdict on the committed subject.

## The test skill body sits within five lines of the progressive-disclosure ceiling

Finding `f-007`, rule `progressive_disclosure_headroom`, raised by the configured `skill-auditor` against `src/plugins/spec-tree/skills/test/SKILL.md`. The body measures 495 lines against the 500-line budget `/skill-standards` `<progressive_disclosure>` sets, with the whole `<testing_methodology>` inline and two small conditional references beside it. The next inline rule addition breaches the budget or forces an unplanned eager-foundation exception claim. The auditor names `<four_part_progression>` and the two Stage 2 lookup tables as the detail a reader does not need on every invocation.

**Settlement condition**: the body measures at or below the ceiling with editing headroom restored, by moving that conditional detail into a cited reference or by declaring the eager-foundation exception with its justification. The ceiling itself is the trigger — the entry closes when a later change reaches it.

**Why separate from Change #33**: the crowding predates this changeset. The move relocates content Change #33 neither adds nor governs, and it carries its own skill-audit gate.

## The canonical filename patterns are stated twice in the test skill

Finding `f-008`, rule `duplicated_canonical_content`, raised by the configured `skill-auditor` against `src/plugins/spec-tree/skills/test/SKILL.md`. The four per-language filename patterns appear as the model in `<naming_and_co_location>` and again as the canonical-pattern column of the legacy-filename table in the scaffolding step. A language addition or token change can leave the two copies disagreeing inside one file.

**Settlement condition**: one section owns the canonical patterns and the other cites it, leaving the legacy table to carry only the patterns that fail the check.

**Why separate from Change #33**: both copies predate this changeset, which changes neither section's patterns.

## A property-selection rule in the test skill states neither a requirement nor an option

Finding `f-010`, rule `constraint_language`, raised by the configured `skill-auditor` against `src/plugins/spec-tree/skills/test/SKILL.md`. The phrase "mandatory candidates" in the property-selection guidance gives no decidable instruction: a candidate that is mandatory is neither required nor optional, so the reader cannot tell what the rule obliges.

**Settlement condition**: the guidance states the selection rule decidably and ties it to the Stage 1 quantifier test that already owns the classification.

**Why separate from Change #33**: the wording predates this changeset, whose property-boundary rules leave it untouched.
