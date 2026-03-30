# Deficiencies: auditing-python-architecture

Insights from the `auditing-python-tests` rewrite applied to this skill. This is the strongest of the 4 renamed skills — it has context loading, proper `/testing` section references, and clean guidelines. Deficiencies are minor.

## D1: No failure modes section

The test audit skills include concrete stories of auditor failures. This skill has none.

**Candidates for failure modes:**

- **Accepted temporal language because it was in the Rationale section** — reviewer thought Rationale was exempt from atemporal voice. It isn't — the rule applies to ALL sections.
- **Approved ADR with "DI Protocol" but no testing strategy** — reviewer saw the Protocol definition and assumed testing was covered. The ADR had no level assignments.
- **Missed "respx.mock" in a code example** — the ADR's Correct Approach section showed mocking in a code block, but the reviewer only checked prose for mocking language.
- **Accepted Level 2 for a SaaS service** — reviewer didn't verify the "SaaS services jump L1→L3" rule and accepted L2 for Trakt.tv API testing.

## D2: Example uses line numbers despite guidelines saying not to

The `<review_guidelines>` section correctly says "Don't reference specific line numbers (they change)." But the `<example_review>` section references "Lines 132-133", "Lines 132, 133, 145" throughout.

**Action:** Remove line number references from the example. Use section names or quoted text instead.

## D3: No structured verdict per principle checked

The verdict is flat (APPROVED/REJECTED with a violations list). A structured per-principle table would make the output more consistent with the test audit format and easier for an agent to parse:

```text
| # | Principle            | Status | Detail                           |
|---|----------------------|--------|----------------------------------|
| 1 | Testing strategy     | PASS   | Levels assigned for all components |
| 2 | Mocking prohibition  | REJECT | "mock at boundary" in testing strategy |
| 3 | Atemporal voice      | REJECT | Context narrates code state      |
| 4 | Exception docs       | PASS   | All doubles have exception case  |
```

## D4: Output format has unclosed code fence

The `<output_format>` section uses mixed ```` and ``` fencing that doesn't render correctly, same issue as the TypeScript architecture skill.

**Action:** Fix code fence nesting.

## D5: SaaS "jump L1→L3" rule is buried

The critical rule "SaaS services have no Level 2 — jump from Level 1 to Level 3" is in the middle of a bullet list. This is one of the most commonly violated principles (see D1 failure mode 4) and deserves more prominent treatment.

**Action:** Elevate to a callout or separate subsection, or add to the example as a correct/incorrect pattern pair.

## Priority order

1. **D1** (add failure modes) — highest impact on audit quality
2. **D2** (fix example line numbers) — consistency with own guidelines
3. **D3** (structured verdict) — machine-readable output
4. **D4** (fix code fences) — rendering bug
5. **D5** (elevate SaaS rule) — prevents most common violation
