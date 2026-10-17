# Issues: Test Skill

## DEBT: the controlled-implementation exception depends on caller-loaded workflow authority

`src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` line 42 permits a controlled implementation only through the generic test workflow's exception cases, while this independently loadable reference does not identify that authority. A consumer loading the reference without its authoring or auditing caller cannot determine the permitted exception set, so controlled-implementation judgments can vary by invocation context.

The configured `skill-auditor` produced inconsistent verdicts on byte-identical skill bundles: it approved heads `86d778748a302217ef03e5e08e7f816bc30970fb` and `086db895f4204d393799b649d5e5e7d640e28f39`, then produced two rejecting verdicts at head `7ca59434d5f62a142fe690e2c00b97bc1f47d6d0`. Both rejections reported `f-002`, rule `caller_independence`, against line 42. The approval on the identical subject remains the Change #94 gate result; the finding is retained here as debt for independent settlement.

Run `2026-10-17_19-43-16-101-974a660b94a1` raised the same finding, rule `caller-independence` against assertion ordinal 3, at severity debt. The finding sits at line 44 of the shared standard, which names the controlled-implementation exception set only by pointing to the generic test workflow, so a consumer that loads the standard alone cannot see the set. Base-ref evidence: `git diff --unified=0 262c63fbf4a417463fd537fda8453fc6c902eb75 -- src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` shows line 44 untouched in the audited tree.

**Settlement condition**: a separate Change makes the controlled-implementation exception authority independently available from the shared reference, or amends the governing decision to establish why every valid consumer necessarily loads the named workflow authority, then obtains a consistent configured `skill-auditor` verdict on the committed subject.

## DEBT: the TypeScript test specialist repeats the generic dependency-to-level table and miscounts the exception cases

Finding from run `2026-10-17_19-43-16-101-974a660b94a1`, rule `language-specialist-repeats-generic-decision`, assertion ordinal 5, severity debt. `src/plugins/typescript/skills/author-typescript-test/SKILL.md` restates the generic Stage 2 dependency-to-level table (Step 2, lines 76-83) and says "6 exception cases" (line 279), while the generic test skill declares seven. The two copies can drift, and the count already disagrees.

Base-ref evidence: `git diff --unified=0 262c63fbf4a417463fd537fda8453fc6c902eb75 -- src/plugins/typescript/skills/author-typescript-test/SKILL.md` is empty; both locations are untouched in the audited tree.

**Settlement condition**: the TypeScript specialist cites the generic test skill for the dependency-to-level table and the exception-case set, and carries only the TypeScript-specific expression of each level, then obtains a consistent configured `skill-auditor` verdict on the committed subject.

## The canonical filename patterns are stated twice in the test skill

Finding `f-008`, rule `duplicated_canonical_content`, raised by the configured `skill-auditor` against `src/plugins/spec-tree/skills/test/SKILL.md`. The four per-language filename patterns appear as the model in `<naming_and_co_location>` and again as the canonical-pattern column of the legacy-filename table in the scaffolding step. A language addition or token change can leave the two copies disagreeing inside one file.

**Settlement condition**: one section owns the canonical patterns and the other cites it, leaving the legacy table to carry only the patterns that fail the check.

**Why separate from Change #33**: both copies predate this changeset, which changes neither section's patterns.

## A property-selection rule in the test skill states neither a requirement nor an option

Finding `f-010`, rule `constraint_language`, raised by the configured `skill-auditor` against `src/plugins/spec-tree/skills/test/SKILL.md`. The phrase "mandatory candidates" in the property-selection guidance gives no decidable instruction: a candidate that is mandatory is neither required nor optional, so the reader cannot tell what the rule obliges.

**Settlement condition**: the guidance states the selection rule decidably and ties it to the Stage 1 quantifier test that already owns the classification.

**Why separate from Change #33**: the wording predates this changeset, whose property-boundary rules leave it untouched.

## The test skill body sits ten lines under the progressive-disclosure ceiling

`src/plugins/spec-tree/skills/test/SKILL.md` measures 490 lines against the 500-line budget that `/skill-standards` `<progressive_disclosure>` sets. The two Stage 2 lookup tables live in `src/plugins/spec-tree/skills/test/references/execution-level-lookup.md`, which Stage 2 loads when it runs. No eager-foundation exception is declared: the Stage 2 tables are read only outside decision-rule mode, so they are conditional detail. An inline rule addition of ten or more lines leaves the body at 500 lines or more, which breaches the ceiling.

**Settlement condition**: the body gains headroom beyond the next foreseeable rule addition, by moving a section that not every invocation needs behind a conditional reference, then obtains a consistent configured `skill-auditor` verdict on the committed subject.
