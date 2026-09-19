# Issues: Test Skill

## The test skill exceeds the progressive-disclosure ceiling with no declared exception

`src/plugins/spec-tree/skills/test/SKILL.md` runs past the 500-line ceiling `/skill-standards` `<progressive_disclosure>` sets, with no `references/` directory and no inline statement invoking the `<eager_foundation_exception>`. Its rendered payload measures under the exception's 40,000-code-point bound, so the gap is a missing declaration rather than a size defect: a future editor cannot tell whether every language's `/test-{lang}` specialist needs this routing and naming material on every invocation, which is what the exception requires, or whether the body grew past the ceiling incidentally.

**Resolution shape**: either add a short block declaring the exception and why each part of the body is needed on every invocation, or move the per-language filename tables and the legacy-pattern table into a cited reference. Gate the change with the configured `skill-auditor`.

**Evidence**: raised as a `worth-improving` finding by `instructions:skill-auditor` on the Go delegation change to this skill, which measured the payload at 33,217 code points.

## DEBT: the controlled-implementation exception depends on caller-loaded workflow authority

`src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` line 42 permits a controlled implementation only through the generic test workflow's exception cases, while this independently loadable reference does not identify that authority. A consumer loading the reference without its authoring or auditing caller cannot determine the permitted exception set, so controlled-implementation judgments can vary by invocation context.

The configured `skill-auditor` produced inconsistent verdicts on byte-identical skill bundles: it approved heads `86d778748a302217ef03e5e08e7f816bc30970fb` and `086db895f4204d393799b649d5e5e7d640e28f39`, then produced two rejecting verdicts at head `7ca59434d5f62a142fe690e2c00b97bc1f47d6d0`. Both rejections reported `f-002`, rule `caller_independence`, against line 42. The approval on the identical subject remains the Change #94 gate result; the finding is retained here as debt for independent settlement.

**Settlement condition**: a separate Change makes the controlled-implementation exception authority independently available from the shared reference, or amends the governing decision to establish why every valid consumer necessarily loads the named workflow authority, then obtains a consistent configured `skill-auditor` verdict on the committed subject.
