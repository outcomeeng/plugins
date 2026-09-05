# Issues: Test Skill

## The test skill exceeds the progressive-disclosure ceiling with no declared exception

`src/plugins/spec-tree/skills/test/SKILL.md` runs past the 500-line ceiling `/skill-standards` `<progressive_disclosure>` sets, with no `references/` directory and no inline statement invoking the `<eager_foundation_exception>`. Its rendered payload measures under the exception's 40,000-code-point bound, so the gap is a missing declaration rather than a size defect: a future editor cannot tell whether every language's `/test-{lang}` specialist needs this routing and naming material on every invocation, which is what the exception requires, or whether the body grew past the ceiling incidentally.

**Resolution shape**: either add a short block declaring the exception and why each part of the body is needed on every invocation, or move the per-language filename tables and the legacy-pattern table into a cited reference. Gate the change with the configured `skill-auditor`.

**Evidence**: raised as a `worth-improving` finding by `instructions:skill-auditor` on the Go delegation change to this skill, which measured the payload at 33,217 code points.
